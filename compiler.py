from Object import *

'''
考虑到设计难度，尝试对栈式虚拟机进行开发
简单初版
先压入左操作数，再压入右操作数
读取时先获得右操作数，再获得左操作数
压入：push
弹出：pop
赋值变量：write
读取变量：read
双操作数算数操作： add sub mul div mod power lt gt le ge eq ne and or xor bitwise_and bitwise_or
'''
from enum import IntEnum, auto


class code(IntEnum):
    push = auto()
    pop = auto()
    write = auto()
    read = auto()
    jump_if_false = auto()
    jump_if_true = auto()
    be_not = auto()
    jump = auto()

    def __repr__(self):
        return f'{self.name.upper()}'


class calc(IntEnum):
    add = auto()
    sub = auto()
    mul = auto()
    div_int = auto()
    div_float = auto()
    mod = auto()
    power = auto()
    lt = auto()
    gt = auto()
    le = auto()
    ge = auto()
    eq = auto()
    ne = auto()
    xor = auto()
    bitwise_and = auto()
    bitwise_or = auto()

    def __repr__(self):
        return f'{self.name.upper()}'


class Compiler:

    def __init__(self, ast):
        self.node_level = 0
        self.ast = ast
        self.bytecodes = []
        self.direct_add = {int, float, bool, str, type(None)}
        self.direct_ret_type = {Break_stmt, Continue_stmt}
        self.need_compile = {Binary_expr: self.binary_node, Id: self.read, If_stmt: self.if_node,
                             While_stmt: self.while_node}
        self.back_label = []
        self.back_map = {}
        self.loop_bounds = None

    def do(self):
        for i in self.ast:
            self.compile(i)
        # 标记回填具体数值
        for index, label in self.back_label:
            self.bytecodes[index] = (self.bytecodes[index][0], self.back_map[label])
        return self.bytecodes

    def compile(self, node):
        self.node_level += 1
        res = None
        t = type(node)
        if t in self.direct_add:
            self.bytecodes.append((code.push, node))
        elif t in self.direct_ret_type:
            res = t
            if t is Break_stmt:
                if self.loop_bounds is None:
                    raise Lang_Err('SyntaxError', 'break out of loop')
                else:
                    self.add_code_label(code.jump, self.loop_bounds[1])
            if t is Continue_stmt:
                if self.loop_bounds is None:
                    raise Lang_Err('SyntaxError', 'continue out of loop')
                else:
                    self.add_code_label(code.jump, self.loop_bounds[0])
        else:
            self.need_compile[t](node)
        self.node_level -= 1
        return res

    def read(self, node):
        self.bytecodes.append((code.read, node.id))
        if self.node_level == 1:
            self.bytecodes.append((code.pop,))

    def binary_node(self, node):
        op, left, right = node.op, node.left, node.right
        if op == '=':
            self.compile(right)
            self.bytecodes.append((code.write, left.id))
        elif op == '+':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.add,))
        elif op == '-':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.sub,))
        elif op == '*':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.mul,))
        elif op == '/':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.div_float,))
        elif op == '//':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.div_int,))
        elif op == '<':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.lt,))
        elif op == '>':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.gt,))
        elif op == '<=':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.le,))
        elif op == '>=':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.ge,))
        elif op == '==':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.eq,))
        elif op == '!=':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.ne,))
        elif op == '%':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.mod,))
        elif op == '**':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.power,))
        elif op == '&&':
            false_label = object()
            end = object()
            self.compile(left)
            self.add_code_label(code.jump_if_false, false_label)
            self.compile(right)
            self.add_code_label(code.jump_if_false, false_label)
            self.bytecodes.append((code.push, True))
            self.add_code_label(code.jump, end)
            self.record_label_location(false_label)
            self.bytecodes.append((code.push, False))
            self.record_label_location(end)
        elif op == '||':
            true_label = object()
            end = object()
            self.compile(left)
            self.add_code_label(code.jump_if_true, true_label)
            self.compile(right)
            self.add_code_label(code.jump_if_true, true_label)
            self.bytecodes.append((code.push, False))
            self.add_code_label(code.jump, end)
            self.record_label_location(true_label)
            self.bytecodes.append((code.push, True))
            self.record_label_location(end)
        elif op == '^':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.xor,))
        elif op == '&':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.bitwise_and,))
        elif op == '|':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((calc.bitwise_or,))

        if self.node_level == 1:
            self.bytecodes.append((code.pop,))

    def compile_block(self, body):
        # 重置节点层级，保证pop指令的添加无误
        old = self.node_level
        self.node_level = 0
        for i in body:
            t = self.compile(i)
            if t is Break_stmt or t is Continue_stmt:
                break

        # 恢复节点层级
        self.node_level = old

    def add_code_label(self, code_op, label):
        self.back_label.append((len(self.bytecodes), label))
        self.bytecodes.append((code_op, label))

    def record_label_location(self, label):
        self.back_map[label] = len(self.bytecodes)

    def if_node(self, node):
        condition, then, if_list, otherwise = node.condition, node.then, node.if_list, node.otherwise
        self.compile(condition)
        next_label = object()
        self.add_code_label(code.jump_if_false, next_label)
        self.compile_block(then)
        end = None
        if if_list or otherwise:
            end = object()
            self.add_code_label(code.jump, end)
        self.record_label_location(next_label)
        if if_list:
            for i in if_list:
                next_label = object()
                condition = i.condition
                then = i.then
                self.compile(condition)
                self.add_code_label(code.jump_if_false, next_label)
                self.compile_block(then)
                self.add_code_label(code.jump, end)
                self.record_label_location(next_label)
        if otherwise:
            self.compile_block(otherwise)
        if end:
            self.record_label_location(end)

    def while_node(self, node):
        old = self.loop_bounds
        condition = node.condition
        then = node.then
        start = object()
        end = object()
        self.loop_bounds = [start, end]
        self.record_label_location(start)
        self.compile(condition)
        self.add_code_label(code.jump_if_false, end)
        self.compile_block(then)
        self.add_code_label(code.jump, start)
        self.record_label_location(end)
        self.loop_bounds = old

from Object import *

'''
考虑到设计难度，尝试对栈式虚拟机进行开发
简单初版
先压入左操作数，再压入右操作数
读取时先获得右操作数，再获得左操作数
压入：push
弹出：pop
赋值变量：write write_index
读取变量：read read_index
双操作数算数操作： add sub mul div mod power lt gt le ge eq ne and or bitwise_xor bitwise_and bitwise_or bitwise_left_step 
                 bitwise_right_step
单操作数算数操作： logic_not bitwise_not fac neg
'''
from enum import IntEnum


def get_counter():
    """
    得到一个计数器的counter
    :return:
    """
    n = 0

    def inner_counter():
        nonlocal n
        n += 1
        return n - 1

    return inner_counter


auto = get_counter()


class code(IntEnum):
    push = auto()
    push_index = auto()
    pop = auto()
    write = auto()
    read = auto()
    write_index = auto()
    read_index = auto()
    jump_if_false = auto()
    jump_if_true = auto()
    jump = auto()
    get_list = auto()
    get_dict = auto()

    def __repr__(self):
        return f'{self.name.upper()}'


auto = get_counter()


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
    bitwise_xor = auto()
    bitwise_and = auto()
    bitwise_or = auto()
    bitwise_left_step = auto()
    bitwise_right_step = auto()

    logic_not = auto()
    bitwise_not = auto()
    fac = auto()
    neg = auto()

    def __repr__(self):
        return f'{self.name.upper()}'


def is_hashable(node):
    """
    判断对象是否可哈希
    :param node: 要判断的对象
    :return: 可以 True 不可以 False
    """
    try:
        hash(node)
        return True
    except TypeError:
        return False


class Compiler:

    def __init__(self, ast):
        self.node_level = 0
        self.ast = ast
        self.bytecodes = []
        self.direct_add = {int, float, bool, str, type(None), list, dict}
        self.direct_ret_type = {Break_stmt, Continue_stmt}
        self.need_compile = {Binary_expr: self.binary_node, Id: self.read, If_stmt: self.if_node,
                             While_stmt: self.while_node, List: self.process_List_and_Dict,
                             Dict: self.process_List_and_Dict,
                             Assign_expr: self.assign, Index_expr: self.read,
                             Unary_expr: self.unary_node}
        self.need_pop = {Assign_expr, Binary_expr, List, Dict, Unary_expr, Index_expr, Id}
        self.binary_op = {'+': calc.add, '-': calc.sub, '*': calc.mul, '//': calc.div_int, '/': calc.div_float,
                          '%': calc.mod,
                          '**': calc.power,
                          '<': calc.lt, '>': calc.gt, '<=': calc.le, '>=': calc.ge, '==': calc.eq, '!=': calc.ne,
                          '^': calc.bitwise_xor, '&': calc.bitwise_and, '|': calc.bitwise_or,
                          '<<': calc.bitwise_left_step, '>>': calc.bitwise_right_step}
        self.unary_op = {'not': calc.logic_not, '~': calc.bitwise_not, '!': calc.fac, '-': calc.neg}
        self.back_label = []
        self.back_map = {}
        self.hash_map = {}
        self.unhash_map = {}
        self.loop_bounds = None
        self.counter = get_counter()

    def do(self):
        """
        生成字节码
        :return: 字节码
        """
        for i in self.ast:
            self.compile(i)
        # 标记回填具体数值
        for index, label in self.back_label:
            self.bytecodes[index] = (self.bytecodes[index][0], self.back_map[label])
        return self.bytecodes

    def compile(self, node):
        """
        compile 分派
        :param node: 语法树节点
        :return: None | 类型
        """
        self.node_level += 1
        res = None
        t = type(node)
        if t in self.direct_add:
            if t is str:
                if node in self.hash_map:
                    flag = self.hash_map[node]
                else:
                    flag = self.counter()
                    self.hash_map[node] = flag
                self.bytecodes.append((code.push_index, flag))
            elif t is list or t is dict:
                flag = self.counter()
                self.unhash_map[flag] = node
                self.bytecodes.append((code.push_index, flag))
            else:
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
        if self.node_level == 1 and t in self.need_pop:
            self.bytecodes.append((code.pop,))
        self.node_level -= 1
        return res

    def process_List_and_Dict(self, node):
        """
        生成字典和列表相关的字节码
        :param node: List | Dict
        :return: None
        """
        if type(node) is List:
            size = len(node.val)
            for i in node.val:
                self.compile(i)
            self.bytecodes.append((code.get_list, size))
        else:
            size = len(node.val)
            for key in node.val:
                self.compile(key)
                self.compile(node.val[key])
            self.bytecodes.append((code.get_dict, size))

    def read(self, node):
        """
        生成读变量的字节码
        :param node: Id | IndexError
        :return: None
        """
        t = type(node)
        if t is Id:
            name = node.id
            if name in self.hash_map:
                flag = self.hash_map[name]
            else:
                flag = self.counter()
                self.hash_map[name] = flag
            self.bytecodes.append((code.push_index, flag))
            self.bytecodes.append((code.read,))
        else:
            left = node.left
            # right 是 list 封装的
            right = node.right
            self.compile(left)
            self.compile(right[0])
            self.bytecodes.append((code.read_index,))

    def assign(self, node):
        """
        生成写变量的字节码
        :param node: Assign
        :return: None
        """
        op, left, right = node.op, node.left, node.right
        if op == '=':
            t = type(left)
            if t is Id:
                name = left.id
                if name in self.hash_map:
                    flag = self.hash_map[name]
                else:
                    flag = self.counter()
                    self.hash_map[name] = flag
                self.bytecodes.append((code.push_index, flag))
                self.compile(right)
                self.bytecodes.append((code.write,))
            else:
                self.compile(left.left)
                # left 是 Index_expr，left.right 是 list 封装的
                self.compile(left.right[0])
                self.compile(right)
                self.bytecodes.append((code.write_index,))

    def unary_node(self, node):
        """
        单目运算符字节码
        :param node: Unary
        :return: None
        """
        op, val = node.op, node.val
        self.compile(val)
        self.bytecodes.append((self.unary_op[op],))

    def binary_node(self, node):
        """
        双目运算符字节码
        :param node: Binary
        :return: None
        """
        op, left, right = node.op, node.left, node.right
        if op == '&&':
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
        else:
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((self.binary_op[op],))

    def compile_block(self, body):
        """
        生成局部块的字节码
        :param body: 一个块容器
        :return: None
        """
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
        """
        增加一条带有标记的跳转字节码
        :param code_op: 字节码类型
        :param label: 标记
        :return: None
        """
        self.back_label.append((len(self.bytecodes), label))
        self.bytecodes.append((code_op, label))

    def record_label_location(self, label):
        """
        记录某个标记的具体绝对位置
        :param label: 标记
        :return: None
        """
        self.back_map[label] = len(self.bytecodes)

    def if_node(self, node):
        """
        生成 if 语句的字节码
        :param node: if
        :return: None
        """
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
        """
        生成 while 语句的字节码
        :param node: while
        :return: None
        """
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

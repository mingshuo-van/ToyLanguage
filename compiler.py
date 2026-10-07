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
双操作数算数操作： add sub mul div
'''
from enum import IntEnum, auto


class code(IntEnum):
    push = auto()
    pop = auto()
    write = auto()
    read = auto()
    add = auto()
    sub = auto()
    mul = auto()
    div_int = auto()
    div_float = auto()
    jump_if_false = auto()
    jump = auto()


class Compiler:

    def __init__(self, ast):
        self.node_level = 0
        self.ast = ast
        self.bytecodes = []
        self.direct_ret = [int, float, bool, str, None]
        self.need_compile = {Binary_expr: self.binary_node, Id: self.read, If_stmt: self.if_node}

    def do(self):
        for i in self.ast:
            self.compile(i)
        return self.bytecodes

    def compile(self, node):
        self.node_level += 1
        t = type(node)
        if t in self.direct_ret:
            self.bytecodes.append((code.push, node))
        else:
            self.need_compile[t](node)
        self.node_level -= 1

    def read(self, node):
        self.bytecodes.append((code.push, node.id))
        self.bytecodes.append((code.read,))
        if self.node_level == 1:
            self.bytecodes.append((code.pop,))

    def binary_node(self, node):
        op, left, right = node.op, node.left, node.right
        if op == '=':
            self.bytecodes.append((code.push, left.id))
            self.compile(right)
            self.bytecodes.append((code.write,))
        elif op == '+':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((code.add,))
        elif op == '-':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((code.sub,))
        elif op == '*':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((code.mul,))
        elif op == '/':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((code.div_float,))
        elif op == '//':
            self.compile(left)
            self.compile(right)
            self.bytecodes.append((code.div_int,))
        if self.node_level == 1:
            self.bytecodes.append((code.pop,))

    def if_node(self, node):
        back_label = []
        back_map = {}
        condition, then, if_list, otherwise = node.condition, node.then, node.if_list, node.otherwise
        self.compile(condition)
        next = object()
        back_label.append((len(self.bytecodes), next))
        self.bytecodes.append((code.jump_if_false, next))
        # 重置节点层级，保证pop指令的添加无误
        old = self.node_level
        self.node_level = 0
        for i in then:
            self.compile(i)
        end = None
        if if_list or otherwise:
            end = object()
            back_label.append((len(self.bytecodes), end))
            self.bytecodes.append((code.jump, end))
        back_map[next] = len(self.bytecodes)
        # 恢复层级信息，避免其他节点深度判断错误
        self.node_level = old
        if if_list:
            for i in if_list:
                next = object()
                condition = i.condition
                then = i.then
                self.compile(condition)
                back_label.append((len(self.bytecodes), next))
                self.bytecodes.append((code.jump_if_false, next))
                # 重置节点层级，保证pop指令的添加无误
                old = self.node_level
                self.node_level = 0
                for j in then:
                    self.compile(j)
                # 恢复层级信息，避免其他节点深度判断错误
                self.node_level = old
                back_label.append((len(self.bytecodes), end))
                self.bytecodes.append((code.jump, end))
                back_map[next] = len(self.bytecodes)
        if otherwise:
            # 重置节点层级，保证pop指令的添加无误
            old = self.node_level
            self.node_level = 0
            for i in otherwise:
                self.compile(i)
            # 恢复层级信息，避免其他节点深度判断错误
            self.node_level = old
        if end:
            back_map[end] = len(self.bytecodes)
        # 标记回填具体数值
        for index, label in back_label:
            self.bytecodes[index] = (self.bytecodes[index][0], back_map[label])

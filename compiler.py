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



class Compiler:

    def __init__(self, ast):
        self.node_level = 0
        self.ast = ast
        self.bytecodes = []
        self.direct_ret = [int, float, bool, str, None]
        self.need_compile = {Binary_expr: self.binary_node, Id: self.read}

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
        self.bytecodes.append((code.push,node.id))
        self.bytecodes.append((code.read, ))
        if self.node_level == 1:
            self.bytecodes.append((code.pop,))

    def binary_node(self, node):
        op, left, right = node.op, node.left, node.right
        if op == '=':
            self.bytecodes.append((code.push,left.id))
            self.compile(right)
            self.bytecodes.append((code.write,))
            if self.node_level == 1:
                self.bytecodes.append((code.pop,))
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

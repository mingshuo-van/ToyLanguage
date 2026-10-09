from compiler import code, calc
from math import gamma, factorial
from Object import *


class Index:
    """
    包装是否在 hash_map 和 unhash_map 中存在
    """

    def __init__(self, index):
        self.index = index


def fac(n):
    """
    计算阶乘的函数
    :param n: 被施加阶乘计算的数
    :return: 计算后的数
    """
    t = type(n)
    if t is not int and t is not float:
        raise Lang_Err('TypeError', f'{n} is not int or float')
    if n < 0 and n == int(n):
        raise Lang_Err('ValueError', f'{n}! need the num >= 0 or type(num) is float')
    if type(n) is float:
        return gamma(n + 1)
    return factorial(n)


class Func:

    def __init__(self, name, var_list, scope, parent=None):
        self.name = name
        self.var_list = var_list
        self.scope = scope
        self.parent = parent

    def __repr__(self):
        return f'(Func {self.name} {self.var_list})'


class Interpreter_bytecode:
    def __init__(self, bytecodes, hash_map, unhash_map):
        self.bytecodes = bytecodes
        self.hash_map = {v: k for k, v in hash_map.items()}
        self.unhash_map = unhash_map
        self.stack_data = []
        self.stack_frame = []
        self.env = {}
        self.pc = 0
        self.size = len(bytecodes)
        self.op_calc = [
            lambda x, y: x + y,
            lambda x, y: x - y,
            lambda x, y: x * y,
            lambda x, y: x // y,
            lambda x, y: x / y,
            lambda x, y: x % y,
            lambda x, y: x ** y,
            lambda x, y: x < y,
            lambda x, y: x > y,
            lambda x, y: x <= y,
            lambda x, y: x >= y,
            lambda x, y: x == y,
            lambda x, y: x != y,
            lambda x, y: x ^ y,
            lambda x, y: x & y,
            lambda x, y: x | y,
            lambda x, y: x << y,
            lambda x, y: x >> y,
            lambda val: not val,
            lambda val: ~val,
            lambda val: fac(val),
            lambda val: -val
        ]

    def get_target_object(self, num):
        v = [0] * num
        for i in range(num):
            v[i] = self.stack_data.pop()
            if type(v[i]) is Index:
                index = v[i].index
                v[i] = self.hash_map[index] if index in self.hash_map else self.unhash_map[index]
        return v if len(v) > 1 else v[0]

    def do(self):
        """
        执行字节码
        :return: None
        """
        while self.pc < self.size:
            cur = self.bytecodes[self.pc]
            self.pc += 1
            op = cur[0]
            if op is code.push:
                self.stack_data.append(cur[1])
            elif op is code.push_index:
                self.stack_data.append(Index(cur[1]))
            elif op is code.pop:
                self.stack_data.pop()
            elif op is code.write:
                right, left = self.get_target_object(2)
                self.env[left] = right
                self.stack_data.append(right)
            elif op is code.read:
                head = self.get_target_object(1)
                self.stack_data.append(self.env[head])
            elif op is code.write_index:
                value, index, arr = self.get_target_object(3)
                arr[index] = value
                self.stack_data.append(value)
            elif op is code.read_index:
                right, left = self.get_target_object(2)
                self.stack_data.append(left[right])
            elif op is code.get_list:
                size = cur[1]
                arr = self.get_target_object(size)
                arr.reverse()
                self.stack_data.append(arr)
            elif op is code.get_dict:
                size = cur[1]
                arr = {}
                for i in range(size):
                    right, left = self.get_target_object(2)
                    arr[left] = right
                self.stack_data.append(dict(reversed(list(arr.items()))))
            elif op is code.jump_if_false:
                if not self.get_target_object(1):
                    self.pc = cur[1]
            elif op is code.jump_if_true:
                if self.get_target_object(1):
                    self.pc = cur[1]
            elif op is code.jump:
                self.pc = cur[1]
            elif op is code.call_register:
                scope, var_list, name = self.get_target_object(3)
                hash_map = {}
                for k, v in scope['hash_map'].items():
                    hash_map[v] = k
                scope['hash_map'] = hash_map
                self.env[name] = Func(name, var_list, scope, parent=self.env)
            elif op is code.call:
                var_list, func = self.get_target_object(2)
                self.stack_frame.append((self.pc, func))
            elif op <= calc.bitwise_right_step:
                right, left = self.get_target_object(2)
                self.stack_data.append(self.op_calc[op](left, right))
            elif op <= calc.neg:
                self.stack_data.append(self.op_calc[op](self.get_target_object(1)))

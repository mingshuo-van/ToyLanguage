from compiler import code, calc
from math import gamma, factorial
from Object import *


class Var:
    """
    包装在 varname 中存在
    """

    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f'Var({self.index})'


class Const:
    """
    包装在 consts 中存在
    """

    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f'Const({self.index})'


class FuncI:
    """
    包装在 func_scope 中存在
    """

    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f'FuncI({self.index})'


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

    def __init__(self, name, var_list, message, parent=None):
        self.name = name
        self.var_list = var_list
        self.message = message
        self.parent = parent
        self.env = {}

    def __repr__(self):
        return f'(Func {self.name} {self.var_list})'


def get_inner_object(node):
    """
    获得 Inner 包装
    :param node: element
    :return: Inner
    """
    t = type(node)
    if t is int:
        f = InnerInt
    elif t is float:
        f = InnerFloat
    elif t is str:
        f = InnerStr
    elif t is bool:
        f = InnerBool
    else:
        f = None
    return f(node) if f is not None else node


def get_origin_object(node):
    if isinstance(node, Inner):
        return node.val
    return node


inner_flag = object()

from InnerFunc import *


class Interpreter_bytecode:
    def __init__(self, bytecodes, varname, consts, func_scope):
        self.bytecodes = bytecodes
        self.varname = {v: k for k, v in varname.items()}
        self.consts = {v: k for k, v in consts.items()}
        self.func_scope = {v: k for k, v in func_scope.items()}
        self.stack_data = []
        self.stack_frame = []
        self.env = {}
        self.pc = 0
        self.size = len(bytecodes)
        self.op_calc = [
            lambda x, y: x | y if type(y) is dict and type(x) is dict else (
                str(x) + str(y) if type(x) is str or type(y) is str else x + y),
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
        self.old_message = []
        self.builtins_func = {
            'print': Func('print', ['line', 'end'],
                          FuncMessage(inner_flag, {0: 'line', 1: 'end'}, {}, {}, []), self.env)
        }
        self.builtins_map = {
            'print': inner_print
        }

    def get_target_object(self, num):
        v = [0] * num
        for i in range(num):
            v[i] = self.stack_data.pop()
            if type(v[i]) is Var:
                v[i] = self.varname[v[i].index]
            elif type(v[i]) is Const:
                v[i] = self.consts[v[i].index]
            elif type(v[i]) is FuncI:
                v[i] = self.func_scope[v[i].index]
            v[i] = get_origin_object(v[i])
        return v if len(v) > 1 else v[0]

    def start_func(self, func):
        self.old_message.append([self.bytecodes, self.varname, self.consts, self.func_scope, self.env, self.stack_data])
        message = func.message
        self.bytecodes = message.bytecodes
        self.varname = message.varname
        self.consts = message.consts
        self.func_scope = message.func_scope
        self.env = func.env
        self.stack_data = []

    def end_func(self):
        self.bytecodes, self.varname, self.consts, self.func_scope, self.env, self.stack_data = self.old_message.pop()

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
            elif op is code.push_var_index:
                self.stack_data.append(Var(cur[1]))
            elif op is code.push_const_index:
                self.stack_data.append(Const(cur[1]))
            elif op is code.push_func_index:
                self.stack_data.append(FuncI(cur[1]))
            elif op is code.pop:
                self.stack_data.pop()
            elif op is code.write:
                right, left = self.get_target_object(2)
                self.env[left] = right
                self.stack_data.append(right)
            elif op is code.read:
                head = self.get_target_object(1)
                if head in self.env:
                    self.stack_data.append(self.env[head])
                else:
                    get = False
                    if self.old_message:
                        for arr in reversed(self.old_message):
                            if head in arr[4]:
                                self.stack_data.append(arr[4][head])
                                get = True
                                break
                    if not get and head in self.builtins_func:
                        self.stack_data.append(self.builtins_func[head])
                        get = True
                    if not get:
                        raise Lang_Err('NameError', f'{head} is not a name')
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
                arr = self.get_target_object(cur[1])
                name = arr[-1]
                message = arr[0]
                var_list = arr[1:-1]
                var_list.reverse()
                self.env[name] = Func(name, var_list, message, parent=self.env)
            elif op is code.call:
                arr = self.get_target_object(cur[1])
                if type(arr) is list:
                    func: Func = arr[-1]
                    var_list = arr[:-1]
                else:
                    func: Func = arr
                    var_list = []
                var_list.reverse()
                if func.message.bytecodes is not inner_flag:
                    self.stack_frame.append((self.pc, func))
                    for index, name in enumerate(func.var_list):
                        func.env[name] = var_list[index]
                    self.start_func(func)
                    self.pc = 0
                    self.size = len(self.bytecodes)
                else:
                    res = self.builtins_map[func.name](*var_list)
                    self.stack_data.append(get_inner_object(res))
            elif op is code.ret:
                res = self.stack_data[-1]
                self.end_func()
                # 进入新环境可以包装一次
                self.stack_data.append(get_inner_object(res))
                self.pc = self.stack_frame.pop()[0]
                self.size = len(self.bytecodes)
            elif op is code.get_origin:
                # 因为如果被包装成 const_index 或者 var_index
                # 离开当前环境后索引就无效了
                self.stack_data.append(self.get_target_object(1))
            elif op <= calc.bitwise_right_step:
                right, left = self.get_target_object(2)
                self.stack_data.append(
                    get_inner_object(self.op_calc[op](left, right)))
            elif op <= calc.neg:
                val = self.get_target_object(1)
                self.stack_data.append(get_inner_object(self.op_calc[op](val)))

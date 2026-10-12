from compiler import code, calc
from math import gamma, factorial
from Object import *


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
    __slots__ = ('name', 'var_list', 'message', 'parent', 'env')

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

def get_element(node):
    """
    辅助拆箱 cell
    在 read 或 具备 read 语义的情况下用于获得内置元素
    但不会直接用于 write 的 左值
    取决于具体的功能
    :param node: 要处理的元素
    :return: node | Cell.val
    """
    return node.val if type(node) is Cell else node


inner_flag = object()
need_to_be_cell = object()

from InnerFunc import *


class Interpreter_bytecode:
    __slots__ = ('bytecodes', 'varname', 'consts', 'func_scope', 'stack_data', 'stack_frame', 'env', 'scope', 'op_calc'
                 , 'old_message', 'builtins_func', 'builtins_map')

    def __init__(self, bytecodes, varname, consts, func_scope):
        self.bytecodes = bytecodes
        self.varname = {v: k for k, v in varname.items()}
        self.consts = {v: k for k, v in consts.items()}
        self.func_scope = {v: k for k, v in func_scope.items()}
        self.stack_data = []
        self.stack_frame = []
        self.env = {}
        self.scope = [self.env, None]  # 本层变量作用域引用, 父全作用域引用
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
                          FuncMessage(inner_flag, {0: 'line', 1: 'end'}, {}, {}), self.env),
            'time': Func('time', [],
                         FuncMessage(inner_flag, {0: 'line', 1: 'end'}, {}, {}), self.env)
        }
        self.builtins_map = {
            'print': inner_print,
            'time': inner_time
        }

    def get_target_object(self, num):
        v = [self.stack_data.pop() for _ in range(num)]
        return v if len(v) > 1 else v[0]

    def start_func(self, func):
        self.old_message.append(
            [self.bytecodes, self.varname, self.consts, self.func_scope, self.env, self.stack_data, self.scope])
        message = func.message
        self.bytecodes = message.bytecodes
        self.varname = message.varname
        self.consts = message.consts
        self.func_scope = message.func_scope
        self.scope = [func.env, func.parent]
        self.env = func.env
        self.stack_data = []

    def end_func(self):
        self.bytecodes, self.varname, self.consts, self.func_scope, self.env, self.stack_data, self.scope = self.old_message.pop()

    def do(self):
        """
        执行字节码
        :return: None
        """
        pc = 0
        bytecodes = self.bytecodes
        size = len(bytecodes)
        get_target_object = self.get_target_object
        op_calc = self.op_calc
        while pc < size:
            cur = bytecodes[pc]
            pc += 1
            op = cur[0]
            if isinstance(op, calc):
                if op <= calc.bitwise_right_step:
                    right, left = get_target_object(2)
                    right = get_origin_object(right)
                    left = get_origin_object(left)
                    self.stack_data.append(
                        get_inner_object(op_calc[op](left, right)))
                elif op <= calc.neg:
                    val = get_target_object(1)
                    val = get_origin_object(val)
                    self.stack_data.append(get_inner_object(op_calc[op](val)))
            elif op is code.push:
                self.stack_data.append(cur[1])
            elif op is code.push_var_index:
                self.stack_data.append(self.varname[cur[1]])
            elif op is code.read_var_index:
                index = cur[1]
                head = self.varname[index]
                get = False
                scope = self.scope
                while scope is not None:
                    if head in scope[0]:
                        self.stack_data.append(scope[0][head])
                        get = True
                        break
                    else:
                        scope = scope[1]
                if not get and head in self.builtins_func:
                    self.stack_data.append(self.builtins_func[head])
                    get = True
                if not get:
                    raise Lang_Err('NameError', f'{head} is not a name')
            elif op is code.read_const_index:
                index = cur[1]
                head = self.consts[index]
                self.stack_data.append(head)
            elif op is code.read_func_index:
                index = cur[1]
                head = self.func_scope[index]
                self.stack_data.append(head)
            elif op is code.pop:
                self.stack_data.pop()
            elif op is code.write:
                right, left = get_target_object(2)
                self.env[get_origin_object(left)] = right
                self.stack_data.append(right)
            elif op is code.write_index:
                value, index, arr = get_target_object(3)
                arr[get_origin_object(index)] = value
                self.stack_data.append(value)
            elif op is code.read_index:
                right, left = get_target_object(2)
                self.stack_data.append(left[get_origin_object(right)])
            elif op is code.read_slice:
                right, left, arr = get_target_object(3)
                want = InnerList()
                for i in arr[get_origin_object(left):get_origin_object(right)]:
                    want.append(i)
                self.stack_data.append(want)
            elif op is code.get_list:
                x = cur[1]
                arr = self.stack_data[-x:]
                del self.stack_data[-x:]
                want = InnerList()
                for i in arr:
                    want.append(i)
                self.stack_data.append(want)
            elif op is code.get_dict:
                x = cur[1]
                arr = {}
                for i in range(x):
                    right, left = get_target_object(2)
                    arr[get_origin_object(left)] = right
                want = InnerDict()
                for k, v in dict(reversed(list(arr.items()))).items():
                    want[k] = v
                self.stack_data.append(want)
            elif op is code.jump_if_false:
                if not get_target_object(1):
                    pc = cur[1]
            elif op is code.jump_if_true:
                if get_target_object(1):
                    pc = cur[1]
            elif op is code.jump:
                pc = cur[1]
            elif op is code.call_register:
                arr = get_target_object(cur[1])
                name = get_origin_object(arr[-1])
                message = arr[0]
                var_list = arr[1:-1]
                var_list.reverse()
                self.env[name] = Func(name, var_list, message, parent=self.scope)
            elif op is code.call:
                arr = get_target_object(cur[1])
                if type(arr) is list:
                    func: Func = arr[-1]
                    var_list = arr[:-1]
                else:
                    func: Func = arr
                    var_list = []
                func.env = {}
                var_list.reverse()
                if func.message.bytecodes is not inner_flag:
                    self.stack_frame.append((pc, func))
                    for index, name in enumerate(func.var_list):
                        func.env[get_origin_object(name)] = var_list[index]
                    varname = func.message.varname
                    for index in func.message.cells:
                        # 这是要用 Cell 包装的本函数内部变量
                        func.env[get_origin_object(varname[index])] = Cell(None)
                    for level, index in func.message.need_to_get:
                        # 这是本层要沿 parent 链追溯并记录的内容
                        parent = func.parent
                        for _ in range(level):
                            parent = parent[1]
                        func.env[varname[index]] = parent[0][varname[index]]
                    self.start_func(func)
                    pc = 0
                    bytecodes = self.bytecodes
                    size = len(bytecodes)
                else:
                    res = self.builtins_map[func.name](*var_list)
                    self.stack_data.append(get_inner_object(res))
            elif op is code.ret:
                res = get_target_object(1)
                self.end_func()
                # 进入新环境可以尝试包装成内置类型一次
                self.stack_data.append(get_inner_object(res))
                pc = self.stack_frame.pop()[0]
                bytecodes = self.bytecodes
                size = len(bytecodes)

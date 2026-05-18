from Object import *
from math import gamma, factorial
from time import time
from random import random, seed, randrange
import sys


def inner_str(object):
    """
    内置字符串转换函数，对一些元素修改了转换格式
    :param object:
    :return: object转换成的字符串
    """
    if object is None:
        return 'null'
    if object is True:
        return 'true'
    if object is False:
        return 'false'
    return str(object)


class Func:
    """
    函数信息，用于在函数表用以 name : Func 的形式注册函数
    词法作用域，支持闭包
    """

    def __init__(self, vars, body, parent):
        self.vars = vars
        self.body = body
        self.parent = parent

    def __repr__(self):
        return f'Func({self.vars})'


def inner_print(s, end):
    """
    内置打印函数，对一些元素修改了打印格式，默认换行
    :param s: 要打印的字符串
    :param end:指定结尾使用的字符串，默认为换行符
    :return: None
    """
    if s is None:
        s = 'null'
    elif s is True:
        s = 'true'
    elif s is False:
        s = 'false'
    print(s, end=end)


def push(box, idx):
    """
    用于把元素idx加入列表box中
    :param box:列表
    :param idx:元素
    :return: None
    """
    if type(box) is not list:
        raise KeyError(f'{box} must be list')
    box.append(idx)


# 这是给字典的键值对迭代的迭代器类型，专门保存起来是为了方便后续inner_next某些操作
iter_item_type = type(iter({}.items()))
func_type = type(Func([], [], None))


class IterEnd:
    """
    迭代器迭代结束的信标
    """
    pass


class VirtualMachine:
    """
    虚拟机类
    """

    def __init__(self, ast):
        # 要消费的语法树
        self.ast = ast
        # 存储变量和函数定义的全局字典，只有这个作用域的生命周期延续几乎整个程序运行期间
        # 其他各级作用域随生随灭，闭包情况除外
        self.scope = {'id': {}}
        # 内置函数声明
        self.builtins_scope = {'print': Func([Id('s'), Id('end')], [], None),
                               'vars': Func([], [], None),
                               'get': Func([Id('s')], [], None),
                               'int': Func([Id('s')], [], None),
                               'float': Func([Id('s')], [], None),
                               'str': Func([Id('s')], [], None),
                               'bool': Func([Id('s')], [], None),
                               'list': Func([Id('s')], [], None),
                               'dict': Func([Id('s')], [], None),
                               'push': Func([Id('box'), Id('idx')], [], None),
                               'pop': Func([Id('box'), Id('key')], [], None),
                               'has': Func([Id('box'), Id('key')], [], None),
                               'iter_key': Func([Id('box')], [], None),
                               'iter_value': Func([Id('box')], [], None),
                               'iter_item': Func([Id('box')], [], None),
                               'next': Func([Id('iter_pointer')], [], None),
                               'join': Func([Id('box'), Id('s')], [], None),
                               'split': Func([Id('target'), Id('cut'), Id('count')], [], None),
                               'strip': Func([Id('s')], [], None),
                               'lstrip': Func([Id('s')], [], None),
                               'rstrip': Func([Id('s')], [], None),
                               'find': Func([Id('target'), Id('sub'), Id('start'), Id('end')], [], None),
                               'count': Func([Id('target'), Id('sub'), Id('start'), Id('end')], [], None),
                               'replace': Func([Id('target'), Id('old'), Id('new'), Id('count')], [], None),
                               'len': Func([Id('target')], [], None),
                               'time': Func([], [], None),
                               'seed': Func([Id('instance')], [], None),
                               'random': Func([], [], None),
                               'randrange': Func([Id('start'), Id('end'), Id('step')], [], None),
                               'open': Func([Id('address'), Id('mode'), Id('coding')], [], None),
                               'read': Func([Id('file_handle')], [], None),
                               'write': Func([Id('file_handle'), Id('word')], [], None),
                               'close': Func([Id('file_handle')], [], None),
                               'exit': Func([Id('num')], [], None)
                               }
        # 内置函数实际执行体
        self.func = {
            'print': lambda: inner_print(self.read_variable(Id('s'), tolerance=True, default='', only_local=True),
                                         self.read_variable(Id('end'), tolerance=True, default='\n', only_local=True)),
            'vars': lambda: print(
                self.cur_scope['parent']['id'] if 'parent' in self.cur_scope else self.cur_scope['id']),
            'get': lambda: input(self.read_variable(Id('s'), tolerance=True, default='', only_local=True)),
            'int': lambda: int(self.read_variable(Id('s'), tolerance=True, default=0, only_local=True)),
            'float': lambda: float(self.read_variable(Id('s'), tolerance=True, default=0.0, only_local=True)),
            'str': lambda: inner_str(self.read_variable(Id('s'), tolerance=True, default='', only_local=True)),
            'bool': lambda: bool(self.read_variable(Id('s'), tolerance=True, default=False, only_local=True)),
            'list': lambda: list(self.read_variable(Id('s'), tolerance=True, default='', only_local=True)),
            'dict': lambda: dict(self.read_variable(Id('s'), tolerance=True, default='', only_local=True)),
            'push': lambda: push(self.read_variable(Id('box'), only_local=True),
                                 self.read_variable(Id('idx'), only_local=True)),
            'pop': lambda: self.read_variable(Id('box'), only_local=True).pop(
                self.read_variable(Id('key'), only_local=True)),
            'has': lambda: self.read_variable(Id('key'), only_local=True) in self.read_variable(
                Id('box'),
                only_local=True),
            'iter_key': self.iter_key,
            'iter_value': self.iter_value,
            'iter_item': self.iter_item,
            'next': lambda: self.inner_next(self.read_variable(Id('iter_pointer'), only_local=True)),
            'join': lambda: self.read_variable(Id('s'), tolerance=True, default='', only_local=True).join(
                self.read_variable(Id('box'), only_local=True)
            ),
            'split': lambda: self.read_variable(Id('target')).split(
                self.read_variable(Id('cut'), tolerance=True, default=' ', only_local=True),
                maxsplit=self.read_variable(Id('count'), tolerance=True, default=-1, only_local=True)
            ),
            'strip': lambda: self.read_variable(Id('s'), only_local=True).strip(),
            'rstrip': lambda: self.read_variable(Id('s'), only_local=True).rstrip(),
            'lstrip': lambda: self.read_variable(Id('s'), only_local=True).lstrip(),
            'find': self.find,
            'count': self.count,
            'replace': lambda: self.read_variable(Id('target'), only_local=True).replace(
                self.read_variable(Id('old'), only_local=True),
                self.read_variable(Id('new'), only_local=True),
                count=self.read_variable(Id('count'), tolerance=True, default=-1, only_local=True)
            ),
            'len': lambda: len(self.read_variable(Id('target'), only_local=True)),
            'time': time,
            'seed': lambda: seed(self.read_variable(Id('instance'), only_local=True, tolerance=True)),
            'random': random,
            'randrange': lambda: randrange(
                self.read_variable(Id('start'), only_local=True),
                self.read_variable(Id('end'), only_local=True),
                self.read_variable(Id('step'), tolerance=True, default=1, only_local=True)
            ),
            'open': lambda: open(
                self.read_variable(Id('address'), only_local=True),
                self.read_variable(Id('mode'), only_local=True, tolerance=True, default='r'),
                encoding=self.read_variable(Id('coding'), only_local=True, tolerance=True, default='utf8')
            ),
            'read': lambda: self.read_variable(Id('file_handle'), only_local=True).readlines(),
            'write': lambda: self.read_variable(Id('file_handle'), only_local=True).write(
                self.read_variable(Id('word'), only_local=True)
            ),
            'close': lambda: self.read_variable(Id('file_handle'), only_local=True).close(),
            'exit': self.inner_exit
        }
        # 当前作用域指针
        self.cur_scope = self.scope
        # 单目运算路由表
        self.unary_op = {'-': lambda x: -self.run(x), '!': self.fac,
                         '~': lambda x: ~self.run(x), 'not': lambda x: not self.run(x),
                         }
        # 双目运算路由表
        self.binary_op = {'+': self.inner_plus,
                          '-': lambda x, y: self.run(x) - self.run(y),
                          '*': lambda x, y: self.run(x) * self.run(y), '**': lambda x, y: self.run(x) ** self.run(y),
                          '/': lambda x, y: self.run(x) / self.run(y), '//': lambda x, y: self.run(x) // self.run(y),
                          '^': lambda x, y: self.run(x) ^ self.run(y), '%': lambda x, y: self.run(x) % self.run(y),
                          '&': lambda x, y: self.run(x) & self.run(y), '|': lambda x, y: self.run(x) | self.run(y),
                          '>': lambda x, y: self.run(x) > self.run(y), '<': lambda x, y: self.run(x) < self.run(y),
                          '>=': lambda x, y: self.run(x) >= self.run(y), '<=': lambda x, y: self.run(x) <= self.run(y),
                          '&&': lambda x, y: False if not self.run(x) else bool(self.run(y)),
                          '||': lambda x, y: True if self.run(x) else bool(self.run(y)),
                          '==': lambda x, y: self.run(x) == self.run(y), '!=': lambda x, y: self.run(x) != self.run(y),
                          '<<': lambda x, y: self.run(x) << self.run(y), '>>': lambda x, y: self.run(x) >> self.run(y),
                          '=': self.write_local_variable,
                          ':=': self.write_nonlocal_variable,
                          '=>': self.write_global_variable,
                          'index': self.index
                          }
        # 供self.run函数短路返回的类型集合
        self.kind = {int, float, str, bool, list, dict, type(None), iter_item_type,
                     type(iter({})), type(iter({}.values())), Return_stmt, Break_stmt, Continue_stmt,
                     type(sys.__stdin__), type(IterEnd), func_type}
        # self.fun路由表
        self.ret = {Unary_expr: self.unary,
                    Binary_expr: self.binary,
                    While_stmt: self.while_stmt,
                    If_stmt: self.if_stmt,
                    Call_define_stmt: self.call_define_stmt,
                    Call_stmt: self.call_stmt,
                    Id: self.read_variable,
                    Builtins_stmt: self.builtins_stmt,
                    List: self.transform_iterable_object_and_calc_inner_node,
                    Dict: self.transform_iterable_object_and_calc_inner_node
                    }

    def inner_exit(self):
        raise Exit_Error(self.read_variable(Id('num'), tolerance=True, default=0, only_local=True))

    def fac(self, n):
        """
        计算阶乘的函数
        :param n: 被施加阶乘计算的数
        :return: 计算后的数
        """
        n = self.run(n)
        if n < 0 and n == int(n):
            raise ValueError(f'{n}! need the num >= 0 or type(num) is float')
        if type(n) is float:
            return gamma(n + 1)
        return factorial(n)

    def iter_key(self):
        """
        返回一个字典键的迭代器
        :return: 一个键迭代器
        """
        # 避免_iter_end被覆盖或未被创建，主动赋值一次
        self.cur_scope['parent']['id']['_iter_end'] = IterEnd
        return iter(self.read_variable(Id('box'), only_local=True))

    def iter_value(self):
        """
        返回一个字典值的迭代器
        :return: 一个值迭代器
        """
        # 避免_iter_end被覆盖或未被创建，主动赋值一次
        self.cur_scope['parent']['id']['_iter_end'] = IterEnd
        return iter(self.read_variable(Id('box'), only_local=True).values())

    def iter_item(self):
        """
        返回一个字典键值对的迭代器
        :return: 一个键值对迭代器
        """
        # 避免_iter_end被覆盖或未被创建，主动赋值一次
        self.cur_scope['parent']['id']['_iter_end'] = IterEnd
        return iter(self.read_variable(Id('box'), only_local=True).items())

    def inner_plus(self, x, y):
        """
        内置加法函数
        :param x: 第一个操作数
        :param y: 第二个操作数
        :return: 加法运算结果
        """
        # 计算出对应的操作数
        # 因为 x 和 y 可能是需要执行的操作
        x = self.run(x)
        y = self.run(y)
        # 支持dict和str的加法
        # 任何一个操作数是str，就把另一个操作数也变成字符串
        tx = type(x)
        if tx is str:
            return x + inner_str(y)
        if type(y) is str:
            return inner_str(x) + y
        if tx is dict:
            # 因为只有当两个操作数都是dict时，加法才合法
            # 且前面已经排除了两个中有一个是字符串的情况
            # 所以直接计算，如果不对会自然报错
            return x | y
        # 说明是其他类型，直接计算
        return x + y

    def inner_next(self, iter_pointer):
        # 驱动迭代器执行
        # 迭代器消费完毕会返回提示结束的信标
        try:
            t = next(iter_pointer)
            return [self.run(t[0]), self.run(t[1])] if type(iter_pointer) is iter_item_type else [self.run(t)]
        except StopIteration:
            return IterEnd

    def find(self):
        """
        str.find()的包装，用于寻找在字符串target中sub字串的第一个出现的位置的索引
        :return: 一个整型，代表索引
        """
        # target: 代表主字符串
        # sub: 要寻找的字串
        # start: 开始寻找的位置，默认为0
        # end: 结束寻找的位置，默认为字符串长
        s = self.read_variable(Id('target'), only_local=True)
        return s.find(
            self.read_variable(Id('sub'), only_local=True),
            self.read_variable(Id('start'), tolerance=True, default=0, only_local=True),
            self.read_variable(Id('end'), tolerance=True, default=len(s), only_local=True)
        )

    def count(self):
        """
        str.count()的包装，用于获取在字符串target中sub字串出现的次数
        :return: 一个整型，代表次数
        """
        s = self.read_variable(Id('target'), only_local=True)
        return s.count(
            self.read_variable(Id('sub'), only_local=True),
            self.read_variable(Id('start'), tolerance=True, default=0, only_local=True),
            self.read_variable(Id('end'), tolerance=True, default=len(s), only_local=True)
        )

    def transform_iterable_object_and_calc_inner_node(self, object):
        """
        把内置List和Dict转换成list和dict，同时对其中的元素求值
        如 List[Call_stmt]->list[具体结果]
        :param object: 要转换的对象
        :return: 转换后的对象
        """
        t = type(object)
        if t is List:
            # 这里不直接修改object是为了避免修改了节点状态
            # 否则，第一次调用的run会让后面所有的object变成第一次调用的样子
            # 例如可以避免当类似[outer()]的闭包模式导致的不符合直觉问题
            object = object.val
            res = []
            for i in range(len(object)):
                res.append(self.run(object[i]))
            object = res
        elif t is Dict:
            object = object.val
            res = {}
            for k in object.keys():
                res[self.run(k)] = self.run(object[k])
            object = res
        return object

    def run(self, node):
        """
        解释器的一级路由，把具体的AST节点路由到对应的计算函数
        :param node:
        :return: 直接返回非内部节点，或节点求值后的内容，内部节点返回的内容有可能是None
        """
        key = type(node)
        if key in self.kind:
            return node
        return self.ret[key](node)

    def read_variable(self, name, tolerance=False, default=None, only_local=False):
        """
        读取变量以返回具体的值（可能是不可变或可变对象）
        :param name: 要查询的内容，一定是Id
        :param tolerance: 在查询变量失败时是否不报错，宽松处理
        :param default: 宽松处理时，兜底的默认返回值
        :param only_local: 是否仅在当前的作用域查询
        :return: 查询的结果
        """
        scope = self.cur_scope
        if only_local:
            # 声明仅在本层查询时，只对本层处理
            if name.id not in scope['id']:
                if tolerance:
                    return default
                raise KeyError(f'{name.id} not a variable in local scope')
            return scope['id'][name.id]
        while name.id not in scope['id']:
            # 寻找有对应标识符的作用域
            # 以初始作用域为起点，按照创建时的父作用域链拾阶而上
            if scope != self.scope:
                scope = scope['parent']
            elif not tolerance:
                raise KeyError(f'{name.id} not a variable')
            else:
                return default
        return scope['id'][name.id]

    def write_variable(self, name, node, scope):
        """
        具体执行写操作的函数，不论write_local,write_nonlocal,write_global都最终调用它
        :param name: 被写入的左值，可能是Binary_expr(index)或者Id
        :param node: 要写入的内容，可能是另一个可以返回值的节点，或者直接可以写入的字面量
        :param scope: 目标作用域
        :return: 返回写入的内容
        """
        stack = []
        while type(name) is Binary_expr:
            name, idx = name.left, name.right
            stack.append(idx)
        if stack:
            arr = scope['id'][name.id]
            for i in range(len(stack) - 1, 0, -1):
                if len(stack[i]) == 2:
                    arr = arr[self.run(stack[i][0]):self.run(stack[i][1])]
                else:
                    arr = arr[self.run(stack[i][0])]
            value = self.run(node)
            if len(stack[0]) == 2:
                arr[self.run(stack[0][0]):self.run(stack[0][1])] = value
            else:
                arr[self.run(stack[0][0])] = value
            return value
        else:
            scope['id'][name.id] = self.run(node)
            return scope['id'][name.id]

    def write_local_variable(self, name, node, scope=None):
        """
        在本层写入内容
        :param name:  被写入的左值，可能是Binary_expr(index)或者Id
        :param node:  要写入的内容，可能是另一个可以返回值的节点，或者直接可以写入的字面量
        :param scope: : 目标作用域，默认为当前作用域
        :return: 写入的内容
        """
        if scope is None:
            scope = self.cur_scope
        return self.write_variable(name, node, scope)

    def write_nonlocal_variable(self, name, node):
        """
        在本层写入内容
        :param name:  被写入的左值，可能是Binary_expr(index)或者Id
        :param node:  要写入的内容，可能是另一个可以返回值的节点，或者直接可以写入的字面量
        :return: 写入的内容
        """
        scope = self.cur_scope
        if 'parent' in scope:
            # 如果不是全局作用域，直接切换到其父级作用域
            scope = scope['parent']
        name_origin = name
        while type(name) is Binary_expr:
            # 如果是一个需要可索引的左值，则获得其真正的Id
            name = name.left
        while name.id not in scope['id']:
            # 拿到正确的作用域
            if scope != self.scope:
                scope = scope['parent']
            else:
                raise KeyError(f'the variable called {name.id} not in parent scope')
            # 适配write_variable的逻辑，传入未拆分的原始Binary_expr节点
        return self.write_variable(name_origin, node, scope)

    def write_global_variable(self, name, node):
        """
        在全局作用域写入内容
        :param name:  被写入的左值，可能是Binary_expr(index)或者Id
        :param node:  要写入的内容，可能是另一个可以返回值的节点，或者直接可以写入的字面量
        :return: 写入的内容
        """
        name_origin = name
        while type(name) is Binary_expr:
            name = name.left
        if name.id not in self.scope['id']:
            raise KeyError(f'the variable called {name.id} not in global scope')
        return self.write_variable(name_origin, node, self.scope)

    def unary(self, node):
        """
        单目运算的负责函数
        :param node: 要计算的单目节点
        :return: 计算结果
        """
        op, val = node.op, node.val
        if op == 'remove':
            if val.id in self.cur_scope['id']:
                self.cur_scope['id'].pop(val.id)
        else:
            return self.unary_op[op](val)

    def index(self, left, right):
        """
        用于处理索引操作
        :param left: 双目节点左操作数
        :param right: 双目节点右操作数
        :return: 取址结果
        """
        a = self.run(left)
        if len(right) == 2:
            return a[self.run(right[0]):self.run(right[1])]
        return a[self.run(right[0])]

    def binary(self, node):
        """
        处理双目运算节点的函数
        :param node: 要处理的双目运算节点
        :return: 可能的节点返回值 或 None
        """
        op, left, right = node.op, node.left, node.right
        if op == '?=':
            op = node.op = '='
            right = node.right = self.run(right)
        return self.binary_op[op](left, right)

    def while_stmt(self, node):
        """
        负责执行while循环的函数
        :param node: while节点
        :return: Node 或 可能的 return节点
        """
        condition, then = node.condition, node.then
        while self.run(condition):
            for i in then:
                flag = self.run(i)
                t = type(flag)
                if t is Break_stmt:
                    # break相当于函数结束
                    return
                if t is Continue_stmt:
                    # continue相当于小循环结束
                    break
                if t is Return_stmt:
                    # return需要原样送往上层
                    return flag

    def if_stmt(self, node):
        """
        负责执行if循环的函数
        :param node: if节点
        :return: Node 或 可能的 return/break/continue节点
        """
        condition, then, el_if, otherwise = node.condition, node.then, node.if_list, node.otherwise
        # 记录本次if是否已经执行过某个分支了
        do = False
        if self.run(condition):
            # 执行if
            do = True
            for i in then:
                flag = self.run(i)
                t = type(flag)
                if t is Break_stmt or t is Continue_stmt or t is Return_stmt:
                    return flag
        if not do:
            # 如果if没有执行
            if el_if:
                # 尝试执行elif
                for i in el_if:
                    then = i.then
                    if self.run(i.condition):
                        for j in then:
                            flag = self.run(j)
                            t = type(flag)
                            if t is Break_stmt or t is Continue_stmt or t is Return_stmt:
                                return flag
                        # 如果elif执行了，记录已经执行过某个分支了
                        do = True
                        # 不必继续尝试接下来的循环，可以跳出了
                        break
        # 否则，尝试执行else
        if not do and otherwise:
            for i in otherwise:
                flag = self.run(i)
                t = type(flag)
                if t is Break_stmt or t is Continue_stmt or t is Return_stmt:
                    return flag

    def call_define_stmt(self, node):
        """
        处理函数定义节点
        :param node: 函数定义节点
        :return: None
        """
        name, vars, body = node.name, node.vars, node.body
        # 三个参数分别是形参列表，函数体，父级作用域
        f = Func(vars, body, self.cur_scope)
        # 把当前函数记录在父级作用域
        self.cur_scope['id'][name.id] = f
        if self.cur_scope != self.scope:
            for i in body:
                if type(i) is Binary_expr and i.op == ':=':
                    # 寻找引用的父级作用域变量
                    name = i.left
                    if type(name) is Binary_expr and name.op == 'index':
                        while type(name) is Binary_expr:
                            name = name.left
                    search = self.cur_scope
                    while name.id not in search['id']:
                        if search != self.scope:
                            search = search['parent']
                        else:
                            raise KeyError(f'{name.id} is not a variable')
                    # 记录引用，供之后分析释放未引用变量占用的内存
                    search['be_quoted'][name.id] = None

    def switch_call_scope_and_binds_arguments(self, name, vars, search):
        """
        在执行函数时切换作用域并绑定实参到形参
        :param name: Id类，函数名
        :param vars: 实参列表
        :param search: 当前作用域
        :return: 目标Func函数体 或 None
        """
        if search == self.builtins_scope:
            # 当调用内置函数时走快速通道
            if name.id not in search:
                raise KeyError(f'{name.id} is not a valid function name')
        else:
            # 按照作用域链查找函数定义
            while name.id not in search['id']:
                if search != self.scope:
                    search = search['parent']
                else:
                    if name.id in self.builtins_scope:
                        return None
                    else:
                        raise KeyError(f'{name.id} not is a valid function name')
        f = search[name.id] if search == self.builtins_scope else search['id'][name.id]
        # 创建当前要执行函数的局部作用域
        local_scope = {'parent': self.cur_scope if search == self.builtins_scope else f.parent, 'id': {},
                       'be_quoted': {}
                       }
        # 进行形参实参绑定
        for key, val in zip(f.vars, vars):
            self.write_local_variable(key, self.run(val), local_scope)
        # 切换作用到已经准备好的局部作用域
        self.cur_scope = local_scope
        return f

    def call_stmt(self, node):
        """
        函数调用节点执行
        :param node: 函数调用节点
        :return: 函数调用节点的返回值
        """
        name, vars = node.name, node.vars
        if type(name) is not Id:
            # 对于调用函数没有函数名，而是另一个函数的返回值时
            # 用内置临时名字承接对应函数的返回值，继续执行
            # 如果该函数没有返回一个可以执行的函数
            # 在接下来的流程中会自然报错
            self.cur_scope['id']['[temp_'] = self.run(name)
            name = Id('[temp_')
        old_scope = self.cur_scope
        f = self.switch_call_scope_and_binds_arguments(name, vars, self.cur_scope)
        res = None
        if f is None:
            # 用户没有定义可调用的函数，尝试作为内置函数执行
            res = self.builtins_stmt(node)
        else:
            for i in f.body:
                flag = self.run(i)
                if type(flag) is Return_stmt:
                    res = self.run(flag.val)
                    break

        if f:
            # 分析有无闭包并回收无关变量的内存
            be_quoted = self.cur_scope['be_quoted']
            for k, v in self.cur_scope['id'].items():
                if k in be_quoted or type(v) is func_type:
                    be_quoted[k] = v
            self.cur_scope['id'] = {}
            for k, v in be_quoted.items():
                self.cur_scope['id'][k] = v
        self.cur_scope = old_scope
        if name.id == '[temp_':
            # 回收内置函数，避免污染符号表
            self.cur_scope['id'].pop('[temp_')
        return res

    def builtins_stmt(self, node):
        """
        执行内置函数节点调用的函数
        :param node: 内置节点或普通函数调用节点
        :return: 函数节点返回值
        """
        name, vars = node.name, node.vars
        if name.id not in self.builtins_scope:
            raise KeyError(f'{name.id} not a inner function')
        old_scope = self.cur_scope
        self.switch_call_scope_and_binds_arguments(name, vars, self.builtins_scope)
        key = name.id
        res = self.func[key]()
        # 分析可能的闭包情况，当前内置函数应该无闭包实现
        # 但保留，保持和call_stmt的对称
        be_quoted = self.cur_scope['be_quoted']
        for k, v in self.cur_scope['id'].items():
            if k in be_quoted or type(v) is func_type:
                be_quoted[k] = v
        self.cur_scope['id'] = {}
        for k, v in be_quoted.items():
            self.cur_scope['id'][k] = v
        self.cur_scope = old_scope
        return res

    def vm(self):
        """
        对外调用的接口
        :return: None
        """
        try:
            for i in self.ast:
                # 顺序执行整个代码文件的每一个AST
                self.run(i)
        except Exit_Error as e:
            print(f'exit the code program with {str(e)}')

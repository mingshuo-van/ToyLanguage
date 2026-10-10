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
函数注册： call_register
函数调用： call
函数返回： ret
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
    push_var_index = auto()
    push_const_index = auto()
    push_func_index = auto()
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
    call_register = auto()
    call = auto()
    ret = auto()

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
        self.direct_ret_type = {Break_stmt, Continue_stmt}
        self.need_compile = {Binary_expr: self.binary_node, Id: self.read, If_stmt: self.if_node,
                             While_stmt: self.while_node, List: self.process_List_and_Dict,
                             Dict: self.process_List_and_Dict,
                             Assign_expr: self.assign, Index_expr: self.read,
                             Unary_expr: self.unary_node,
                             Call_define_stmt: self.call_define,
                             Return_stmt: self.ret_node,
                             Call_stmt: self.call,
                             int: self.inner, float: self.inner, str: self.inner, bool: self.inner}
        self.need_pop = {Assign_expr, Binary_expr, List, Dict, Unary_expr, Index_expr, Id, Call_stmt}
        self.binary_op = {'+': calc.add, '-': calc.sub, '*': calc.mul, '//': calc.div_int, '/': calc.div_float,
                          '%': calc.mod,
                          '**': calc.power,
                          '<': calc.lt, '>': calc.gt, '<=': calc.le, '>=': calc.ge, '==': calc.eq, '!=': calc.ne,
                          '^': calc.bitwise_xor, '&': calc.bitwise_and, '|': calc.bitwise_or,
                          '<<': calc.bitwise_left_step, '>>': calc.bitwise_right_step}
        self.unary_op = {'not': calc.logic_not, '~': calc.bitwise_not, '!': calc.fac, '-': calc.neg}
        self.back_label = []
        self.back_map = {}
        self.varname = {}
        self.consts = {}
        self.func_scope = {}
        self.old_compile_env = []
        self.loop_bounds = None
        self.func_counter = get_counter()
        self.varname_counter = get_counter()
        self.consts_counter = get_counter()

    def inner(self, node):
        """
        处理 python 的内置元素包装
        :param node: element
        :return: None
        """
        t = type(node)
        if t is int:
            f = InnerInt
        elif t is float:
            f = InnerFloat
        elif t is str:
            f = InnerStr
        else:
            f = InnerBool
        node = f(node)
        self.bytecodes.append((code.push_const_index, self.get_consts_flag(node)))

    def get_varname_flag(self, node):
        """
        得到变量名的 flag
        :param node: 变量名
        :return: flag
        """
        if node not in self.varname:
            self.varname[node] = self.varname_counter()
        return self.varname[node]

    def get_consts_flag(self, node):
        """
        得到字面量的 flag
        :param node: 字面量
        :return: flag
        """
        if node not in self.consts:
            self.consts[node] = self.consts_counter()
        return self.consts[node]

    def get_func_scope_flag(self, node):
        """
        得到对应元素的flag
        :param node: 一些函数相关的对象
        :return: int
        """
        if node not in self.func_scope:
            self.func_scope[node] = self.func_counter()
        return self.func_scope[node]

    def set_new_compile_env(self):
        # 临时修改以bytecodes为代表的多个容器的指向，以存储函数执行体的字节码进独立的块并控制独立的常量池
        self.old_compile_env.append(
            [self.bytecodes, self.back_label, self.back_map, self.varname, self.consts, self.func_scope,
             self.loop_bounds,
             self.func_counter, self.varname_counter, self.consts_counter, []])
        self.bytecodes = []
        self.back_label = []
        self.back_map = {}
        self.varname = {}
        self.consts = {}
        self.func_scope = {}
        self.loop_bounds = None
        self.func_counter = get_counter()
        self.varname_counter = get_counter()
        self.consts_counter = get_counter()

    def recovery_old_compile_env(self):
        self.bytecodes, self.back_label, self.back_map, self.varname, self.consts, self.func_scope, \
            self.loop_bounds, \
            self.func_counter, self.varname_counter, self.consts_counter, cells = self.old_compile_env.pop()

        return cells

    def real_write_label_location(self):
        """
        标记回填具体数值
        :return: None
        """
        for index, label in self.back_label:
            self.bytecodes[index] = (self.bytecodes[index][0], self.back_map[label])

    def do(self):
        """
        生成字节码
        :return: 字节码
        """
        for i in self.ast:
            self.compile(i)
        self.real_write_label_location()
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
        if t is None:
            self.bytecodes.append((code.push, None))
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
        生成读变量的字节码，需要考虑在函数内部时寻找到闭包捕获的变量，然后记录在cells（当前该功能未实现）
        :param node: Id | IndexError
        :return: None
        """
        t = type(node)
        if t is Id:
            flag = self.get_varname_flag(node.id)
            self.bytecodes.append((code.push_var_index, flag))
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
                flag = self.get_varname_flag(left.id)
                self.bytecodes.append((code.push_var_index, flag))
                self.compile(right)
                self.bytecodes.append((code.write,))
            else:
                self.compile(left.left)
                # left 是 Index_expr，left.right 是 list 封装的
                self.compile(left.right[0])
                self.compile(right)
                self.bytecodes.append((code.write_index,))

    def ret_node(self, node):
        """
        生成 ret 字节码
        :param node: return
        :return: None
        """
        self.compile(node.val)
        self.bytecodes.append((code.ret,))

    def call_define(self, node):
        """
        函数注册字节码生成
        :param node: call_define
        :return: None
        """
        name, var_list, body = node.name, node.vars, node.body
        self.set_new_compile_env()
        for i in var_list:
            # 保证形参一定被记录在varname中
            self.get_varname_flag(i.id)
        for i in body:
            self.compile(i)
        if self.bytecodes[-1][0] is not code.ret:
            self.bytecodes.append((code.push, None))
            self.bytecodes.append((code.ret,))
        self.real_write_label_location()
        message = FuncMessage(self.bytecodes,
                              {k: v for v, k in self.varname.items()},
                              {k: v for v, k in self.consts.items()},
                              {k: v for v, k in self.func_scope.items()},
                              None)
        cells = self.recovery_old_compile_env()
        message.cells = cells
        self.bytecodes.append((code.push_var_index, self.get_varname_flag(name.id)))
        for i in var_list:
            self.bytecodes.append((code.push_var_index, self.get_varname_flag(i.id)))

        self.bytecodes.append((code.push_func_index, self.get_func_scope_flag(message)))

        self.bytecodes.append((code.call_register, len(var_list) + 2))

    def call(self, node):
        name, var_list = node.name, node.vars
        self.bytecodes.append((code.push_var_index, self.get_varname_flag(name.id)))
        self.bytecodes.append((code.read,))
        for i in var_list:
            self.compile(i)
        self.bytecodes.append((code.call, len(var_list) + 1))

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

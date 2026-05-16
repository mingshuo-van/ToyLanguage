r"""
factor -> number | '(' assign ')' | '-' power | factor '!' |id|str|bool| '!' factor | '~' factor
power  -> factor ** power | factor
term   -> term * power | term / power | term % power | power
expr   -> expr + term | expr - term | term
bitwise_step -> bitwise_step >> expr | bitwise_step << expr | expr
comp   -> bitwise_step == bitwise_step | bitwise_step != bitwise_step |
            bitwise_step >= bitwise_step | bitwise_step <= bitwise_step |
            bitwise_step > bitwise_step | bitwise_step < bitwise_step | bitwise_step
bitwise_and -> bitwise_and & comp | comp
bitwise_xor -> bitwise_xor ^ bitwise_and | bitwise_and
bitwise_or -> bitwise_or '|' bitwise_xor | bitwise_xor
logic_and -> logic_and && bitwise_or | bitwise_or
logic_or -> logic_and '||' logic_or | logic_and
assign -> id = assign | id := assign | id => assign | id ?= assign | logic_or

program -> stmt_list

stmt -> if_stmt | while_stmt | call_define_stmt | call_stmt | assign | remove_stmt | builtins_stmt

stmt_list -> stmt*

if_stmt -> 'if' '(' assign ')' '{' stmt_list '}' ( 'elif' '(' assign ')' '{'stmt_list})* ( 'else' '{'stmt_list'}')?

while_stmt -> 'while' '(' assign ')' '{'stmt_list'}'

call_define_stmt -> 'fn' id '(' (id ( ',' id)*)?  ')' '{' stmt_list '}'

call_stmt -> id '(' (assign ( ',' assign)*)? ')'

builtins_stmt -> '::' id '(' (assign ( ',' assign)*? ')'

remove_stmt -> 'remove' id
"""


class Expression:
    pass


class Unary_expr(Expression):
    """
    单目运算节点，包括 逻辑非，阶乘，负号，按位非
    """

    def __init__(self, op, val):
        self.op = op
        self.val = val

    def __repr__(self):
        return f'Unary_expr({self.op} {self.val})'


class Binary_expr(Expression):
    """
    双目运算节点
    一切双目运算符或可以视为双目运算符的运算符，包括getitem语义也被其修饰
    """

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f'Binary_expr({self.op} {self.left} {self.right})'


class Id(Expression):
    """
    标识符节点
    """

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f'ID({self.id})'


class List(Expression):
    """
    修饰list,其节点的求值会延迟到具体执行时
    """

    def __init__(self, arr):
        self.val = arr

    def __repr__(self):
        return f'List({self.val})'


class Dict(Expression):
    """
    修饰dict，其节点的求值会延迟到具体执行时
    """

    def __init__(self, d):
        self.val = d

    def __repr__(self):
        return f'Dict({self.val})'


class Statement:
    pass


class If_stmt(Statement):
    """
    if 语句
    """

    def __init__(self, condition, then, if_list=None, otherwise=None):
        """
        :param condition: if 条件
        :param then: if body
        :param if_list: elif 链，作为一个 if(condition){body}存储
        :param otherwise: else body
        """
        self.condition = condition
        self.then = then
        self.if_list = if_list
        self.otherwise = otherwise

    def __repr__(self):
        s = f'if({self.condition}){{{self.then}}}'
        if self.if_list:
            for i in self.if_list:
                s += 'elif' + '(' + repr(i.condition) + ')' + '{' + repr(i.then) + '}'
        if self.otherwise:
            s += 'else' + '{' + repr(self.otherwise) + '}'
        return '(' + s + ')'


class While_stmt(Statement):
    """
    while 语句
    """

    def __init__(self, condition, then):
        """
        :param condition: while 条件
        :param then: while body
        """
        self.condition = condition
        self.then = then

    def __repr__(self):
        return f'(while({self.condition}){{{self.then}}})'


class Call_define_stmt(Statement):
    def __init__(self, name, vars, body):
        self.name = name
        self.vars = vars
        self.body = body

    def __repr__(self):
        return f'(fn {self.name} ({self.vars}) {{{self.body}}})'


class Call_stmt(Statement):
    """
    函数调用，在没有自定义和内置函数同名的函数时也可以调用内置函数
    """

    def __init__(self, name, vars):
        """"
        :param name:函数名，是标识符
        :param vars: 参数列表
        """
        self.name = name
        self.vars = vars

    def __repr__(self):
        return f'(call {self.name} ({self.vars}))'


class Builtins_stmt(Statement):
    """
    内置函数调用，用::前缀指定调用的是内置函数
    """

    def __init__(self, name, vars):
        """"
        :param name:函数名，是标识符
        :param vars: 参数列表
        """
        self.name = name
        self.vars = vars

    def __repr__(self):
        return f'(builtins {self.name} ({self.vars}))'


class Break_stmt(Statement):
    """
    break
    """

    def __repr__(self):
        return f'break'


class Continue_stmt(Statement):
    """
    continue
    """

    def __repr__(self):
        return f'continue'


class Return_stmt(Statement):
    """
    return 语句
    """

    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return f'(return {self.val})'


class Exit_Error(Exception):
    """
    exit Exception，以区分退出当前代码和退出整个解释器程序
    使用异常，保证一定能穿透到上层
    """

    def __init__(self, val):
        super().__init__(val)

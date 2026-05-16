from Object import *
from math import gamma,factorial


def fac(n):
    """
    计算阶乘的函数
    :param n: 被施加阶乘计算的数
    :return: 计算后的数
    """
    if n < 0 and n == int(n):
        raise ValueError(f'{n}! need the num >= 0 or type(num) is float')
    if type(n) is float:
        # 碰到浮点数时，调用标准库的gamma函数计算，返回的是一个浮点数
        return gamma(n + 1)
    # 如果是整数，用标准库的factorial计算，保证返回的是整型
    return factorial(n)


def inner_str(object):
    if object is None:
        return 'null'
    if object is True:
        return 'true'
    if object is False:
        return 'false'
    return str(object)


def is_bool_morgan_form(node):
    """
    判断当前节点是否可以用德摩根律处理
    当前的优化思路是采用两种变换，分别是:
    not a and not b -> not (a or b)
    not a or not b -> not (a and b)
    对应的内部节点类似：
    and(not(a),not(b)) -> not(or(a,b))
    or(not(a),not(b)) -> not(and(a,b))
    :param node: 要被判断的节点
    :return: 可以处理->True，不能处理->False
    """
    if type(node) is not Binary_expr:
        # or 或 and 必须首先是一个Binary_expr类
        return False
    if not (node.op == '&&' or node.op == '||'):
        # 其中的运算操作必须是 and 或 or
        return False
    if not (type(node.left) is Unary_expr and type(node.right) is Unary_expr):
        # not是被Unary_expr修饰的
        return False
    if not (node.left.op == 'not' and node.right.op == 'not'):
        # 具体运算符必须是not
        return False
    return True


def is_bool_double_neg_form(node):
    """
    判断当前节点是否可以消除多重否定
    要避免类似 not not x -> x 后原来的布尔语义可能丢失的问题
    所以能够处理的类型如下：
    要么是 not not not a -> not a，奇数个not，可以保证最后一定会留下not
    要么是 not not x 且 x 自带 bool 语义，在这里是 Binary_expr(&&)和Binary_expr(||)
    对于 x 是 True 或 False 的情况不在这里处理
    因为后面的fold_constant会连带处理
    同时还能减少一次if判断
    :param node:要判断的节点
    :return: 可以处理->True，不能处理->False
    """
    # 判断当前节点是否是not
    if not (type(node) is Unary_expr and node.op == 'not'):
        return False
    # 判断是否还有一个not
    if not (type(node.val) is Unary_expr and node.val.op == 'not'):
        return False
    # 判断内层是否自带bool语义
    t = type(node.val.val)
    if t is Binary_expr:
        # 这部分内置在if里，是避免t是一个没有op属性的类型
        op = node.val.val.op
        if op == '||' or op == '&&':
            return True
        return False
    # 否则判断是否有第三个not
    # 通过递归处理，必然保证正确
    # 若 not not not not -> not not -> 判断是否可化简 -> 处理成功
    # 若 not not not not not -> not not not -> not -> 处理成功
    if t is Unary_expr and node.val.val.op == 'not':
        return True
    return False


class Optimizer:
    """
    优化器类
    """

    def __init__(self, ast):
        self.ast = ast
        # 递归优化的叶子节点，在此终止递归
        self.ret_from_optimize = {int, float, bool, str, Break_stmt, Continue_stmt, Id}
        # fold_constance中必然可以折叠的节点，另有特殊操作行为的节点在函数中特判
        self.literal_used = {int, float, bool}
        # 为fold_constance准备的通用节点，特殊行为另有在fold_constance中的特判
        self.binary_op = {
            '+': lambda x, y: x + y, '-': lambda x, y: x - y,
            '*': lambda x, y: x * y, '**': lambda x, y: x ** y,
            '/': lambda x, y: x / y, '//': lambda x, y: x // y,
            '^': lambda x, y: x ^ y, '%': lambda x, y: x % y,
            '&': lambda x, y: x & y, '|': lambda x, y: x | y,
            '>': lambda x, y: x > y, '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y, '<=': lambda x, y: x <= y,
            '&&': lambda x, y: x and y, '||': lambda x, y: x or y,
            '==': lambda x, y: x == y, '!=': lambda x, y: x != y,
            '<<': lambda x, y: x << y, '>>': lambda x, y: x >> y,
        }

    def bool_optimize(self, node):
        """
        做关于bool的上下文无关形式优化，例如应用德摩根律，做多重否定消除
        :param node: 要处理的节点
        :return: 处理后的节点
        """
        t = type(node)
        if t in self.ret_from_optimize:
            return node
        if t is Unary_expr:
            # 先计算子节点，再计算当前的节点，保证子节点本身已经得到优化
            node.val = self.bool_optimize(node.val)
            if is_bool_double_neg_form(node):
                # 消除一对双重否定后生成的新节点可能仍有优化的空间
                node = self.bool_optimize(node.val.val)
        elif t is Binary_expr:
            # 先计算子节点
            node.left = self.bool_optimize(node.left)
            node.right = self.bool_optimize(node.right)
            if is_bool_morgan_form(node):
                op = '&&' if node.op == '||' else '||'
                # 因为上面已经做过递归优化子节点，所以左右节点的节点也已经是优化过的了，直接取值即可
                left = node.left.val
                right = node.right.val
                node = self.bool_optimize(Unary_expr('not', Binary_expr(op, left, right)))
        elif t is If_stmt:
            # 对于 if 的condition,then,elif的condition,then和else的body一个个做处理
            node.condition = self.bool_optimize(node.condition)
            then = node.then
            for i in range(len(then)):
                then[i] = self.bool_optimize(then[i])
            otherwise = node.otherwise
            if otherwise:
                for i in range(len(otherwise)):
                    otherwise[i] = self.bool_optimize(otherwise[i])
            if_list = node.if_list
            if if_list:
                for i in range(len(if_list)):
                    if_list[i] = self.bool_optimize(if_list[i])
        elif t is While_stmt:
            # 处理while的condition和then
            node.condition = self.bool_optimize(node.condition)
            then = node.then
            for i in range(len(then)):
                then[i] = self.bool_optimize(then[i])
        elif t is Call_define_stmt:
            # 处理函数定义语句的body
            body = node.body
            for i in range(len(body)):
                body[i] = self.bool_optimize(body[i])
        elif t is Call_stmt or t is Builtins_stmt:
            # 处理函数调用语句的实参
            vars = node.vars
            for i in range(len(vars)):
                vars[i] = self.bool_optimize(vars[i])
        elif t is Return_stmt:
            # 处理函数的返回语句
            node.val = self.bool_optimize(node.val)
        elif t is List:
            # 处理List
            for i in range(len(node.val)):
                node.val[i] = self.bool_optimize(node.val[i])
        elif t is Dict:
            # 处理Dict
            for k in node.val:
                node.val[k] = self.bool_optimize(node.val[k])
        return node

    def fold_constance(self, node):
        """
        把可以在运行前计算且计算后不使节点数或内存占用显著增长的计算提前
        :param node: 要处理的节点
        :return: 处理后的节点
        """
        t = type(node)
        if t in self.ret_from_optimize:
            return node
        if t is Unary_expr:
            # 递归处理单目节点的子节点，保证当前处理时其子节点已经是最优
            node.val = val = self.fold_constance(node.val)
            op = node.op
            t = type(val)
            # 通过最优子节点判断当前节点是否能优化
            if t in self.literal_used:
                if op == 'not':
                    node = not val
                elif op == '!':
                    node = fac(val)
                elif op == '-':
                    node = -val
                else:
                    node = ~val
            elif op == 'not':
                if t is str:
                    node = not val
                elif t is List or t is Dict:
                    node = not val.val
        elif t is Binary_expr:
            # 递归处理双目的子节点，保证当前节点处理时其子节点已经是最优
            node.left = left = self.fold_constance(node.left)
            node.right = right = self.fold_constance(node.right)
            op = node.op
            x = type(left)
            y = type(right)
            xi = x in self.literal_used
            yi = y in self.literal_used
            if xi and yi:
                node = self.binary_op[op](left, right)
            elif op == '+':
                # 处理 + 运算符的特殊行为
                if x is str and (yi or y is str):
                    node = left + inner_str(right)
                elif y is str and xi:
                    node = inner_str(left) + right
                elif x is Dict and y is Dict:
                    node = Dict(left.val | right.val)
                elif x is List and y is List:
                    node = List(left.val + right.val)
            elif op == '&&':
                # 可以隐式转bool的节点先转bool，并更新对应的判断参数，方便接下来基于常量的优化
                if x is str:
                    node.left = left = bool(left)
                elif x is List or x is Dict:
                    node.left = left = bool(left.val)
                if y is str:
                    node.right = right = bool(right)
                elif y is List or y is Dict:
                    node.right = right = bool(right.val)
                # 任何一个操作数为假，整个 and 运算为假
                if left is False or right is False:
                    node = False
                # 任何一个操作数为真，则其对运算无贡献
                if left is True:
                    return right
                if right is True:
                    return left
            elif op == '||':
                # 可以隐式转bool的节点先转bool，并更新对应的判断参数，方便接下来基于常量的优化
                if x is str:
                    node.left = left = bool(left)
                elif x is List or x is Dict:
                    node.left = left = bool(left.val)
                if y is str:
                    node.right = right = bool(right)
                elif y is List or y is Dict:
                    node.right = right = bool(right.val)
                # 任何一个操作数为真，整个 or 运算为真
                if left is True or right is True:
                    node = True
                # 任何一个操作数为假，则其对整个 or 运算无贡献
                if left is False:
                    return right
                if right is False:
                    return left
        elif t is If_stmt:
            # 对于 if 的condition,then,elif的condition,then和else的body一个个做处理
            node.condition = self.fold_constance(node.condition)
            then = node.then
            for i in range(len(then)):
                then[i] = self.fold_constance(then[i])
            otherwise = node.otherwise
            if otherwise:
                for i in range(len(otherwise)):
                    otherwise[i] = self.fold_constance(otherwise[i])
            if_list = node.if_list
            if if_list:
                for i in range(len(if_list)):
                    if_list[i] = self.fold_constance(if_list[i])
        elif t is While_stmt:
            # 处理while的condition和then
            node.condition = self.fold_constance(node.condition)
            then = node.then
            for i in range(len(then)):
                then[i] = self.fold_constance(then[i])
        elif t is Call_define_stmt:
            # 处理函数定义语句的body
            body = node.body
            for i in range(len(body)):
                body[i] = self.fold_constance(body[i])
        elif t is Call_stmt or t is Builtins_stmt:
            # 处理函数调用语句的实参
            vars = node.vars
            for i in range(len(vars)):
                vars[i] = self.fold_constance(vars[i])
        elif t is Return_stmt:
            # 处理函数返回值
            node.val = self.fold_constance(node.val)
        elif t is List:
            # 对List的元素逐个处理
            for i in range(len(node.val)):
                node.val[i] = self.fold_constance(node.val[i])
        elif t is Dict:
            # 对Dict的元素逐个处理
            for k in node.val:
                node.val[k] = self.fold_constance(node.val[k])
        return node

    def optimize(self):
        # 供外界调用的方法
        for i in range(len(self.ast)):
            self.ast[i] = self.fold_constance(self.bool_optimize(self.ast[i]))

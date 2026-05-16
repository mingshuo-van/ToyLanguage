from Object import *


class Parser:
    """
    进行语法分析，构建AST的语法解析器类
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0  # 指向当前正在处理的token的索引
        self.length = len(self.tokens)  # token 列表的总长度

    def renew_tokens_length(self):
        """
        主动调用重新校准tokens记录的长度
        但不会重置其他内置参数
        :return: None
        """
        self.length = len(self.tokens)

    def reset_tokens(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.length = len(self.tokens)

    def consume(self):
        """
        消耗当前的一个token，并返回消耗的token
        :return: token or None
        """
        token = self.tokens[self.pos] if self.pos < self.length else None
        self.pos += 1
        return token

    def expect(self, type, val=None):
        """
        :param type: 期待的token.type
        :param val: 期待的token.val，如果不指定可以留空，只会比较type
        :return: 消耗的token
        """
        token = self.tokens[self.pos] if self.pos < self.length else None
        if token is None:
            raise TypeError(f'unexpected token {token}')
        self.consume()
        if val is None:
            if not token.type == type:
                raise TypeError(f'unexpected token {token}')
        elif not (token.type == type and token.val == val):
            raise TypeError(f'unexpected token {token}')
        return token

    def program(self):
        """
        用于递归下降解析程序
        :return: 存放AST语句的一个列表
        """
        return self.stmt_list()

    def stmt_list(self):
        """
        用于解析语句块
        :return: [(stmt(,stmt)*)?]
        """
        if self.pos >= self.length or self.tokens[self.pos].type == '}':
            # 如果进入就是}或者进入后整个AST就立刻消费完成
            # 说明当前的语句块是空块，返回空列表
            return []
        # 消除左递归，解析一个语句，然后解析后面的语句块
        stmt = self.stmt()
        res = [stmt]
        while self.pos < self.length and self.tokens[self.pos].type != '}':
            res.append(self.stmt())
        return res

    def stmt(self):
        """
        专门用于解析语句
        :return: 解析的语句
        """
        token = self.tokens[self.pos] if self.pos < self.length else None
        t = token.type
        # 这里拿到当前token不立刻消耗，在if-elif链具体判断出对应要调用的语句后
        # 根据对应语句的实际需要，决定是直接消耗当前token还是保留供被调用语句消耗
        if t == 'if':
            # 解析条件判断语句
            return self.if_stmt()
        elif t == 'while':
            # 解析循环语句
            return self.while_stmt()
        elif t == 'fn':
            # 解析函数定义语句
            return self.call_define_stmt()
        elif t == 'id':
            # 碰到普通标识符，当表达式处理
            return self.assign()
        elif t == 'break':
            # 直接返回break类
            self.consume()
            return Break_stmt()
        elif t == 'continue':
            # 直接返回continue类
            self.consume()
            return Continue_stmt()
        elif t == 'return':
            # 返回return语句
            # 根据情况判断有无返回值
            self.consume()
            if self.pos < self.length and self.tokens[self.pos].type != '}':
                return Return_stmt(self.assign())
            else:
                return Return_stmt(None)
        elif t == 'remove':
            # 返回定义的remove语句
            return self.remove_stmt()
        else:
            # 其他情况，当表达式处理
            return self.assign()

    # 下方所有代码，具体注释参照定于与Object.py文件上方的文法即可
    # 不写具体的函数级注释

    def remove_stmt(self):
        self.consume()
        name = self.consume()
        return Unary_expr('remove', Id(name.val))

    def if_stmt(self):
        self.consume()
        self.expect('(')
        condition = self.assign()
        self.expect(')')
        self.expect('{')
        then = self.stmt_list()
        self.expect('}')
        if_list = []
        while self.pos < self.length and self.tokens[self.pos].type == 'elif':
            self.consume()
            self.expect('(')
            condition_elif = self.assign()
            self.expect(')')
            self.expect('{')
            then_elif = self.stmt_list()
            self.expect('}')
            if_list.append(If_stmt(condition_elif, then_elif))
        otherwise = None
        if self.pos < self.length and self.tokens[self.pos].type == 'else':
            self.consume()
            self.expect('{')
            otherwise = self.stmt_list()
            self.expect('}')
        return If_stmt(condition, then, if_list if if_list else None, otherwise)

    def while_stmt(self):
        self.consume()
        self.expect('(')
        condition = self.assign()
        self.expect(')')
        self.expect('{')
        then = self.stmt_list()
        self.expect('}')
        return While_stmt(condition, then)

    def call_define_stmt(self):
        self.consume()
        name = self.expect('id')
        name = Id(name.val)
        self.expect('(')
        vars = []
        while self.pos < self.length and self.tokens[self.pos].type == 'id':
            vars.append(Id(self.tokens[self.pos].val))
            self.consume()
            if self.tokens[self.pos].type == ')':
                break
            else:
                self.expect(',')
        self.expect(')')
        self.expect('{')
        body = self.stmt_list()
        self.expect('}')
        return Call_define_stmt(name, vars, body)

    def call_stmt(self):
        self.expect('(')
        vars = []
        if self.pos < self.length and self.tokens[self.pos].type != ')':
            vars.append(self.assign())
            while self.pos < self.length and self.tokens[self.pos].type == ',':
                self.consume()
                vars.append(self.assign())
        self.expect(')')
        return vars

    def factor(self):
        token = self.tokens[self.pos] if self.pos < self.length else None
        self.consume()
        cast = {'int': int, 'str': str, 'float': float, 'true': lambda x: True, 'false': lambda x: False,
                'null': lambda x: None}
        if token.type in cast:
            node = cast[token.type](token.val)
        elif token.type == '(':
            rest = self.assign()
            self.expect(')')
            node = rest
        elif token.type == '-':
            rest = self.power()
            node = Unary_expr('-', rest)
        elif token.type == 'id':
            node = Id(token.val)
            if self.pos < self.length and self.tokens[self.pos].type == '(':
                node = Call_stmt(node, self.call_stmt())
                while self.pos < self.length and self.tokens[self.pos].type == '(':
                    node = Call_stmt(node, self.call_stmt())
        elif token.type == '::':
            node = self.builtins_stmt()
        elif token.type == '!':
            node = Unary_expr('not', self.factor())
        elif token.type == '~':
            node = Unary_expr('~', self.factor())
        elif token.type == '[':
            node = self.parse_list()
        elif token.type == '{':
            node = self.parse_dict()
        else:
            raise TypeError(f'unexpected {token}')
        while self.pos < self.length and self.tokens[self.pos].type == '[':
            self.consume()
            is_slice = False
            if self.tokens[self.pos].type == ':':
                a = None
                b = None
                is_slice = True
                self.consume()
            else:
                a = self.assign()
                b = None
                if self.tokens[self.pos].type == ':':
                    is_slice = True
                    self.consume()
                    b = self.assign()
            self.expect(']')
            arr = [a]
            if is_slice:
                arr.append(b)
            node = Binary_expr('index', node, arr)
            if self.pos < self.length and self.tokens[self.pos].type == '(':
                node = Call_stmt(node, self.call_stmt())
        while self.pos < self.length and self.tokens[self.pos].type == '!':
            self.consume()
            node = Unary_expr('!', node)
        return node

    def builtins_stmt(self):
        call = self.factor()
        return Builtins_stmt(call.name, call.vars)

    def parse_list(self):
        arr = []
        if self.pos < self.length and self.tokens[self.pos].type == ']':
            self.consume()
            return List(arr)
        while self.pos < self.length:
            arr.append(self.assign())
            if self.tokens[self.pos].type == ',':
                self.consume()
            if self.tokens[self.pos].type == ']':
                break
        self.consume()
        return List(arr)

    def parse_dict(self):
        d = {}
        if self.pos < self.length and self.tokens[self.pos].type == '}':
            self.consume()
            return Dict(d)
        while self.pos < self.length:
            key = self.assign()
            self.expect(':')
            val = self.assign()
            d[key] = val
            if self.tokens[self.pos].type == ',':
                self.consume()
            if self.tokens[self.pos].type == '}':
                break
        self.consume()
        return Dict(d)

    def power(self):
        token = self.factor()
        if self.pos < self.length and self.tokens[self.pos].type == '**':
            self.consume()
            token = Binary_expr('**', token, self.power())
        return token

    def term(self):
        token = self.power()
        while self.pos < self.length and self.tokens[self.pos].type in {'*', '/', '%', '//'}:
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.power())
        return token

    def expr(self):
        token = self.term()
        while self.pos < self.length and self.tokens[self.pos].type in {'+', '-'}:
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.term())
        return token

    def bitwise_step(self):
        token = self.expr()
        while self.pos < self.length and (self.tokens[self.pos].type == '>>' or self.tokens[self.pos].type == '<<'):
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.expr())
        return token

    def comp(self):
        token = self.bitwise_step()
        if self.pos < self.length and self.tokens[self.pos].type in {'==', '!=', '>=', '<=', '>', '<'}:
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.bitwise_step())
        return token

    def bitwise_and(self):
        token = self.comp()
        while self.pos < self.length and self.tokens[self.pos].type == '&':
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.comp())
        return token

    def bitwise_xor(self):
        token = self.bitwise_and()
        while self.pos < self.length and self.tokens[self.pos].type == '^':
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.bitwise_and())
        return token

    def bitwise_or(self):
        token = self.bitwise_xor()
        while self.pos < self.length and self.tokens[self.pos].type == '|':
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.bitwise_xor())
        return token

    def logic_and(self):
        token = self.bitwise_or()
        while self.pos < self.length and self.tokens[self.pos].type == '&&':
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.bitwise_or())
        return token

    def logic_or(self):
        token = self.logic_and()
        while self.pos < self.length and self.tokens[self.pos].type == '||':
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.logic_and())
        return token

    def assign(self):
        token = self.logic_or()
        if self.pos < self.length and self.tokens[self.pos].type in {'=', ':=', '=>', '?='}:
            op = self.tokens[self.pos].type
            self.consume()
            token = Binary_expr(op, token, self.assign())
        return token

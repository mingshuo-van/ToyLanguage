import sys

sys.setrecursionlimit(10000)
sys.set_int_max_str_digits(0)


class Token:
    """
    Token类，如果是关键字，采用type == val == keyword
    否则，type in {int,float,str,id}
    """

    def __init__(self, type, val):
        self.type = type
        self.val = val

    def __repr__(self):
        return f'{self.type}  {self.val}'


class Tokenizer:
    """
    分词器类
    """

    def __init__(self, address):
        if address != '':
            with open(address, 'r', encoding='utf8') as f:
                self.txt = [line.strip() for line in f]
            self.pos = 0  # 列定位
            self.index = 0  # 行定位
            self.length = len(self.txt)  # 行数
            self.cnt = len(self.txt[0]) if self.length > 0 else 0  # 当前解析的行长
        # 准备辅助集合
        # 用于存储合法的标识符构成符号
        self.valid_variable_chars = {'_', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        x = ord('a')
        y = ord('A')
        for i in range(26):
            self.valid_variable_chars.add(chr(x + i))
            self.valid_variable_chars.add(chr(y + i))
        # 内置关键字
        self.inner = {'while', 'true', 'false', 'if', 'elif', 'else', 'fn', 'break', 'continue', 'return', 'remove',
                      'null',
                      '==', '!=', '>=', '<=', '&&', '||', '<<', '>>', '**', ':=', '=>', '?=', '//', '::',
                      '+', '-', '*', '/', '%', '^', '&', '|', '~', '!', '<', '>', '(', ')', '{', '}', '[', ']', ',',
                      '.', '=', ':'}
        # 主要用于判断某token开头是否是数字
        self.digit = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        # 判断整型的合法构成字符
        self.digit_int = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_'}
        # 判断浮点型的合法构成字符
        # 浮点型执行类似1e5这样的形式，也可以写1e5-3这样的格式，但是不支持1e-3，可以写1/1e3代替
        self.digit_float = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_', '.', 'E', 'e'}

    def renew_txt_length(self):
        """
        可以手动调用更新总行数
        :return: None
        """
        self.length = len(self.txt)

    def reset_address(self, address):
        """
        可以更新要执行的代码文件地址
        会自动把需要更新的内置参数更新
        :param address:新的代码文件地址
        :return: None
        """
        with open(address, 'r', encoding='utf8') as f:
            self.txt = [line.strip() for line in f]
        self.pos = 0
        self.index = 0
        self.length = len(self.txt)
        self.cnt = len(self.txt[0]) if self.length > 0 else 0  # 当前解析的行长

    def cur(self):
        """
        如果本行没结束，或本文件未遍历完，返回当前字符
        否则返回空
        :return: 当前字符 or None
        """
        if self.index < self.length and self.pos < self.cnt:
            return self.txt[self.index][self.pos]
        return None

    def peek(self):
        """
        窥探下一个字符
        :return:下一个字符 or None
        """
        if self.index < self.length and self.pos + 1 < self.cnt:
            return self.txt[self.index][self.pos + 1]
        if self.index + 1 < self.length:
            return self.txt[self.index + 1][0]
        return None

    def consume(self):
        """
        消耗当前字符并返回，同时返回是否即将换行的信息
        :return: 被消耗的字符,是否即将换行
        """
        token = self.cur()
        if self.pos < self.cnt:
            self.pos += 1
        elif self.index < self.length:
            self.index += 1
            self.pos = 0
            self.cnt = len(self.txt[self.index]) if self.index < self.length else 0
        return token, self.pos >= self.cnt

    def jump(self):
        """
        跳过空格
        :return:None
        """
        if self.cur() is None:
            self.next_line()
        while self.cur() == ' ':
            self.consume()

    def next_line(self):
        """
        主动换行
        :return:None
        """
        self.index += 1
        self.pos = 0
        self.cnt = len(self.txt[self.index]) if self.index < self.length else 0

    def is_id(self, s: str):
        """
        判断传入的字符串是否是合法的标识符
        :param s: 要被判断的字符串
        :return: 是合法的字符串则返回True，否则返回False
        """
        if not s:
            # 空字符串不合法
            return False
        if s[0] in self.digit:
            # 合法标识符的首字符不能是数字
            return False
        for i in range(1, len(s)):
            if s[i] not in self.valid_variable_chars:
                # 只要出现了不合法的字符，就说明这个字符串不是一个合法的标识符
                return False
        return True

    def is_int(self, s: str):
        """
        判断传入的字符串是否是合法的整型
        :param s: 要被判断的字符串
        :return: 是->True,不是->False
        """
        if not s:
            # 空字符串不是合法的整型
            return False
        for i in s:
            if i not in self.digit_int:
                # 出现任何不属于合法整型的字符，就不是合法的整型
                return False
        return True

    def is_float(self, s: str):
        """
        判断传入的字符串是否是合法的浮点型
        :param s: 要被判断的字符串
        :return: 是->True,不是->False
        """
        if not s:
            # 空字符串不是合法的浮点型
            return False
        point = False
        e = False
        for i in s:
            if i not in self.digit_float:
                # 出现任何不属于合法整型的字符，就不是合法的整型
                return False
            if i == '.':
                if not point:
                    # 首次出现小数点，记录
                    point = True
                else:
                    # 出现多次小数点，不合法
                    raise ValueError(f'two point in float {s}')
            if i == 'e' or i == 'E':
                if not e:
                    # 首次出现科学计数法符号
                    e = True
                else:
                    # 科学计数法符号只能出现一次
                    raise ValueError(f'two e|E in float {s}')
        return True

    def get_whole_couple_block(self, flag):
        """
        当遇到成对的符号时，调用获得整个字符串，如 "" ,符号必须一样
        :param flag: 成对的符号中的其中一个
        :return: 获得的包括成对符号本身的字符串
        """
        count = 1
        res = self.cur()
        self.consume()
        while count & 1:
            while self.cur() is None:
                self.consume()
                if self.index >= self.length:
                    raise TypeError(f'the counts of {flag} must be a even {res}')
            if self.cur() == flag:
                count += 1
            if self.cur() == '\\':
                # 当遇到转义符号时，替换合法的转义符号，否则，吃掉转义符号继续进行
                if self.peek() not in set("\'\";\\"):
                    res += {'n': '\n', 't': '\t', 'r': '\r'}[self.peek()]
                    self.consume()
                    self.consume()
                    continue
                else:
                    self.consume()
            res += self.cur()
            self.consume()
        return res

    def get_one_token(self):
        """
        一次调用，返回一个完整Token
        :return: Token
        """
        res = ''
        self.jump()
        cur = self.cur()
        if cur is None:
            return None
        kind = None
        # 这里用type仅仅是因为 kind is type 操作比 kind == "str" 更便宜而已
        # 用的具体类型只是随便选的而已
        if 'a' <= cur <= 'z' or 'A' <= cur <= 'Z':
            kind = str
        elif '0' <= cur <= '9':
            kind = int
        elif cur == '_':
            kind = bool
        elif cur in set('(){}[],.'):
            # 检测括号
            self.consume()
            return Token(cur, cur)
        if cur == '\'' or cur == '\"':
            # 检测字符串
            return Token('str', self.get_whole_couple_block(cur)[1:-1])
        while cur and cur != ' ':
            if cur == '#':
                self.next_line()
                break
            if cur == ';':
                self.consume()
                break
            res += cur
            _, next_line = self.consume()
            if next_line:
                break
            cur = self.cur()
            if kind is str and res in self.inner and cur not in self.valid_variable_chars:
                # 检测是否是关键字，true和false也归属这里
                break
            if kind is str and cur not in self.valid_variable_chars:
                # 检测非关键字，以字母开头的一个完整标识符
                break
            if kind is int and cur not in set('0123456789eE._'):
                # 检测是否是整型或浮点型
                break
            if kind is bool and cur not in self.valid_variable_chars:
                # 检测以下划线开头的一个完整标识符
                break
            if res in self.inner and res + cur not in self.inner:
                # 检测内置运算符，内置运算符之间必须没有空格，如== **
                break
        if res in self.inner:
            return Token(res, res)
        if self.is_id(res):
            return Token('id', res)
        if self.is_int(res):
            return Token('int', res)
        if self.is_float(res):
            return Token('float', res)

    def tokenize(self):
        """
        供外界调用的函数，返回当前解析代码文件的完整token列表
        :return: token 列表
        """
        res = [self.get_one_token()]
        if res[-1] is None:
            res.pop()
        while self.index < self.length:
            res.append(self.get_one_token())
            if res[-1] is None:
                res.pop()
        return res

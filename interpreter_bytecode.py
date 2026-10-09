from compiler import code, calc


class Interpreter_bytecode:
    def __init__(self, bytecodes):
        self.bytecodes = bytecodes
        self.stack = []
        self.env = {}
        self.pc = 0
        self.size = len(bytecodes)
        self.op_calc = [
            None,
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
        ]

    def do(self):
        while self.pc < self.size:
            cur = self.bytecodes[self.pc]
            self.pc += 1
            op = cur[0]
            if op is code.push:
                self.stack.append(cur[1])
            elif op is code.pop:
                self.stack.pop()
            elif op is code.write:
                right = self.stack.pop()
                left = self.stack.pop()
                self.env[left] = right
                self.stack.append(right)
            elif op is code.read:
                head = self.stack.pop()
                self.stack.append(self.env[head])
            elif op is code.write_index:
                value, index, arr = self.stack.pop(), self.stack.pop(), self.stack.pop()
                arr[index] = value
                self.stack.append(value)
            elif op is code.read_index:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left[right])
            elif op is code.get_list:
                size = cur[1]
                arr = self.stack[-size:]
                self.stack = self.stack[:-size]
                self.stack.append(list(reversed(arr)))
            elif op is code.get_dict:
                size = cur[1]
                arr = {}
                for i in range(size):
                    right = self.stack.pop()
                    left = self.stack.pop()
                    arr[left] = right
                self.stack.append(dict(reversed(list(arr.items()))))
            elif op is code.jump_if_false:
                if not self.stack.pop():
                    self.pc = cur[1]
            elif op is code.jump_if_true:
                if self.stack.pop():
                    self.pc = cur[1]
            elif op is code.jump:
                self.pc = cur[1]
            elif calc.add <= op <= calc.bitwise_or:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(self.op_calc[op](left, right))

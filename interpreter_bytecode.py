from compiler import code


class Interpreter_bytecode:
    def __init__(self, bytecodes):
        self.bytecodes = bytecodes
        self.stack = []
        self.env = {}
        self.pc = 0
        self.size = len(bytecodes)

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
                left = cur[1]
                self.env[left] = right
                self.stack.append(right)
            elif op is code.read:
                head = cur[1]
                self.stack.append(self.env[head])
            elif op is code.add:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left + right)
            elif op is code.sub:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left - right)
            elif op is code.mul:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left * right)
            elif op is code.div_int:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left // right)
            elif op is code.div_float:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left / right)
            elif op is code.jump_if_false:
                if not self.stack.pop():
                    self.pc = cur[1]
            elif op is code.jump:
                self.pc = cur[1]
            elif op is code.lt:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left < right)
            elif op is code.gt:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left > right)
            elif op is code.le:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left <= right)
            elif op is code.ge:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left >= right)
            elif op is code.eq:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left == right)
            elif op is code.ne:
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left != right)

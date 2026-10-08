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
            op = cur[0]
            if op is code.push:
                self.pc += 1
                self.stack.append(cur[1])
            elif op is code.pop:
                self.pc += 1
                self.stack.pop()
            elif op is code.write:
                self.pc += 1
                right = self.stack.pop()
                left = cur[1]
                self.env[left] = right
                self.stack.append(right)
            elif op is code.read:
                self.pc += 1
                head = cur[1]
                self.stack.append(self.env[head])
            elif op is code.add:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left + right)
            elif op is code.sub:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left - right)
            elif op is code.mul:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left * right)
            elif op is code.div_int:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left // right)
            elif op is code.div_float:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left / right)
            elif op is code.jump_if_false:
                if not self.stack.pop():
                    self.pc = cur[1]
                else:
                    self.pc += 1
            elif op is code.jump:
                self.pc = cur[1]
            elif op is code.lt:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left < right)
            elif op is code.gt:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left > right)
            elif op is code.le:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left <= right)
            elif op is code.ge:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left >= right)
            elif op is code.eq:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left == right)
            elif op is code.ne:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left != right)

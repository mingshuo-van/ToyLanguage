from compiler import code
class Interpreter_bytecode:
    def __init__(self,bytecodes):
        self.bytecodes = bytecodes
        self.stack = []
        self.env = {}
        self.pc = 0
        self. size = len(bytecodes)

    def do(self):
        while self.pc < self.size:
            cur = self.bytecodes[self.pc]
            if cur[0] is code.push:
                self.pc += 1
                self.stack.append(cur[1])
            elif cur[0] is code.pop:
                self.pc += 1
                self.stack.pop()
            elif cur[0] is code.write:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.env[left] = right
                self.stack.append(right)
            elif cur[0] is code.read:
                self.pc += 1
                head = self.stack.pop()
                self.stack.append(self.env[head])
            elif cur[0] is code.add:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left + right)
            elif cur[0] is code.sub:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left - right)
            elif cur[0] is code.mul:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left * right)
            elif cur[0] is code.div_int:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left // right)
            elif cur[0] is code.div_float:
                self.pc += 1
                right = self.stack.pop()
                left = self.stack.pop()
                self.stack.append(left / right)




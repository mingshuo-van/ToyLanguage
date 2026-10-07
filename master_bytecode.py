from Tokenizer import Tokenizer
from Parser import Parser
from Optimizer import Optimizer
from compiler import Compiler
from interpreter_bytecode import Interpreter_bytecode

file = 'test/test.py'
with open(file,'r') as f:
    for line in f:
        print(line,end='')
t = Tokenizer(file)
p = Parser(t.tokenize())
o = Optimizer(p.stmt_list())
# o.optimize()
print(o.ast)
c = Compiler(o.ast)
c.do()
for i in c.bytecodes:
    print(i)

i = Interpreter_bytecode(c.bytecodes)
i.do()
print(i.env)
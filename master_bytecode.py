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
o.optimize()
for idx,i in enumerate(o.ast):
    print(f'{idx}------{i}')
c = Compiler(o.ast)
c.do()
for idx,i in enumerate(c.bytecodes):
    print(f'{idx}------{i}')

i = Interpreter_bytecode(c.bytecodes,c.hash_map,c.unhash_map)
i.do()
print(f'env:\n{i.env}')
print(f'stack:\n{i.stack}')
print(f'hash_map:\n{i.hash_map}')
print(f'unhash_map:\n{i.unhash_map}')
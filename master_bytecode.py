from Tokenizer import Tokenizer
from Parser import Parser
from Optimizer import Optimizer
from compiler import Compiler
from interpreter_bytecode import Interpreter_bytecode

file = 'test/test.py'
with open(file, 'r') as f:
    for line in f:
        print(line, end='')
t = Tokenizer(file)
p = Parser(t.tokenize())
o = Optimizer(p.stmt_list())
o.optimize()
for idx, i in enumerate(o.ast):
    print(f'{idx}------{i}')
c = Compiler(o.ast)
c.do()
for idx, i in enumerate(c.bytecodes):
    print(f'{idx}------{i}')

i = Interpreter_bytecode(c.bytecodes, c.varname, c.consts, c.func_scope)
i.do()
print(f'env:\n{i.env}')
print(f'stack_data:\n{i.stack_data}')
print(f'stack_frame:\n{i.stack_frame}')
print(f'varname:\n{i.varname}')
print(f'consts:\n{i.consts}')
print(f'func_scope:\n{i.func_scope}')

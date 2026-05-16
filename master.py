import sys
import os
import pickle
from Tokenizer import Tokenizer
from Parser import Parser
from Optimizer import Optimizer
from VirtualMachine import VirtualMachine

t = Tokenizer('')
p = Parser([])
o = Optimizer([])
v = VirtualMachine([])
while True:
    line = input().strip()
    if line == 'exit':
        sys.exit()
    ast = False
    run = False
    if line.startswith('ast'):
        ast = True
    elif line.startswith('run'):
        run = True
    else:
        continue
    address = ''
    index = 3
    size = len(line)
    while index < size and line[index] == ' ':
        index += 1
    if index < size and line[index] == '\"' or line[index] == '\'':
        op = line[index]
        index += 1
        while index < size and line[index] != op:
            address += line[index]
            index += 1
    elif index < size:
        while index < size and line[index] != ' ':
            address += line[index]
            index += 1
    if ast:
        t.reset_address(address)
        p.reset_tokens(t.tokenize())
        o.ast = p.program()
        o.optimize()
        parent = os.path.dirname(address)
        name = os.path.splitext(os.path.basename(address))[0]
        with open(parent + '/' + name + '.ast', 'wb') as f:
            pickle.dump(o.ast, f)
            print(f'ast finish the file {address}')
    elif run:
        with open(address, 'rb') as f:
            v.ast = pickle.load(f)
        v.vm()

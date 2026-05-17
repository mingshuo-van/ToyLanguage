import sys
import os
import pickle
from Tokenizer import Tokenizer
from Parser import Parser
from Optimizer import Optimizer
from VirtualMachine import VirtualMachine


def get_ast(address):
    t.reset_address(address)
    p.reset_tokens(t.tokenize())
    o.ast = p.program()
    o.optimize()
    parent = os.path.dirname(address)
    name = os.path.splitext(os.path.basename(address))[0]
    try:
        with open(parent + '/' + name + '.ast', 'wb') as f:
            pickle.dump(o.ast, f)
            print(f'ast finish the file {address}')
            return o.ast
    except FileNotFoundError:
        print(f'{address} 不存在')
        return None


def run_ast(address):
    try:
        if isinstance(address, str):
            with open(address, 'rb') as f:
                v.ast = pickle.load(f)
        else:
            v.ast = address
    except FileNotFoundError:
        print(f'{address} 不存在')
    v.vm()


address = ''
if len(sys.argv) > 1:
    address = sys.argv[1:]

t = Tokenizer('')
p = Parser([])
o = Optimizer([])
v = VirtualMachine([])
if address:
    for i in address:
        if os.path.splitext(i)[1] == '.ast':
            run_ast(i)
        else:
            res = get_ast(i)
            if res:
                run_ast(res)

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
        get_ast(address)
    elif run:
        if os.path.splitext(address)[1] == '.ast':
            run_ast(address)
        else:
            res = get_ast(address)
            if res:
                run_ast(res)

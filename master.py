import sys
import os
import pickle

import Object
from Tokenizer import Tokenizer
from Parser import Parser
from Optimizer import Optimizer
from Interpreter import Interpreter


def get_ast(address):
    t.reset_address(address)
    p.reset_tokens(t.tokenize())
    o.ast = p.program()
    o.optimize()
    parent = os.path.dirname(address)
    name = os.path.splitext(os.path.basename(address))[0]
    with open(parent + '/' + name + '.ast', 'wb') as f:
        pickle.dump(o.ast, f)
        print(f'ast finish the file {address}')
        return o.ast


def run_ast(address):
    if isinstance(address, str):
        with open(address, 'rb') as f:
            v.ast = pickle.load(f)
    else:
        v.ast = address
    v.vm()


address = ''
if len(sys.argv) > 1:
    address = sys.argv[1:]

t = Tokenizer('')
p = Parser([])
o = Optimizer([])
v = Interpreter([])
if address:
    for i in address:
        if os.path.splitext(i)[1] == '.ast':
            run_ast(i)
        else:
            res = get_ast(i)
            if res:
                run_ast(res)


def main():
    while True:
        address = ''
        try:
            line = input().strip()
            if line == 'exit':
                sys.exit()
            ast = False
            run = False
            if line.startswith('ast'):
                ast = True
            elif line.startswith('run'):
                run = True
            elif line.startswith('help'):
                print('输入 ast [address] 可以生成address对应代码的.ast文件,若已有则会覆盖'
                      '\n输入 run [address] 可以运行address对应的.ast文件，若非'
                      '对应.ast文件则把address对应文件作为代码先生成.ast文件然后运行\n'
                      'ast 时的address结尾可以为任意后缀(不可无后缀，具体文件须真实存在)\n'
                      'run 时的address结尾可以为任意后缀(不可无后缀，具体文件须真实存在)')
                continue
            else:
                print('\033[31m 无此指令，可输入help获取帮助\033[0m')
                continue
            index = 3
            size = len(line)
            while index < size and line[index] == ' ':
                index += 1
            if index < size and (line[index] == '\"' or line[index] == '\''):
                op = line[index]
                index += 1
                while index < size and line[index] != op:
                    address += line[index]
                    index += 1
            elif index < size:
                while index < size and line[index] != ' ':
                    address += line[index]
                    index += 1
            address = address.strip()
            if not address:
                print('\033[31m address is empty!\033[0m')
            else:
                if ast:
                    get_ast(address)
                elif run:
                    if os.path.splitext(address)[1] == '.ast':
                        run_ast(address)
                    else:
                        res = get_ast(address)
                        if res:
                            run_ast(res)
        except Object.Lang_Err as e:
            print(f'\033[31m An error occurred! The code program were interrupted! {e.args[0]} : {e.args[1]}\033[0m')
        except FileNotFoundError:
            print(f'\033[31m address is not exists {address}\033[0m')
        except Exception:
            import traceback
            print(f'\033[31m unexpected internal error\n {traceback.format_exc()}\033[0m')
            del traceback


if __name__ == '__main__':
    main()

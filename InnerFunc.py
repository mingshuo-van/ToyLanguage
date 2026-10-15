from Object import *

def get_inner_object(node):
    """
    获得 Inner 包装
    :param node: element
    :return: Inner
    """
    if node is None:
        return InnerNull
    t = type(node)
    if t is int:
        f = InnerInt
    elif t is float:
        f = InnerFloat
    elif t is str:
        f = InnerStr
    elif t is bool:
        f = InnerBool
    else:
        f = None
    return f(node) if f is not None else node

def get_origin_object(node):
    """
    辅助拆箱 cell 和 inner
    在 read 或 具备 read 语义的情况下用于获得内置元素
    但不会直接用于 write 的 左值
    取决于具体的功能
    :param node: 要处理的元素
    :return: node | Cell.val
    """
    node = node.val if type(node) is Cell else node
    if isinstance(node, Inner):
        return node.val
    elif node is InnerNull:
        return None
    return node


def get_func(var_list):
    return Func(None, var_list,
                FuncMessage(inner_flag, {index: i for index, i in enumerate(var_list)}, {}, {}),
                None)


def inner_print(line, end='\n'):
    print(str(line), end=end)


from time import time


def inner_time():
    return time()


def inner_get(alter=''):
    return input(alter)


def inner_int(element):
    try:
        return int(get_origin_object(element))
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_float(element):
    try:
        return float(get_origin_object(element))
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_str(element):
    try:
        return str(get_origin_object(element))
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_bool(element):
    try:
        return bool(get_origin_object(element))
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_list(element=None):
    res = InnerList()
    if element is None:
        return res
    t = type(element)
    if t is InnerList:
        for i in element:
            res.append(i)
    elif t is InnerDict:
        for i in element.keys():
            res.append(i)
    else:
        raise Lang_Err('TypeError', f'{t} is not iterable')
    return res


def inner_dict(element=None):
    res = InnerDict()
    if element is None:
        return res
    t = type(element)
    if t is InnerList:
        l = len(element)
        if l & 1:
            raise Lang_Err('ValueError', 'dictionary update sequence element')
        for i in range(0, len(element), 2):
            res[element[i]] = element[i + 1]
    elif t is InnerDict:
        for k, v in element.items():
            res[k] = v
    else:
        raise Lang_Err('TypeError', f'{t} is not iterable')
    return res


def inner_push(box, idx):
    try:
        return box.append(get_inner_object(idx))
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_pop(box, key):
    try:
        return box.pop(key)
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_has(box, key):
    try:
        return key in box
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


def inner_len(box):
    try:
        return len(box)
    except Exception as e:
        raise Lang_Err(e.__class__.__name__, str(e))


builtins_func = {
    'print': get_func(['line', 'end']),
    'time': get_func([]),
    'get': get_func(['alter']),
    'int': get_func(['element']),
    'float': get_func(['element']),
    'str': get_func(['element']),
    'bool': get_func(['element']),
    'list': get_func([]),
    'dict': get_func([]),
    'push': get_func(['box', 'idx']),
    'pop': get_func(['box', 'key']),
    'has': get_func(['box', 'key']),
    'len': get_func(['box'])
}

builtins_map = {
    'print': inner_print,
    'time': inner_time,
    'get': inner_get,
    'int': inner_int,
    'float': inner_float,
    'str': inner_str,
    'bool': inner_bool,
    'list': inner_list,
    'dict': inner_dict,
    'push': inner_push,
    'pop': inner_pop,
    'has': inner_has,
    'len': inner_len
}

"""
'vars': Func([], [], None),
'join': Func([Id('box'), Id('s')], [], None),
'split': Func([Id('target'), Id('cut'), Id('count')], [], None),
'strip': Func([Id('s')], [], None),
'lstrip': Func([Id('s')], [], None),
'rstrip': Func([Id('s')], [], None),
'find': Func([Id('target'), Id('sub'), Id('start'), Id('end')], [], None),
'count': Func([Id('target'), Id('sub'), Id('start'), Id('end')], [], None),
'replace': Func([Id('target'), Id('old'), Id('new'), Id('count')], [], None),
'seed': Func([Id('instance')], [], None),
'random': Func([], [], None),
'randrange': Func([Id('start'), Id('end'), Id('step')], [], None),
'open': Func([Id('address'), Id('mode'), Id('coding')], [], None),
'read': Func([Id('file_handle')], [], None),
'write': Func([Id('file_handle'), Id('word')], [], None),
'close': Func([Id('file_handle')], [], None),
'exit': Func([Id('num')], [], None),
'err_name': Func([Id('err')], [], None),
'err_des': Func([Id('err')], [], None),
'clear': Func([], [], None)
"""

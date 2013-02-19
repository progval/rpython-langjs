from rpython.rlib.rfloat import NAN
from rpython.rlib.rstring import UnicodeBuilder

from js.jsobj import W_String, W_StringObject
from js.exception import JsTypeError
from js.builtins import get_arg
from js.object_space import w_return, _w


def setup(global_object):
    from js.builtins import put_native_function, put_property
    from js.object_space import object_space

    #String
    # 15.5.1
    from js.jsobj import W_StringConstructor
    w_String = W_StringConstructor()
    object_space.assign_proto(w_String, object_space.proto_function)
    put_property(w_String, u'length', _w(1), writable=False, enumerable=False, configurable=False)
    put_property(global_object, u'String', w_String)

    # 15.5.4
    w_StringPrototype = W_StringObject(_w(u''))
    object_space.assign_proto(w_StringPrototype, object_space.proto_object)

    # 15.5.3.1
    object_space.proto_string = w_StringPrototype

    put_property(w_String, u'prototype', w_StringPrototype, writable=False, enumerable=False, configurable=False)

    # 15.5.3.2
    put_native_function(w_String, u'fromCharCode', from_char_code, params=[u'char1'])

    # 15.5.4.1
    put_property(w_StringPrototype, u'constructor', w_String)

    # 15.5.4.2
    put_native_function(w_StringPrototype, u'toString', to_string)

    # 15.5.4.3
    put_native_function(w_StringPrototype, u'valueOf', value_of)

    # 15.5.4.4
    put_native_function(w_StringPrototype, u'charAt', char_at, params=[u'pos'])

    # 15.5.4.5
    put_native_function(w_StringPrototype, u'charCodeAt', char_code_at, params=[u'pos'])

    # 15.5.4.6
    put_native_function(w_StringPrototype, u'concat', concat, params=[u'string1'])

    # 15.5.4.7
    put_native_function(w_StringPrototype, u'indexOf', index_of, params=[u'searchstring'])

    # 15.5.4.8
    put_native_function(w_StringPrototype, u'lastIndexOf', last_index_of, params=[u'searchstring'])

    # 15.5.4.14
    put_native_function(w_StringPrototype, u'split', split, params=[u'separator', u'limit'])

    # 15.5.4.15
    put_native_function(w_StringPrototype, u'substring', substring, params=[u'start', u'end'])

    # 15.5.4.16
    put_native_function(w_StringPrototype, u'toLowerCase', to_lower_case)

    # 15.5.4.18
    put_native_function(w_StringPrototype, u'toUpperCase', to_upper_case)


# 15.5.3.2
@w_return
def from_char_code(this, args):
    builder = UnicodeBuilder(len(args))

    for arg in args:
        i = arg.ToInt16()
        c = unichr(i)
        builder.append(c)

    s = builder.build()
    return s


# 15.5.4.2
@w_return
def to_string(this, args):
    if isinstance(this, W_String):
        s = this
    elif isinstance(this, W_StringObject):
        s = this.PrimitiveValue()
    else:
        raise JsTypeError(u'')

    return s.to_string()


# 15.5.4.3
@w_return
def value_of(this, args):
    if isinstance(this, W_String):
        s = this
    elif isinstance(this, W_StringObject):
        s = this.PrimitiveValue()
    else:
        raise JsTypeError(u'')

    assert isinstance(s, W_String)
    return s


# 15.5.4.4
@w_return
def char_at(this, args):
    pos = get_arg(args, 0)

    position = pos.ToInt32()

    this.check_object_coercible()
    string = this.to_string()

    size = len(string)
    if position < 0 or position >= size:
        return u''

    return string[position]


#15.5.4.5
@w_return
def char_code_at(this, args):
    pos = get_arg(args, 0)

    this.check_object_coercible()
    string = this.to_string()
    position = pos.ToInt32()
    size = len(string)

    if position < 0 or position >= size:
        return NAN

    char = string[position]
    return ord(char)


#15.5.4.6
@w_return
def concat(this, args):
    string = this.to_string()
    others = [obj.to_string() for obj in args]
    string += u''.join(others)
    return string


# 15.5.4.7
@w_return
def index_of(this, args):
    string = this.to_string()
    if len(args) < 1:
        return -1

    substr = args[0].to_string()
    size = len(string)
    if len(args) < 2:
        pos = 0
    else:
        pos = args[1].ToInteger()

    pos = int(min(max(pos, 0), size))

    assert pos >= 0
    return string.find(substr, pos)


# 15.5.4.8
@w_return
def last_index_of(this, args):
    search_string = get_arg(args, 0)
    position = get_arg(args, 1)

    s = this.to_string()
    search_str = search_string.to_string()
    num_pos = position.ToNumber()

    from rpython.rlib.rfloat import INFINITY, isnan, isinf

    if isnan(num_pos):
        pos = INFINITY
    elif isinf(num_pos):
        pos = num_pos
    else:
        pos = int(num_pos)

    length = len(s)
    start = min(max(pos, 0), length)
    search_len = len(search_str)

    if isinf(start):
        idx = s.rfind(search_str)
        return idx

    end = int(start + search_len)
    assert end >= 0
    idx = s.rfind(search_str, 0, end)
    return idx


# pypy/rlib/rstring
def _rsplit(value, by, maxsplit=-1):
    bylen = len(by)
    if bylen == 0:
        raise ValueError("empty separator")

    res = []
    start = 0
    while maxsplit != 0:
        next = value.find(by, start)
        if next < 0:
            break
        res.append(value[start:next])
        start = next + bylen
        maxsplit -= 1   # NB. if it's already < 0, it stays < 0

    res.append(value[start:len(value)])
    return res


# 15.5.4.14
@w_return
def split(this, args):
    from js.object_space import isundefined

    this.check_object_coercible()

    separator = get_arg(args, 0, None)
    limit = get_arg(args, 1)

    string = this.to_string()

    if isundefined(limit):
        import math
        lim = int(math.pow(2, 32) - 1)
    else:
        lim = limit.ToUInt32()

    if lim == 0 or separator is None:
        return [string]

    r = separator.to_string()

    if r == u'':
        i = 0
        splitted = []
        while i < len(string):
            splitted += [string[i]]
            i += 1
        return splitted
    else:
        splitted = _rsplit(string, r, lim)
        return splitted


# 15.5.4.15
@w_return
def substring(this, args):
    string = this.to_string()
    size = len(string)

    if len(args) < 1:
        start = 0
    else:
        start = args[0].ToInteger()

    if len(args) < 2:
        end = size
    else:
        end = args[1].ToInteger()

    tmp1 = min(max(start, 0), size)
    tmp2 = min(max(end, 0), size)
    start = min(tmp1, tmp2)
    end = max(tmp1, tmp2)
    start = int(start)
    end = int(end)

    assert start >= 0
    assert end >= 0
    return string[start:end]


# 15.5.4.16
@w_return
def to_lower_case(this, args):
    from rpython.rlib.unicodedata import unicodedb

    string = this.to_string()
    builder = UnicodeBuilder(len(string))

    for char in string:
        builder.append(unichr(unicodedb.tolower(ord(char))))

    return builder.build()


# 15.5.4.18
@w_return
def to_upper_case(this, args):
    from rpython.rlib.unicodedata import unicodedb

    string = this.to_string()
    builder = UnicodeBuilder(len(string))

    for char in string:
        builder.append(unichr(unicodedb.toupper(ord(char))))

    return builder.build()

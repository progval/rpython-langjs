from js.jsobj import _w, w_Undefined, W_String, W_StringObject
from pypy.rlib.rfloat import NAN, INFINITY, isnan
from js.execution import ThrowException, JsTypeError
from js.builtins import get_arg

def setup(global_object):
    from js.builtins import put_native_function, put_property

    #String
    # 15.5.1
    from js.jsobj import W_StringConstructor
    w_String = W_StringConstructor()
    #put_property(w_String, '__proto__', w_String._prototype_, writable = False, enumerable = False, configurable = False)
    put_property(w_String, 'length', _w(1), writable = False, enumerable = False, configurable = False)

    put_property(global_object, 'String', w_String)


    # 15.5.4
    from js.jsobj import W_StringObject, W__Object
    w_StringPrototype = W_StringObject('')
    w_StringPrototype._prototype_ = W__Object._prototype_

    # 15.5.3.1
    W_StringObject._prototype_ = w_StringPrototype
    put_property(w_String, 'prototype', w_StringPrototype, writable = False, enumerable = False, configurable = False)

    # 15.5.3.2
    put_native_function(w_String, 'fromCharCode', from_char_code, params = ['char1'])

    # 15.5.4.1
    put_property(w_StringPrototype, 'constructor', w_String)

    # 15.5.4.2
    put_native_function(w_StringPrototype, 'toString', to_string)

    # 15.5.4.3
    put_native_function(w_StringPrototype, 'valueOf', value_of)

    # 15.5.4.4
    put_native_function(w_StringPrototype, 'charAt', char_at, params = ['pos'])

    # 15.5.4.5
    put_native_function(w_StringPrototype, 'charCodeAt', char_code_at, params = ['pos'])

    # 15.5.4.6
    put_native_function(w_StringPrototype, 'concat', concat, params = ['string1'])

    # 15.5.4.7
    put_native_function(w_StringPrototype, 'indexOf', index_of, params = ['searchstring'])

    # 15.5.4.8
    put_native_function(w_StringPrototype, 'lastIndexOf', last_index_of, params = ['searchstring'])

    # 15.5.4.14
    put_native_function(w_StringPrototype, 'split', split, params = ['separator', 'limit'])

    # 15.5.4.15
    put_native_function(w_StringPrototype, 'substring', substring, params = ['start', 'end'])

    # 15.5.4.16
    put_native_function(w_StringPrototype, 'toLowerCase', to_lower_case)

    # 15.5.4.18
    put_native_function(w_StringPrototype, 'toUpperCase', to_upper_case)

# 15.5.3.2
def from_char_code(this, args):
    temp = []
    for arg in args:
        i = arg.ToInt16()
        temp.append(unichr(i))
    return u''.join(temp)

# 15.5.4.2
def to_string(this, args):
    if isinstance(this, W_String):
        s = this
    elif isinstance(this, W_StringObject):
        s = this.PrimitiveValue()
    else:
        raise JsTypeError()

    assert isinstance(s, W_String)
    return s.to_string()

# 15.5.4.3
def value_of(this, args):
    if isinstance(this, W_String):
        s = this
    elif isinstance(this, W_StringObject):
        s = this.PrimitiveValue()
    else:
        raise JsTypeError()

    assert isinstance(s, W_String)
    return s

# 15.5.4.4
def char_at(this, args):
    pos = w_Undefined

    if len(args) > 0:
        pos = args[0]

    position = pos.ToInt32()

    this.check_object_coercible()
    string = this.to_string()

    size = len(string)
    if position < 0 or position >= size:
        return u''

    return string[position]

#15.5.4.5
def char_code_at(this, args):
    pos = w_Undefined

    if len(args) > 0:
        pos = args[0]

    this.check_object_coercible()
    string = this.to_string()
    position = pos.ToInt32()
    size = len(string)

    if position < 0 or position >= size:
        return NAN

    char = string[position]
    return ord(char)

#15.5.4.6
def concat(this, args):
    string = this.to_string()
    others = [obj.to_string() for obj in args]
    string += u''.join(others)
    return string

# 15.5.4.7
def index_of(this, args):
    string = this.to_string()
    if len(args) < 1:
        return -1
    substr = args[0].to_string()
    size = len(string)
    subsize = len(substr)
    if len(args) < 2:
        pos = 0
    else:
        pos = args[1].ToInteger()
    pos = int(min(max(pos, 0), size))
    assert pos >= 0
    return string.find(substr, pos)

# 15.5.4.8
def last_index_of(this, args):
    search_string = get_arg(args,0)
    position = get_arg(args, 1)

    s = this.to_string()
    search_str = search_string.to_string()
    num_pos = position.ToNumber()

    from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf

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
        return s.rfind(search_str)

    return s.rfind(search_str, 0, start + search_len)

# 15.5.4.14
def split(this, args):
    from js.jsobj import W__Array, w_Null
    from js.jsobj import put_property

    this.check_object_coercible()

    separator = get_arg(args, 0, None)
    limit = get_arg(args, 1)

    string = this.to_string()

    if limit is w_Undefined:
        import math
        lim = int(math.pow(2,32) - 1)
    else:
        lim = limit.ToUInt32()

    if lim == 0 or separator is None:
        return [string]

    r = separator.to_string()

    if r == '':
        return list(string)
    else:
        splitted = string.split(r, lim)
        return splitted

    return a

# 15.5.4.15
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
    return string[start:end]

# 15.5.4.16
def to_lower_case(this, args):
    string = this.to_string()
    return string.lower()

# 15.5.4.18
def to_upper_case(this, args):
    string = this.to_string()
    return string.upper()


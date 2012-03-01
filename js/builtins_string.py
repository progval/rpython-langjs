from js.jsobj import _w, w_Undefined, W_String
from pypy.rlib.rfloat import NAN, INFINITY, isnan
from js.execution import ThrowException

# 15.5.3.2
def from_char_code(this, args):
    temp = []
    for arg in args:
        i = arg.ToInt32() % 65536 # XXX should be uint16
        temp.append(chr(i))
    return ''.join(temp)

# 15.5.4.4
def char_at(this, args):
    string = this.ToString()
    if len(args)>=1:
        pos = args[0].ToInt32()
        if (not pos >=0) or (pos > len(string) - 1):
            return ''
    else:
        return ''
    return string[pos]

#15.5.4.5
def char_code_at(this, args):
    string = this.ToString()
    if len(args)>=1:
        pos = args[0].ToInt32()
        if pos < 0 or pos > len(string) - 1:
            return NAN
    else:
        return NAN
    char = string[pos]
    return ord(char)

#15.5.4.6
def concat(this, args):
    string = this.ToString()
    others = [obj.ToString() for obj in args]
    string += ''.join(others)
    return string

# 15.5.4.7
def index_of(this, args):
    string = this.ToString()
    if len(args) < 1:
        return -1
    substr = args[0].ToString()
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
    string = this.ToString()
    if len(args) < 1:
        return -1
    substr = args[0].ToString()
    if len(args) < 2:
        pos = INFINITY
    else:
        val = args[1].ToNumber()
        if isnan(val):
            pos = INFINITY
        else:
            pos = args[1].ToInteger()
    size = len(string)
    pos = int(min(max(pos, 0), size))
    subsize = len(substr)
    endpos = pos+subsize
    assert endpos >= 0
    return string.rfind(substr, 0, endpos)

# 15.5.4.14
def split(this, args):
    string = this.ToString()

    if len(args) < 1 or args[0] is w_Undefined:
        return _create_array([_w(string)])
    else:
        separator = args[0].ToString()

    if len(args) >= 2:
        limit = args[1].ToUInt32()
        raise ThrowException(W_String("limit not implemented"))
        # array = string.split(separator, limit)
    else:
        array = string.split(separator)

    w_array = _create_array()
    i = 0
    while i < len(array):
        w_str = W_String(array[i])
        w_array.Put(str(i), w_str)
        i += 1

    return w_array

# 15.5.4.15
def substring(this, args):
    string = this.ToString()
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
    return string[start:end]

# 15.5.4.16
def to_lower_case(this, args):
    string = this.ToString()
    return string.lower()

# 15.5.4.18
def to_upper_case(this, args):
    string = this.ToString()
    return string.upper()

def _create_array(elements=[]):
    from js.jsobj import W__Array
    array = W__Array()
    i = 0
    while i < len(elements):
        array.Put(str(i), elements[i])
        i += 1

    return array


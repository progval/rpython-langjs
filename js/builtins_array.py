from js.jsobj import isnull_or_undefined, _w, w_Undefined
from js.builtins import get_arg
from js.object_space import w_return

def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.jsobj import W_ArrayConstructor, W__Array, W__Object
    from js.object_space import object_space

    w_Array = W_ArrayConstructor()
    object_space.assign_proto(w_Array, object_space.proto_function)
    put_property(global_object, u'Array', w_Array)

    # 15.4.4
    w_ArrayPrototype = W__Array()
    object_space.assign_proto(w_ArrayPrototype, object_space.proto_object)
    object_space.proto_array = w_ArrayPrototype

    # 15.4.3.1
    put_property(w_Array, u'prototype', w_ArrayPrototype, writable = False, enumerable = False, configurable = False)

    # 15.4.4.1
    put_property(w_ArrayPrototype, u'constructor', w_Array)

    # 15.4.4.2
    put_native_function(w_ArrayPrototype, u'toString', to_string)

    # 15.4.4.5
    put_native_function(w_ArrayPrototype, u'join', join, params = [u'separator'])

    # 15.4.4.6
    put_native_function(w_ArrayPrototype, u'pop', pop)

    # 15.4.4.7
    put_native_function(w_ArrayPrototype, u'push', push)

    # 15.4.4.8
    put_native_function(w_ArrayPrototype, u'reverse', reverse)

    # 15.4.4.11
    put_native_function(w_ArrayPrototype, u'sort', sort)

# 15.4.4.7
@w_return
def push(this, args):
    o = this.ToObject()
    len_val = o.get(u'length')
    n = len_val.ToUInt32()

    for item in args:
        e = item
        o.put(unicode(str(n)), e, True)
        n = n + 1

    o.put(u'length', _w(n), True)

    return n

# 15.4.4.2
@w_return
def to_string(this, args):
    array = this.ToObject()
    func = array.get(u'join')
    if func.is_callable():
        return func.Call(this = this).to_string()
    else:
        return this.to_string()

# 15.4.4.5
@w_return
def join(this, args):
    separator = get_arg(args, 0)

    o = this.ToObject()
    len_val = o.get(u'length')
    length = len_val.ToUInt32()

    if separator is w_Undefined:
        sep = u','
    else:
        sep = separator.to_string()

    if length == 0:
        return u''

    element0 = o.get(u'0')
    if isnull_or_undefined(element0):
        r = u''
    else:
        r = element0.to_string()

    k = 1

    while(k < length):
        s = r + sep
        element = o.get(unicode(str(k)))
        if isnull_or_undefined(element):
            _next = u''
        else:
            _next = element.to_string()
        r = s + _next
        k += 1

    return r

# 15.4.4.6
@w_return
def pop(this, args):
    o = this.ToObject()
    lenVal = o.get(u'length')
    l = lenVal.ToUInt32()

    if l == 0:
        o.put(u'length', _w(0))
        return w_Undefined
    else:
        indx = l - 1
        indxs = unicode(str(indx))
        element = o.get(indxs)
        o.delete(indxs, True)
        o.put(u'length', _w(indx))
        return element

# 15.4.4.8
@w_return
def reverse(this, args):
    o = this.ToObject()
    length = o.get(u'length').ToUInt32()

    import math
    middle = math.floor(length/2)

    lower = 0
    while lower != middle:
        upper = length - lower - 1
        lower_p = unicode(str(lower))
        upper_p = unicode(str(upper))
        lower_value = o.get(lower_p)
        upper_value = o.get(upper_p)
        lower_exists = o.has_property(lower_p)
        upper_exists = o.has_property(upper_p)

        if lower_exists is True and upper_exists is True:
            o.put(lower_p, upper_value)
            o.put(upper_p, lower_value)
        elif lower_exists is False and upper_exists is True:
            o.put(lower_p, upper_value)
            o.delete(upper_p)
        elif lower_exists is True and upper_exists is False:
            o.delete(lower_p)
            o.put(upper_p, lower_value)

        lower = lower + 1

# 15.4.4.11
@w_return
def sort(this, args):
    obj = this
    length = this.get(u'length').ToUInt32()

    comparefn = get_arg(args, 0)

    # TODO check if implementation defined

    # sorts need to be in-place, lets do some very non-fancy bubble sort for starters
    while True:
        swapped = False
        for i in xrange(1, length):
            x = unicode(str(i - 1))
            y = unicode(str(i))
            comp = sort_compare(obj, x, y, comparefn)
            if  comp == 1:
                tmp_x = obj.get(x)
                tmp_y = obj.get(y)
                obj.put(x, tmp_y)
                obj.put(y, tmp_x)
                swapped = True
        if not swapped:
            break

    return obj

def sort_compare(obj, j, k, comparefn = w_Undefined):
    j_string = j
    k_string = k
    has_j = obj.has_property(j)
    has_k = obj.has_property(k)

    if has_j is False and has_k is False:
        return 0
    if has_j is False:
        return 1
    if has_k is False:
        return -1

    x = obj.get(j_string)
    y = obj.get(k_string)

    if x is w_Undefined and y is w_Undefined:
        return 0
    if x is w_Undefined:
        return 1
    if y is w_Undefined:
        return -1

    if comparefn is not w_Undefined:
        if not comparefn.is_callable():
            from js.execution import JsTypeError
            raise JsTypeError(u'')

        res = comparefn.Call(args = [x, y], this = w_Undefined)
        return res.ToInteger()

    x_string = x.to_string()
    y_string = y.to_string()
    if x_string < y_string:
        return -1
    if x_string > y_string:
        return 1
    return 0


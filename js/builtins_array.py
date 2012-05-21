from js.jsobj import isnull_or_undefined, _w, w_Undefined
from js.builtins import get_arg

def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.jsobj import W_ArrayConstructor, W__Array, W__Object
    w_Array = W_ArrayConstructor()
    put_property(global_object, 'Array', w_Array)

    # 15.4.4
    w_ArrayPrototype = W__Array()

    w_ArrayPrototype._prototype_ = W__Object._prototype_

    # 15.4.3.1
    W__Array._prototype_ = w_ArrayPrototype
    put_property(w_Array, 'prototype', w_ArrayPrototype, writable = False, enumerable = False, configurable = False)

    # 15.4.4.1
    put_property(w_ArrayPrototype, 'constructor', w_Array)

    # 15.4.4.2
    put_native_function(w_ArrayPrototype, 'toString', to_string)
    # 15.4.4.5
    put_native_function(w_ArrayPrototype, 'join', join, params = ['separator'])
    # 15.4.4.6
    put_native_function(w_ArrayPrototype, 'pop', pop)
    # 15.4.4.7
    put_native_function(w_ArrayPrototype, 'push', push)
    # 15.4.4.8
    put_native_function(w_ArrayPrototype, 'reverse', reverse)
    # 15.4.4.11
    put_native_function(w_ArrayPrototype, 'sort', sort)

# 15.4.4.7
def push(this, args):
    o = this.ToObject()
    len_val = o.get('length')
    n = len_val.ToUInt32()

    for item in args:
        e = item
        o.put(str(n), e, True)
        n = n + 1

    o.put('length', _w(n), True)

    return n

# 15.4.4.2
def to_string(this, args):
    array = this.ToObject()
    func = array.get('join')
    if func.is_callable():
        return func.Call(this = this).to_string()
    else:
        return this.to_string()

# 15.4.4.5
def join(this, args):
    separator = get_arg(args, 0)

    o = this.ToObject()
    len_val = o.get('length')
    length = len_val.ToUInt32()

    if separator is w_Undefined:
        sep = ','
    else:
        sep = separator.to_string()

    if length == 0:
        return ''

    element0 = o.get('0')
    if isnull_or_undefined(element0):
        r = ''
    else:
        r = element0.to_string()

    k = 1

    while(k < length):
        s = r + sep
        element = o.get(str(k))
        if isnull_or_undefined(element):
            _next = ''
        else:
            _next = element.to_string()
        r = s + _next
        k += 1

    return r

# 15.4.4.6
def pop(this, args):
    o = this.ToObject()
    lenVal = o.get('length')
    l = lenVal.ToUInt32()

    if l == 0:
        o.put('length', _w(0))
        return w_Undefined
    else:
        indx = l - 1
        indxs = str(indx)
        element = o.get(indxs)
        o.delete(indxs, True)
        o.put('length', _w(indx))
        return element

# 15.4.4.8
def reverse(this, args):
    o = this.ToObject()
    length = o.get('length').ToUInt32()

    import math
    middle = math.floor(length/2)

    lower = 0
    while lower != middle:
        upper = length - lower - 1
        lower_p = str(lower)
        upper_p = str(upper)
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
def sort(this, args):
    obj = this
    length = this.get('length').ToUInt32()

    comparefn = get_arg(args, 0)

    # TODO check if implementation defined

    # sorts need to be in-place, lets do some very non-fancy bubble sort for starters
    while True:
        swapped = False
        for i in xrange(1, length):
            x = str(i - 1)
            y = str(i)
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
            raise JsTypeError()

        res = comparefn.Call(args = [x, y], this = w_Undefined)
        return res.ToInteger()

    x_string = x.to_string()
    y_string = y.to_string()
    if x_string < y_string:
        return -1
    if x_string > y_string:
        return 1
    return 0


#class W_ArraySort(W_NewBuiltin):
    #length = 1
    ##XXX: further optimize this function
    #def Call(self, args=[], this=None):
        #length = this.Get('length').ToUInt32()

        ## According to ECMA-262 15.4.4.11, non-existing properties always come after
        ## existing values. Undefined is always greater than any other value.
        ## So we create a list of non-undefined values, sort them, and append undefined again.
        #values = []
        #undefs = r_uint(0)

        #for i in range(length):
            #P = str(i)
            #if not this.HasProperty(P):
                ## non existing property
                #continue
            #obj = this.Get(str(i))
            #if obj is w_Undefined:
                #undefs += 1
                #continue
            #values.append(obj)

        ## sort all values
        #if len(args) > 0 and args[0] is not w_Undefined:
            #sorter = Sorter(values, compare_fn=args[0])
        #else:
            #sorter = Sorter(values)
        #sorter.sort()

        ## put sorted values back
        #values = sorter.list
        #for i in range(len(values)):
            #this.Put(str(i), values[i])

        ## append undefined values
        #newlength = len(values)
        #while undefs > 0:
            #undefs -= 1
            #this.Put(str(newlength), w_Undefined)
            #newlength += 1

        ## delete non-existing elements on the end
        #while length > newlength:
            #this.Delete(str(newlength))
            #newlength += 1
        #return this

from js.jsobj import isnull_or_undefined, _w, w_Undefined

# 15.4.4.7
def push(this, args):
    o = this.ToObject()
    lenVal = o.Get('length')
    n = lenVal.ToUInt32()

    for item in args:
        e = item
        o.Put(str(n), e)
        n = n + 1

    o.set_length(n)

    return o

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
    o = this.ToObject()
    lenVal = o.get('length')
    length = lenVal.ToUInt32()

    sep = ','
    if (len(args) > 0):
        sep = args[0].to_string()

    if length == 0:
        return ''

    element0 = o.get('0')
    if isnull_or_undefined(element0):
        return ''

    r = element0.to_string()

    k = 1

    while(k < length):
        s = r + sep
        element = o.get(str(k))
        if isnull_or_undefined(element):
            n = ''
        else:
            n = element.to_string()
        r = s + n
        k = k + 1

    return r

# 15.4.4.6
def pop(this, args):
    o = this.ToObject()
    lenVal = o.Get('length')
    l = lenVal.ToUInt32()

    if l == 0:
        o.Put('length', _w(0))
        return w_Undefined
    else:
        indx = l - 1
        indxs = str(indx)
        element = o.Get(indxs)
        o.Delete(indxs)
        o.Put('length', _w(indx))
        return element

# 15.4.4.8
def reverse(this, args):
    o = this.ToObject()
    length = o.Get('length').ToUInt32()

    import math
    middle = math.floor(length/2)

    lower = 0
    while lower != middle:
        upper = length - lower - 1
        lowerP = str(lower)
        upperP = str(upper)
        lowerValue = o.Get(lowerP)
        upperValue = o.Get(upperP)
        lowerExists = o.HasProperty(lowerP)
        upperExists = o.HasProperty(upperP)

        if lowerExists is True and upperExists is True:
            o.Put(lowerP, upperValue)
            o.Put(upperP, lowerValue)
        elif lowerExists is False and upperExists is True:
            o.Put(lowerP, upperValue)
            o.Delete(upperP)
        elif lowerExists is True and upperExists is False:
            o.Delete(lowerP)
            o.Put(upperP, lowerValue)

        lower = lower + 1

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

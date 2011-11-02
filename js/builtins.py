import math
import time
from pypy.rlib import rrandom
random = rrandom.Random(int(time.time()))

from js.jsobj import W_Object,\
     w_Undefined, W_NewBuiltin, W_IntNumber, w_Null, create_object, W_Boolean,\
     W_FloatNumber, W_String, W_Builtin, W_Array, w_Null, newbool,\
     isnull_or_undefined, W_PrimitiveObject, W_ListObject, W_BaseNumber,\
     DONT_DELETE, DONT_ENUM, READ_ONLY, INTERNAL
from js.execution import ThrowException, JsTypeError

from js.jsparser import parse, ParseError
from js.astbuilder import make_ast_builder, make_eval_ast_builder
from js.jscode import JsCode

from pypy.rlib.objectmodel import specialize
from pypy.rlib.listsort import TimSort
from pypy.rlib.rarithmetic import r_uint
from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf
from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.streamio import open_file_as_stream

from pypy.rlib import jit

@jit.dont_look_inside
def eval_source(script_source, sourcename):
    temp_tree = parse(script_source)
    builder = make_eval_ast_builder()
    return builder.dispatch(temp_tree)

@jit.dont_look_inside
def load_source(script_source, sourcename):
    temp_tree = parse(script_source)
    builder = make_ast_builder()
    return builder.dispatch(temp_tree)

def load_file(filename):
    f = open_file_as_stream(filename)
    t = load_source(f.readall(), filename)
    f.close()
    return t

def make_loadjs(interp):
    def f(args, this):
        filename = str(args[0].ToString())
        t = load_file(filename)
        interp.run(t)
        return w_Undefined
    return f

class W_Eval(W_NewBuiltin):
    def __init__(self, ctx):
        W_NewBuiltin.__init__(self)
        self.ctx = ctx

    length = 1
    def Call(self, args=[], this=None):
        if len(args) >= 1:
            arg0 = args[0]
            if  isinstance(arg0, W_String):
                src = arg0.strval
            else:
                return arg0
        else:
            return w_Undefined

        try:
            node = eval_source(src, 'evalcode')
        except ParseError, e:
            raise ThrowException(W_String('SyntaxError: '+str(e)))

        bytecode = JsCode()
        node.emit(bytecode)
        func = bytecode.make_js_function()
        return func.run(self.ctx)

class W_ParseInt(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        if len(args) < 1:
            return W_FloatNumber(NAN)
        s = args[0].ToString().strip(" ")
        if len(args) > 1:
            radix = args[1].ToInt32()
        else:
            radix = 10
        if len(s) >= 2 and (s.startswith('0x') or s.startswith('0X')) :
            radix = 16
            s = s[2:]
        if s == '' or radix < 2 or radix > 36:
            return W_FloatNumber(NAN)
        try:
            n = int(s, radix)
        except ValueError:
            return W_FloatNumber(NAN)
        return W_IntNumber(n)

class W_ParseFloat(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        if len(args) < 1:
            return W_FloatNumber(NAN)
        s = args[0].ToString().strip(" ")
        try:
            n = float(s)
        except ValueError:
            n = NAN
        return W_FloatNumber(n)

class W_FromCharCode(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        temp = []
        for arg in args:
            i = arg.ToInt32() % 65536 # XXX should be uint16
            temp.append(chr(i))
        return W_String(''.join(temp))

class W_CharAt(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        string = this.ToString()
        if len(args)>=1:
            pos = args[0].ToInt32()
            if (not pos >=0) or (pos > len(string) - 1):
                return W_String('')
        else:
            return W_String('')
        return W_String(string[pos])

class W_CharCodeAt(W_NewBuiltin):
    def Call(self, args=[], this=None):
        string = this.ToString()
        if len(args)>=1:
            pos = args[0].ToInt32()
            if pos < 0 or pos > len(string) - 1:
                return W_FloatNumber(NAN)
        else:
            return W_FloatNumber(NAN)
        char = string[pos]
        return W_IntNumber(ord(char))

class W_Concat(W_NewBuiltin):
    def Call(self, args=[], this=None):
        string = this.ToString()
        others = [obj.ToString() for obj in args]
        string += ''.join(others)
        return W_String(string)

class W_IndexOf(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        string = this.ToString()
        if len(args) < 1:
            return W_IntNumber(-1)
        substr = args[0].ToString()
        size = len(string)
        subsize = len(substr)
        if len(args) < 2:
            pos = 0
        else:
            pos = args[1].ToInteger()
        pos = int(min(max(pos, 0), size))
        assert pos >= 0
        return W_IntNumber(string.find(substr, pos))

class W_LastIndexOf(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        string = this.ToString()
        if len(args) < 1:
            return W_IntNumber(-1)
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
        return W_IntNumber(string.rfind(substr, 0, endpos))

class W_Substring(W_NewBuiltin):
    length = 2
    def Call(self, args=[], this=None):
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
        return W_String(string[start:end])

class W_Split(W_NewBuiltin):
    length = 2
    def Call(self, args=[], this=None):
        string = this.ToString()

        if len(args) < 1 or args[0] is w_Undefined:
            return create_array([W_String(string)])
        else:
            separator = args[0].ToString()

        if len(args) >= 2:
            limit = args[1].ToUInt32()
            raise ThrowException(W_String("limit not implemented"))
            # array = string.split(separator, limit)
        else:
            array = string.split(separator)

        w_array = create_array()
        i = 0
        while i < len(array):
            w_str = W_String(array[i])
            w_array.Put(str(i), w_str)
            i += 1

        return w_array

class W_ToLowerCase(W_NewBuiltin):
    length = 0
    def Call(self, args=[], this=None):
        string = this.ToString()
        return W_String(string.lower())

class W_ToUpperCase(W_NewBuiltin):
    length = 0
    def Call(self, args=[], this=None):
        string = this.ToString()
        return W_String(string.upper())

class W_ToString(W_NewBuiltin):
    def Call(self, args=[], this=None):
        assert isinstance(this, W_PrimitiveObject)
        return W_String("[object %s]"%this.Class)

class W_ValueOf(W_NewBuiltin):
    length = 0
    def Call(self, args=[], this=None):
        return this

class W_HasOwnProperty(W_NewBuiltin):
    def Call(self, args=[], this=None):
        if len(args) >= 1:
            propname = args[0].ToString()
            if propname in self._get_property_keys():
                return newbool(True)
        return newbool(False)

class W_IsPrototypeOf(W_NewBuiltin):
    def Call(self, args=[], this=None):
        w_obj = args[0]
        if len(args) >= 1 and isinstance(w_obj, W_PrimitiveObject):
            O = this
            assert isinstance(w_obj, W_PrimitiveObject)
            V = w_obj.Prototype
            while V is not None:
                if O == V:
                    return newbool(True)
                assert isinstance(V, W_PrimitiveObject)
                V = V.Prototype
        return newbool(False)

class W_PropertyIsEnumerable(W_NewBuiltin):
    def Call(self, args=[], this=None):
        if len(args) >= 1:
            propname = args[0].ToString()
            if self._has_property(propname) and not self._get_property_flags(propname) & DONT_ENUM:
                return newbool(True)
        return newbool(False)

class W_Function(W_NewBuiltin):
    def __init__(self, ctx, Prototype=None, Class='function', Value=w_Undefined):
        W_NewBuiltin.__init__(self, Prototype, Class, Value)
        self.ctx = ctx

    def Call(self, args=[], this=None):
        tam = len(args)
        if tam >= 1:
            fbody  = args[tam-1].ToString()
            argslist = []
            for i in range(tam-1):
                argslist.append(args[i].ToString())
            fargs = ','.join(argslist)
            functioncode = "function (%s) {%s}"%(fargs, fbody)
        else:
            functioncode = "function () {}"
        #remove program and sourcelements node
        funcnode = parse(functioncode).children[0].children[0]
        builder = make_ast_builder()
        ast = builder.dispatch(funcnode)
        bytecode = JsCode()
        ast.emit(bytecode)
        func = bytecode.make_js_function()
        return func.run(self.ctx)

    def Construct(self, args=[]):
        return self.Call(args, this=None)

functionstring= 'function (arguments go here!) {\n'+ \
                '    [lots of stuff :)]\n'+ \
                '}'
class W_FToString(W_NewBuiltin):
    def Call(self, args=[], this=None):
        assert isinstance(this, W_PrimitiveObject)
        if this.Class == 'Function':
            return W_String(functionstring)
        else:
            raise JsTypeError('this is not a function object')

class W_Apply(W_NewBuiltin):
    def __init__(self, ctx):
        W_NewBuiltin.__init__(self)
        self.ctx = ctx

    def Call(self, args=[], this=None):
        try:
            if isnull_or_undefined(args[0]):
                thisArg = self.ctx.get_global()
            else:
                thisArg = args[0].ToObject()
        except IndexError:
            thisArg = self.ctx.get_global()

        try:
            arrayArgs = args[1]
            callargs = arrayArgs.tolist()
        except IndexError:
            callargs = []
        return this.Call(callargs, this=thisArg)

class W_Call(W_NewBuiltin):
    def __init__(self, ctx):
        W_NewBuiltin.__init__(self)
        self.ctx = ctx

    def Call(self, args=[], this=None):
        if len(args) >= 1:
            if isnull_or_undefined(args[0]):
                thisArg = self.ctx.get_global()
            else:
                thisArg = args[0]
            callargs = args[1:]
        else:
            thisArg = self.ctx.get_global()
            callargs = []
        return this.Call(callargs, this = thisArg)

class W_ValueToString(W_NewBuiltin):
    "this is the toString function for objects with Value"
    mytype = ''
    def Call(self, args=[], this=None):
        assert isinstance(this, W_PrimitiveObject)
        if this.Value.type() != self.mytype:
            raise JsTypeError('Wrong type')
        return W_String(this.Value.ToString())


class W_NumberValueToString(W_ValueToString):
    mytype = 'number'

class W_BooleanValueToString(W_ValueToString):
    mytype = 'boolean'

class W_StringValueToString(W_ValueToString):
    mytype = 'string'

class W_ArrayToString(W_NewBuiltin):
    length = 0
    def Call(self, args=[], this=None):
        return W_String(common_join(this, sep=','))

class W_ArrayJoin(W_NewBuiltin):
    length = 1
    def Call(self, args=[], this=None):
        if len(args) >= 1 and not args[0] is w_Undefined:
            sep = args[0].ToString()
        else:
            sep = ','

        return W_String(common_join(this, sep))

class W_ArrayPush(W_NewBuiltin):
    def Call(self, args=[], this=None):
        n = this.Get('length').ToUInt32()
        for arg in args:
            this.Put(str(n), arg)
            n += 1
        j = W_IntNumber(n)
        this.Put('length', j);
        return j

class W_ArrayPop(W_NewBuiltin):
    def Call(self, args=[], this=None):
        len = this.Get('length').ToUInt32()
        if(len == 0):
            return w_Undefined
        else:
            indx = len-1
            indxstr = str(indx)
            element = this.Get(indxstr)
            this.Delete(indxstr)
            this.Put('length', W_IntNumber(indx))
            return element

class W_ArrayReverse(W_NewBuiltin):
    length = 0
    def Call(self, args=[], this=None):
        r2 = this.Get('length').ToUInt32()
        k = r_uint(0)
        r3 = r_uint(math.floor( float(r2)/2.0 ))
        if r3 == k:
            return this

        while k < r3:
            r6 = r2 - k - 1
            r7 = str(k)
            r8 = str(r6)

            r9 = this.Get(r7)
            r10 = this.Get(r8)

            this.Put(r7, r10)
            this.Put(r8, r9)
            k += 1

        return this

class W_ArraySort(W_NewBuiltin):
    length = 1
    #XXX: further optimize this function
    def Call(self, args=[], this=None):
        length = this.Get('length').ToUInt32()

        # According to ECMA-262 15.4.4.11, non-existing properties always come after
        # existing values. Undefined is always greater than any other value.
        # So we create a list of non-undefined values, sort them, and append undefined again.
        values = []
        undefs = r_uint(0)

        for i in range(length):
            P = str(i)
            if not this.HasProperty(P):
                # non existing property
                continue
            obj = this.Get(str(i))
            if obj is w_Undefined:
                undefs += 1
                continue
            values.append(obj)

        # sort all values
        if len(args) > 0 and args[0] is not w_Undefined:
            sorter = Sorter(values, compare_fn=args[0])
        else:
            sorter = Sorter(values)
        sorter.sort()

        # put sorted values back
        values = sorter.list
        for i in range(len(values)):
            this.Put(str(i), values[i])

        # append undefined values
        newlength = len(values)
        while undefs > 0:
            undefs -= 1
            this.Put(str(newlength), w_Undefined)
            newlength += 1

        # delete non-existing elements on the end
        while length > newlength:
            this.Delete(str(newlength))
            newlength += 1
        return this

class W_NativeObject(W_Object):
    def __init__(self, Class, Prototype, Value=w_Undefined):
        W_Object.__init__(self, Prototype, Class, Value)

class W_DateObject(W_NativeObject):
    def Call(self, args=[], this=None):
        return create_object('Object')

    def Construct(self, args=[]):
        v = int(time.time()*1000)
        return create_object('Date', Value = W_IntNumber(v))

def pypy_repr(args, this):
    o = args[0]
    t = 'Unknown'
    if isinstance(o, W_FloatNumber):
        t = 'W_FloatNumber'
    elif isinstance(o, W_IntNumber):
        t = 'W_IntNumber'
    elif isinstance(o, W_BaseNumber):
        t = 'W_Base_Number'
    return W_String(t)

def put_values(ctx, obj, dictvalues):
    for key,value in dictvalues.iteritems():
        obj.Put(key, value)

@specialize.memo()
def get_value_of(type):
    class W_ValueValueOf(W_NewBuiltin):
        "this is the valueOf function for objects with Value"
        def Call(self, args=[], this=None):
            assert isinstance(this, W_PrimitiveObject)
            if type != this.Class:
                raise JsTypeError('%s.prototype.valueOf called with incompatible type' % self.type())
            return this.Value
    return W_ValueValueOf

def common_join(this, sep=','):
    length = this.Get('length').ToUInt32()
    l = []
    i = 0
    while i < length:
        item = this.Get(str(i))
        if isnull_or_undefined(item):
            item_string = ''
        else:
            item_string = item.ToString()
        l.append(item_string)
        i += 1

    return sep.join(l)

class Sorter(TimSort):
    def __init__(self, list, listlength=None, compare_fn=None):
        TimSort.__init__(self, list, listlength)
        self.compare_fn = compare_fn

    def lt(self, a, b):
        if self.compare_fn:
            result = self.compare_fn.Call([a, b]).ToInt32()
            return result == -1
        return a.ToString() < b.ToString()

def writer(x):
    print x

def printjs(args, this):
    writer(",".join([i.ToString() for i in args]))
    return w_Undefined

def noop(*args):
    return w_Undefined

def isnanjs(args, this):
    if len(args) < 1:
        return newbool(True)
    return newbool(isnan(args[0].ToNumber()))

def isfinitejs(args, this):
    if len(args) < 1:
        return newbool(True)
    n = args[0].ToNumber()
    if  isinf(n) or isnan(n):
        return newbool(False)
    else:
        return newbool(True)

def absjs(args, this):
    val = args[0]
    if isinstance(val, W_IntNumber):
        if val.intval > 0:
            return val # fast path
        return W_IntNumber(-val.intval)
    return W_FloatNumber(abs(args[0].ToNumber()))

def floorjs(args, this):
    if len(args) < 1:
        return W_FloatNumber(NAN)

    val = args[0].ToNumber()

    pos = math.floor(val)
    if isnan(val):
        pos = INFINITY

    return W_FloatNumber(pos)

def roundjs(args, this):
    return floorjs(args, this)

def powjs(args, this):
    return W_FloatNumber(math.pow(args[0].ToNumber(), args[1].ToNumber()))

def sqrtjs(args, this):
    return W_FloatNumber(math.sqrt(args[0].ToNumber()))

def logjs(args, this):
    return W_FloatNumber(math.log(args[0].ToNumber()))

def versionjs(args, this):
    return w_Undefined

def randomjs(args, this):
    return W_FloatNumber(random.random())

def minjs(args, this):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return W_FloatNumber(min(a, b))

def maxjs(args, this):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return W_FloatNumber(max(a, b))

def _ishex(ch):
    return ((ch >= 'a' and ch <= 'f') or (ch >= '0' and ch <= '9') or
            (ch >= 'A' and ch <= 'F'))

def unescapejs(args, this):
    # XXX consider using StringBuilder here
    res = []
    w_string = args[0]
    if not isinstance(w_string, W_String):
        raise JsTypeError(W_String("Expected string"))
    assert isinstance(w_string, W_String)
    strval = w_string.strval
    lgt = len(strval)
    i = 0
    while i < lgt:
        ch = strval[i]
        if ch == '%':
            if (i + 2 < lgt and _ishex(strval[i+1]) and _ishex(strval[i+2])):
                ch = chr(int(strval[i + 1] + strval[i + 2], 16))
                i += 2
            elif (i + 5 < lgt and strval[i + 1] == 'u' and
                  _ishex(strval[i + 2]) and _ishex(strval[i + 3]) and
                  _ishex(strval[i + 4]) and _ishex(strval[i + 5])):
                ch = chr(int(strval[i+2:i+6], 16))
                i += 5
        i += 1
        res.append(ch)
    return W_String(''.join(res))

class W_ObjectObject(W_NativeObject):
    def __init__(self, Class, Prototype, Value=w_Undefined):
        W_NativeObject.__init__(self, Class, Prototype, Value)

    def Call(self, args=[], this=None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return args[0].ToObject()
        else:
            return self.Construct()

    def Construct(self, args=[]):
        if (len(args) >= 1 and not args[0] is w_Undefined and not
            args[0] is w_Null):
            # XXX later we could separate builtins and normal objects
            return args[0].ToObject()
        return create_object('Object')

class W_BooleanObject(W_NativeObject):
    def Call(self, args=[], this=None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return newbool(args[0].ToBoolean())
        else:
            return newbool(False)

    def Construct(self, args=[]):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            Value = newbool(args[0].ToBoolean())
            return create_object('Boolean', Value = Value)
        return create_object('Boolean', Value = newbool(False))

class W_NumberObject(W_NativeObject):
    def Call(self, args=[], this=None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return W_FloatNumber(args[0].ToNumber())
        elif len(args) >= 1 and args[0] is w_Undefined:
            return W_FloatNumber(NAN)
        else:
            return W_FloatNumber(0.0)

    def ToNumber(self):
        return 0.0

    def Construct(self, args=[]):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            Value = W_FloatNumber(args[0].ToNumber())
            return create_object('Number', Value = Value)
        return create_object('Number', Value = W_FloatNumber(0.0))

class W_StringObject(W_NativeObject):
    length = 1
    def Call(self, args=[], this=None):
        if len(args) >= 1:
            return W_String(args[0].ToString())
        else:
            return W_String('')

    def Construct(self, args=[]):
        if len(args) >= 1:
            Value = W_String(args[0].ToString())
        else:
            Value = W_String('')
        return Value.ToObject()

def create_array(elements=[]):
    # TODO do not get array prototype from global context?
    #proto = ctx.get_global().Get('Array').Get('prototype')
    from js.builtins import get_builtin_prototype
    proto = get_builtin_prototype('Array')
    assert isinstance(proto, W_PrimitiveObject)
    array = W_Array(Prototype=proto, Class = proto.Class)
    i = 0
    while i < len(elements):
        array.Put(str(i), elements[i])
        i += 1

    return array

class W_ArrayObject(W_NativeObject):
    def __init__(self, Class, Prototype):
        W_NativeObject.__init__(self, Class, Prototype, None )

    def Call(self, args=[], this=None):
        if len(args) == 1 and isinstance(args[0], W_BaseNumber):
            array = create_array()
            array.Put('length', args[0])
        else:
            array = create_array(args)
        return array

    def Construct(self, args=[]):
        return self.Call(args)

_builtin_prototypes = {}
def get_builtin_prototype(name):
    p = _builtin_prototypes.get(name, None)
    if p is None:
        return _builtin_prototypes.get('Object', None)
    return p

def _register_builtin_prototype(name, obj):
    _builtin_prototypes[name] = obj

def setup_builtins(interp):
    allon = DONT_ENUM | DONT_DELETE | READ_ONLY
    from js.jsexecution_context import make_global_context
    ctx = make_global_context()
    w_Global = ctx.to_context_object()

    w_ObjPrototype = W_Object(Prototype=None, Class='Object')

    w_Function = W_Function(ctx, Class='Function', Prototype=w_ObjPrototype)
    w_FncPrototype = W_Function(ctx, Class='Function', Prototype=w_ObjPrototype)#W_Object(Prototype=None, Class='Function')

    w_Function.Put('length', W_IntNumber(1), flags = allon)
    w_Global.Put('Function', w_Function)

    w_Object = W_ObjectObject('Object', w_FncPrototype)
    w_Object.Put('prototype', w_ObjPrototype, flags = allon)
    w_Object.Put('length', W_IntNumber(1), flags = allon)
    w_Global.Prototype = w_ObjPrototype

    w_Object.Put('prototype', w_ObjPrototype, flags = allon)
    w_Global.Put('Object', w_Object)

    w_Function.Put('prototype', w_FncPrototype, flags = allon)
    w_Function.Put('constructor', w_Function, flags=allon)

    toString = W_ToString()

    put_values(ctx, w_ObjPrototype, {
        'constructor': w_Object,
        '__proto__': w_Null,
        'toString': toString,
        'toLocaleString': toString,
        'valueOf': W_ValueOf(),
        'hasOwnProperty': W_HasOwnProperty(),
        'isPrototypeOf': W_IsPrototypeOf(),
        'propertyIsEnumerable': W_PropertyIsEnumerable(),
    })
    _register_builtin_prototype('Object', w_ObjPrototype)

    #properties of the function prototype
    put_values(ctx, w_FncPrototype, {
        'constructor': w_Function,
        '__proto__': w_FncPrototype,
        'toString': W_FToString(),
        'apply': W_Apply(ctx),
        'call': W_Call(ctx),
        'arguments': w_Null,
        'valueOf': W_ValueOf(),
    })
    _register_builtin_prototype('Function', w_FncPrototype)

    w_Boolean = W_BooleanObject('Boolean', w_FncPrototype)
    w_Boolean.Put('constructor', w_FncPrototype, flags = allon)
    w_Boolean.Put('length', W_IntNumber(1), flags = allon)

    w_BoolPrototype = create_object('Object', Value=newbool(False))
    w_BoolPrototype.Class = 'Boolean'

    put_values(ctx, w_BoolPrototype, {
        'constructor': w_FncPrototype,
        '__proto__': w_ObjPrototype,
        'toString': W_BooleanValueToString(),
        'valueOf': get_value_of('Boolean')(),
    })
    _register_builtin_prototype('Boolean', w_BoolPrototype)

    w_Boolean.Put('prototype', w_BoolPrototype, flags = allon)
    w_Global.Put('Boolean', w_Boolean)

    #Number
    w_Number = W_NumberObject('Number', w_FncPrototype)

    w_empty_fun = w_Function.Call(args=[W_String('')])

    w_NumPrototype = create_object('Object', Value=W_FloatNumber(0.0))
    w_NumPrototype.Class = 'Number'
    put_values(ctx, w_NumPrototype, {
        'constructor': w_Number,
        '__proto__': w_empty_fun,
        'toString': W_NumberValueToString(),
        'valueOf': get_value_of('Number')(),
    })
    _register_builtin_prototype('Number', w_NumPrototype)

    put_values(ctx, w_Number, {
        'constructor': w_FncPrototype,
        'prototype': w_NumPrototype,
        '__proto__': w_FncPrototype,
        'length'   : W_IntNumber(1),
    })
    f = w_Number._get_property_flags('prototype') | READ_ONLY
    w_Number._set_property_flags('prototype', f)
    w_Number.Put('MAX_VALUE', W_FloatNumber(1.7976931348623157e308), flags = READ_ONLY | DONT_DELETE)
    w_Number.Put('MIN_VALUE', W_FloatNumber(0), flags = READ_ONLY | DONT_DELETE)
    w_Number.Put('NaN', W_FloatNumber(NAN), flags = READ_ONLY | DONT_DELETE)
    # ^^^ this is exactly in test case suite
    w_Number.Put('POSITIVE_INFINITY', W_FloatNumber(INFINITY), flags = READ_ONLY | DONT_DELETE)
    w_Number.Put('NEGATIVE_INFINITY', W_FloatNumber(-INFINITY), flags = READ_ONLY | DONT_DELETE)


    w_Global.Put('Number', w_Number)


    #String
    w_String = W_StringObject('String', w_FncPrototype)

    w_StrPrototype = create_object('Object', Value=W_String(''))
    w_StrPrototype.Class = 'String'
    w_StrPrototype.Put('length', W_IntNumber(0))

    put_values(ctx, w_StrPrototype, {
        'constructor': w_String,
        '__proto__': w_StrPrototype,
        'toString': W_StringValueToString(),
        'valueOf': get_value_of('String')(),
        'charAt': W_CharAt(),
        'charCodeAt': W_CharCodeAt(),
        'concat': W_Concat(),
        'indexOf': W_IndexOf(),
        'lastIndexOf': W_LastIndexOf(),
        'substring': W_Substring(),
        'split': W_Split(),
        'toLowerCase': W_ToLowerCase(),
        'toUpperCase': W_ToUpperCase()
    })
    _register_builtin_prototype('String', w_StrPrototype)

    w_String.Put('prototype', w_StrPrototype, flags=allon)
    w_String.Put('fromCharCode', W_FromCharCode())
    w_Global.Put('String', w_String)

    w_Array = W_ArrayObject('Array', w_FncPrototype)

    w_ArrPrototype = W_Array(Prototype=w_ObjPrototype)

    put_values(ctx, w_ArrPrototype, {
        'constructor': w_FncPrototype,
        '__proto__': w_ArrPrototype,
        'toString': W_ArrayToString(),
        'join': W_ArrayJoin(),
        'reverse': W_ArrayReverse(),
        'sort': W_ArraySort(),
        'push': W_ArrayPush(),
        'pop': W_ArrayPop(),
    })
    _register_builtin_prototype('Array', w_ArrPrototype)

    w_Array.Put('prototype', w_ArrPrototype, flags = allon)
    w_Array.Put('__proto__', w_FncPrototype, flags = allon)
    w_Array.Put('length', W_IntNumber(1), flags = allon)
    w_Global.Put('Array', w_Array)


    #Math
    w_math = W_Object(Class='Math')
    w_Global.Put('Math', w_math)
    w_math.Put('__proto__',  w_ObjPrototype)
    w_math.Put('prototype', w_ObjPrototype, flags = allon)
    w_math.Put('abs', W_Builtin(absjs, Class='function'))
    w_math.Put('floor', W_Builtin(floorjs, Class='function'))
    w_math.Put('round', W_Builtin(roundjs, Class='function'))
    w_math.Put('pow', W_Builtin(powjs, Class='function'))
    w_math.Put('sqrt', W_Builtin(sqrtjs, Class='function'))
    w_math.Put('log', W_Builtin(logjs, Class='function'))
    w_math.Put('E', W_FloatNumber(math.e), flags=allon)
    w_math.Put('LN2', W_FloatNumber(math.log(2)), flags=allon)
    w_math.Put('LN10', W_FloatNumber(math.log(10)), flags=allon)
    log2e = math.log(math.e) / math.log(2) # rpython supports log with one argument only
    w_math.Put('LOG2E', W_FloatNumber(log2e), flags=allon)
    w_math.Put('LOG10E', W_FloatNumber(math.log10(math.e)), flags=allon)
    w_math.Put('PI', W_FloatNumber(math.pi), flags=allon)
    w_math.Put('SQRT1_2', W_FloatNumber(math.sqrt(0.5)), flags=allon)
    w_math.Put('SQRT2', W_FloatNumber(math.sqrt(2)), flags=allon)
    w_math.Put('random', W_Builtin(randomjs, Class='function'))
    w_math.Put('min', W_Builtin(minjs, Class='function'))
    w_math.Put('max', W_Builtin(maxjs, Class='function'))
    w_Global.Put('version', W_Builtin(versionjs), flags=allon)

    #Date
    w_Date = W_DateObject('Date', w_FncPrototype)

    w_DatePrototype = create_object('Object', Value=W_String(''))
    w_DatePrototype.Class = 'Date'

    put_values(ctx, w_DatePrototype, {
        '__proto__': w_DatePrototype,
        'valueOf': get_value_of('Date')(),
        'getTime': get_value_of('Date')()
    })
    _register_builtin_prototype('Date', w_DatePrototype)

    w_Date.Put('prototype', w_DatePrototype, flags=allon)

    w_Global.Put('Date', w_Date)

    w_Global.Put('NaN', W_FloatNumber(NAN), flags = DONT_ENUM | DONT_DELETE)
    w_Global.Put('Infinity', W_FloatNumber(INFINITY), flags = DONT_ENUM | DONT_DELETE)
    w_Global.Put('undefined', w_Undefined, flags = DONT_ENUM | DONT_DELETE)
    w_Global.Put('eval', W_Eval(ctx))
    w_Global.Put('parseInt', W_ParseInt())
    w_Global.Put('parseFloat', W_ParseFloat())
    w_Global.Put('isNaN', W_Builtin(isnanjs))
    w_Global.Put('isFinite', W_Builtin(isfinitejs))
    w_Global.Put('print', W_Builtin(printjs))
    w_Global.Put('alert', W_Builtin(noop))
    w_Global.Put('unescape', W_Builtin(unescapejs))

    w_Global.Put('this', w_Global)

    # debugging
    if not we_are_translated():
        w_Global.Put('pypy_repr', W_Builtin(pypy_repr))

    w_Global.Put('load', W_Builtin(make_loadjs(interp)))

    return (ctx, w_Global, w_Object)

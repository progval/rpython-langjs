import time

from js.jsobj import w_Undefined, W_IntNumber, w_Null, create_object, W_Boolean,\
     W_FloatNumber, W_String, newbool,\
     isnull_or_undefined, W_Number,\
     DONT_DELETE, DONT_ENUM, READ_ONLY, INTERNAL, _w
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
    def f(this, *args):
        filename = str(args[0].ToString())
        t = load_file(filename)
        interp.run(t)
        return w_Undefined
    return f

# 15.1.2.1
from js.jsobj import W_BasicFunction
class W__Eval(W_BasicFunction):
    def ToString(self):
        return "function eval() { [native code] }"

    def Call(self, args=[], this=None):
        if len(args) == 0:
            return w_Undefined

        arg0 = args[0]
        if  not isinstance(arg0, W_String):
            return arg0

        src = arg0.ToString()
        try:
            node = eval_source(src, 'evalcode')
        except ParseError, e:
            raise ThrowException(W_String('SyntaxError: '+str(e)))

        bytecode = JsCode()
        node.emit(bytecode)
        func = bytecode.make_js_function()
        return func.run(self._context_)

#class W_ParseInt(W_NewBuiltin):
    #length = 1
    #def Call(self, args=[], this=None):
        #if len(args) < 1:
            #return W_FloatNumber(NAN)
        #s = args[0].ToString().strip(" ")
        #if len(args) > 1:
            #radix = args[1].ToInt32()
        #else:
            #radix = 10
        #if len(s) >= 2 and (s.startswith('0x') or s.startswith('0X')) :
            #radix = 16
            #s = s[2:]
        #if s == '' or radix < 2 or radix > 36:
            #return W_FloatNumber(NAN)
        #try:
            #n = int(s, radix)
        #except ValueError:
            #return W_FloatNumber(NAN)
        #return W_IntNumber(n)

#class W_ParseFloat(W_NewBuiltin):
    #length = 1
    #def Call(self, args=[], this=None):
        #if len(args) < 1:
            #return W_FloatNumber(NAN)
        #s = args[0].ToString().strip(" ")
        #try:
            #n = float(s)
        #except ValueError:
            #n = NAN
        #return W_FloatNumber(n)

#class W_FromCharCode(W_NewBuiltin):
    #length = 1
    #def Call(self, args=[], this=None):
        #temp = []
        #for arg in args:
            #i = arg.ToInt32() % 65536 # XXX should be uint16
            #temp.append(chr(i))
        #return W_String(''.join(temp))

#class W_CharCodeAt(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #if len(args)>=1:
            #pos = args[0].ToInt32()
            #if pos < 0 or pos > len(string) - 1:
                #return W_FloatNumber(NAN)
        #else:
            #return W_FloatNumber(NAN)
        #char = string[pos]
        #return W_IntNumber(ord(char))

#class W_Concat(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #others = [obj.ToString() for obj in args]
        #string += ''.join(others)
        #return W_String(string)

#class W_IndexOf(W_NewBuiltin):
    #length = 1
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #if len(args) < 1:
            #return W_IntNumber(-1)
        #substr = args[0].ToString()
        #size = len(string)
        #subsize = len(substr)
        #if len(args) < 2:
            #pos = 0
        #else:
            #pos = args[1].ToInteger()
        #pos = int(min(max(pos, 0), size))
        #assert pos >= 0
        #return W_IntNumber(string.find(substr, pos))

#class W_LastIndexOf(W_NewBuiltin):
    #length = 1
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #if len(args) < 1:
            #return W_IntNumber(-1)
        #substr = args[0].ToString()
        #if len(args) < 2:
            #pos = INFINITY
        #else:
            #val = args[1].ToNumber()
            #if isnan(val):
                #pos = INFINITY
            #else:
                #pos = args[1].ToInteger()
        #size = len(string)
        #pos = int(min(max(pos, 0), size))
        #subsize = len(substr)
        #endpos = pos+subsize
        #assert endpos >= 0
        #return W_IntNumber(string.rfind(substr, 0, endpos))

#class W_Substring(W_NewBuiltin):
    #length = 2
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #size = len(string)
        #if len(args) < 1:
            #start = 0
        #else:
            #start = args[0].ToInteger()
        #if len(args) < 2:
            #end = size
        #else:
            #end = args[1].ToInteger()
        #tmp1 = min(max(start, 0), size)
        #tmp2 = min(max(end, 0), size)
        #start = min(tmp1, tmp2)
        #end = max(tmp1, tmp2)
        #return W_String(string[start:end])

#class W_Split(W_NewBuiltin):
    #length = 2
    #def Call(self, args=[], this=None):
        #string = this.ToString()

        #if len(args) < 1 or args[0] is w_Undefined:
            #return create_array([W_String(string)])
        #else:
            #separator = args[0].ToString()

        #if len(args) >= 2:
            #limit = args[1].ToUInt32()
            #raise ThrowException(W_String("limit not implemented"))
            ## array = string.split(separator, limit)
        #else:
            #array = string.split(separator)

        #w_array = create_array()
        #i = 0
        #while i < len(array):
            #w_str = W_String(array[i])
            #w_array.Put(str(i), w_str)
            #i += 1

        #return w_array

#class W_ToLowerCase(W_NewBuiltin):
    #length = 0
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #return W_String(string.lower())

#class W_ToUpperCase(W_NewBuiltin):
    #length = 0
    #def Call(self, args=[], this=None):
        #string = this.ToString()
        #return W_String(string.upper())

#class W_ToString(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #assert isinstance(this, W_PrimitiveObject)
        #return W_String("[object %s]"%this.Class)

#class W_ValueOf(W_NewBuiltin):
    #length = 0
    #def Call(self, args=[], this=None):
        #return this

#class W_HasOwnProperty(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #if len(args) >= 1:
            #propname = args[0].ToString()
            #if propname in self._get_property_keys():
                #return newbool(True)
        #return newbool(False)

#class W_IsPrototypeOf(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #w_obj = args[0]
        #if len(args) >= 1 and isinstance(w_obj, W_PrimitiveObject):
            #O = this
            #assert isinstance(w_obj, W_PrimitiveObject)
            #V = w_obj.Prototype
            #while V is not None:
                #if O == V:
                    #return newbool(True)
                #assert isinstance(V, W_PrimitiveObject)
                #V = V.Prototype
        #return newbool(False)

#class W_PropertyIsEnumerable(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #if len(args) >= 1:
            #propname = args[0].ToString()
            #if self._has_property(propname) and not self._get_property_flags(propname) & DONT_ENUM:
                #return newbool(True)
        #return newbool(False)

#class W_Function(W_NewBuiltin):
    #def __init__(self, ctx, Prototype=None, Class='function', Value=w_Undefined):
        #W_NewBuiltin.__init__(self, Prototype, Class, Value)
        #self.ctx = ctx

    #def Call(self, args=[], this=None):
        #tam = len(args)
        #if tam >= 1:
            #fbody  = args[tam-1].ToString()
            #argslist = []
            #for i in range(tam-1):
                #argslist.append(args[i].ToString())
            #fargs = ','.join(argslist)
            #functioncode = "function (%s) {%s}"%(fargs, fbody)
        #else:
            #functioncode = "function () {}"
        ##remove program and sourcelements node
        #funcnode = parse(functioncode).children[0].children[0]
        #builder = make_ast_builder()
        #ast = builder.dispatch(funcnode)
        #bytecode = JsCode()
        #ast.emit(bytecode)
        #func = bytecode.make_js_function()
        #return func.run(self.ctx)

    #def Construct(self, args=[]):
        #return self.Call(args, this=None)

#functionstring= 'function (arguments go here!) {\n'+ \
                #'    [lots of stuff :)]\n'+ \
                #'}'
#class W_FToString(W_NewBuiltin):
    #def Call(self, args=[], this=None):
        #from js.jsobj import W__Function
        #if isinstance(this, W_PrimitiveObject):
            #if this.Class == 'Function':
                #return W_String(functionstring)
        #if isinstance(this, W__Function):
            #return W_String(functionstring)

        #raise JsTypeError('this is not a function object')

#class W_Apply(W_NewBuiltin):
    #def __init__(self, ctx):
        #W_NewBuiltin.__init__(self)
        #self.ctx = ctx

    #def Call(self, args=[], this=None):
        #try:
            #if isnull_or_undefined(args[0]):
                #thisArg = self.ctx.get_global()
            #else:
                #thisArg = args[0].ToObject()
        #except IndexError:
            #thisArg = self.ctx.get_global()

        #try:
            #arrayArgs = args[1]
            #callargs = arrayArgs.tolist()
        #except IndexError:
            #callargs = []
        #return this.Call(callargs, this=thisArg)

#class W_Call(W_NewBuiltin):
    #def __init__(self, ctx):
        #W_NewBuiltin.__init__(self)
        #self.ctx = ctx

    #def Call(self, args=[], this=None):
        #if len(args) >= 1:
            #if isnull_or_undefined(args[0]):
                #thisArg = self.ctx.get_global()
            #else:
                #thisArg = args[0]
            #callargs = args[1:]
        #else:
            #thisArg = self.ctx.get_global()
            #callargs = []
        #return this.Call(callargs, this = thisArg)

#class W_ValueToString(W_NewBuiltin):
    #"this is the toString function for objects with Value"
    #mytype = ''
    #def Call(self, args=[], this=None):
        #assert isinstance(this, W_PrimitiveObject)
        #if this.Value.type() != self.mytype:
            #raise JsTypeError('Wrong type')
        #return W_String(this.Value.ToString())

#class W_NumberValueToString(W_ValueToString):
    #mytype = 'number'

#class W_BooleanValueToString(W_ValueToString):
    #mytype = 'boolean'

#class W_StringValueToString(W_ValueToString):
    #mytype = 'string'

#class W_NativeObject(W_Object):
    #def __init__(self, Class, Prototype, Value=w_Undefined):
        #W_Object.__init__(self, Prototype, Class, Value)

#class W_DateObject(W_NativeObject):
    #def Call(self, args=[], this=None):
        #return create_object('Object')

    #def Construct(self, args=[]):
        #v = int(time.time()*1000)
        #return create_object('Date', Value = W_IntNumber(v))

def pypy_repr(this, *args):
    o = args[0]
    return W_String(repr(o))

#@specialize.memo()
#def get_value_of(type):
    #class W_ValueValueOf(W_NewBuiltin):
        #"this is the valueOf function for objects with Value"
        #def Call(self, args=[], this=None):
            #assert isinstance(this, W_PrimitiveObject)
            #if type != this.Class:
                #raise JsTypeError('%s.prototype.valueOf called with incompatible type' % self.type())
            #return this.Value
    #return W_ValueValueOf


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

def printjs(this, *args):
    writer(",".join([i.ToString() for i in args]))
    return w_Undefined

def noop(*args):
    return w_Undefined

def isnanjs(this, *args):
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

def versionjs(args, this):
    return w_Undefined

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
    strval = w_string.ToString()
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

#class W_ObjectObject(W_NativeObject):
    #def __init__(self, Class, Prototype, Value=w_Undefined):
        #W_NativeObject.__init__(self, Class, Prototype, Value)

    #def Call(self, args=[], this=None):
        #if len(args) >= 1 and not isnull_or_undefined(args[0]):
            #return args[0].ToObject()
        #else:
            #return self.Construct()

    #def Construct(self, args=[]):
        #if (len(args) >= 1 and not args[0] is w_Undefined and not args[0] is w_Null):
            ## XXX later we could separate builtins and normal objects
            #return args[0].ToObject()
        #return create_object('Object')

#class W_BooleanObject(W_NativeObject):
    #def Call(self, args=[], this=None):
        #if len(args) >= 1 and not isnull_or_undefined(args[0]):
            #return newbool(args[0].ToBoolean())
        #else:
            #return newbool(False)

    #def Construct(self, args=[]):
        #if len(args) >= 1 and not isnull_or_undefined(args[0]):
            #Value = newbool(args[0].ToBoolean())
            #return create_object('Boolean', Value = Value)
        #return create_object('Boolean', Value = newbool(False))

#class W_NumberObject(W_NativeObject):
    #def Call(self, args=[], this=None):
        #if len(args) >= 1 and not isnull_or_undefined(args[0]):
            #return W_FloatNumber(args[0].ToNumber())
        #elif len(args) >= 1 and args[0] is w_Undefined:
            #return W_FloatNumber(NAN)
        #else:
            #return W_FloatNumber(0.0)

    #def ToNumber(self):
        #return 0.0

    #def Construct(self, args=[]):
        #if len(args) >= 1 and not isnull_or_undefined(args[0]):
            #Value = W_FloatNumber(args[0].ToNumber())
            #return create_object('Number', Value = Value)
        #return create_object('Number', Value = W_FloatNumber(0.0))

#class W_StringObject(W_NativeObject):
    #length = 1
    #def Call(self, args=[], this=None):
        #if len(args) >= 1:
            #return W_String(args[0].ToString())
        #else:
            #return W_String('')

    #def Construct(self, args=[]):
        #if len(args) >= 1:
            #Value = W_String(args[0].ToString())
        #else:
            #Value = W_String('')
        #return Value.ToObject()

def create_array(elements=[]):
    # TODO do not get array prototype from global context?
    #proto = ctx.get_global().Get('Array').Get('prototype')
    #from js.builtins import get_builtin_prototype
    #proto = get_builtin_prototype('Array')
    #assert isinstance(proto, W_PrimitiveObject)
    array = W__Array()
    #i = 0
    while i < len(elements):
        array.Put(str(i), elements[i])
        i += 1

    return array

#class W_ArrayObject(W_NativeObject):
    #def __init__(self, Class, Prototype):
        #W_NativeObject.__init__(self, Class, Prototype, None )

    #def Call(self, args=[], this=None):
        #if len(args) == 1 and isinstance(args[0], W_Number):
            #array = create_array()
            #array.Put('length', args[0])
        #else:
            #array = create_array(args)
        #return array

    #def Construct(self, args=[]):
        #return self.Call(args)

_builtin_prototypes = {}
def get_builtin_prototype(name):
    p = _builtin_prototypes.get(name, None)
    if p is None:
        return _builtin_prototypes.get('Object', None)
    return p

def _register_builtin_prototype(name, obj):
    _builtin_prototypes[name] = obj

def new_native_function(ctx, function, name = None):
    from js.jscode import Js_NativeFunction
    from js.jsobj import W__Function
    return W__Function(ctx, Js_NativeFunction(function, name))

# 15.7.4.2
def number_to_string(this, *args):
    # TODO radix, see 15.7.4.2
    return this.ToString()

def setup_builtins(interp):
    def put_native_function(obj, name, func):
        obj.Put(name, new_native_function(ctx, func, name))

    allon = DONT_ENUM | DONT_DELETE | READ_ONLY
    from js.jsexecution_context import make_global_context

    ctx = make_global_context()
    w_Global = ctx.to_context_object()

    from js.jsobj import W_BasicObject, W__Object
    w_ObjectPrototype = W_BasicObject()
    W__Object._prototype_ = w_ObjectPrototype

    from js.jscode import Js_NativeFunction
    from js.jsobj import W__Function

    # 15.3.4
    import js.builtins_function as function_builtins
    w_FunctionPrototype = new_native_function(ctx, function_builtins.empty, 'Empty')
    w_FunctionPrototype._prototype_ = w_ObjectPrototype

    # 15.3.3.1
    W__Function._prototype_ = w_FunctionPrototype

    from js.jsobj import W_FunctionConstructor
    W_FunctionConstructor._prototype_ = w_FunctionPrototype

    w_Function = W_FunctionConstructor(ctx)
    w_Function.Put('constructor', w_Function, DONT_ENUM)

    w_Global.Put('Function', w_Function)

    from js.jsobj import W_ObjectConstructor
    # 15.2.3
    W_ObjectConstructor._prototype_ = w_FunctionPrototype
    w_Object = W_ObjectConstructor()

    # 15.2.3.1
    w_Object.Put('prototype', w_ObjectPrototype, flags = allon)
    w_Object.Put('length', _w(1), flags = allon)
    w_Global.Put('Object', w_Object)

    w_ObjectPrototype.Put('__proto__', w_Null)
    # 15.2.4.1
    w_ObjectPrototype.Put('constructor', w_Object)

    # 15.2.4.2
    import js.builtins_object as object_builtins
    put_native_function(w_Object, 'toString', object_builtins.to_string)
    put_native_function(w_Object, 'toLocaleString', object_builtins.to_string)
    put_native_function(w_Object, 'valueOf', object_builtins.value_of)

    #put_values(w_ObjPrototype, {
        #'constructor': w_Object,
        #'__proto__': w_Null,
        #'toString': toString,
        #'toLocaleString': toString,
        #'valueOf': W_ValueOf(),
        #'hasOwnProperty': W_HasOwnProperty(),
        #'isPrototypeOf': W_IsPrototypeOf(),
        #'propertyIsEnumerable': W_PropertyIsEnumerable(),
    #})

    #15.3.3.2
    w_Function.Put('length', _w(1), flags = allon)

    # 15.3.4.1
    w_FunctionPrototype.Put('constructor', w_Function)

    # 15.3.4.2
    import js.builtins_function as function_builtins
    put_native_function(w_FunctionPrototype, 'toString', function_builtins.to_string)


    ##properties of the function prototype
    #put_values(w_FncPrototype, {
        #'constructor': w_Function,
        #'__proto__': w_FncPrototype,
        #'toString': W_FToString(),
        #'apply': W_Apply(ctx),
        #'call': W_Call(ctx),
        #'arguments': w_Null,
        #'valueOf': W_ValueOf(),
    #})

    # 15.6.2
    from js.jsobj import W_BooleanConstructor
    w_Boolean = W_BooleanConstructor(ctx)
    w_Global.Put('Boolean', w_Boolean)

    # 15.6.4
    from js.jsobj import W_BooleanObject
    w_BooleanPrototype = W_BooleanObject(False)
    w_BooleanPrototype._prototype_ = W__Object._prototype_

    # 15.6.4.1
    w_BooleanPrototype.Put('constructor', w_Boolean)

    import js.builtins_boolean as boolean_builtins
    # 15.6.4.2
    put_native_function(w_BooleanPrototype, 'toString', boolean_builtins.to_string)

    # 15.6.3.1
    W_BooleanObject._prototype_ = w_BooleanPrototype

    #put_values(w_BoolPrototype, {
        #'constructor': w_FncPrototype,
        #'__proto__': w_ObjPrototype,
        #'toString': W_BooleanValueToString(),
        #'valueOf': get_value_of('Boolean')(),
    #})

    # 15.7.2
    from js.jsobj import W_NumberConstructor
    w_Number = W_NumberConstructor(ctx)
    w_Global.Put('Number', w_Number)

    # 15.7.4
    from js.jsobj import W_NumericObject
    w_NumberPrototype = W_NumericObject(0)
    w_NumberPrototype._prototype_ = W__Object._prototype_

    # 15.7.4.1
    w_NumberPrototype.Put('constructor', w_NumberPrototype)

    # 15.7.4.2
    w_NumberPrototype.Put('toString', new_native_function(ctx, number_to_string, 'toString'))

    # 15.7.3.1
    w_Number.Put('prototype', w_NumberPrototype)
    W_NumericObject._prototype_ = w_NumberPrototype

    # 15.7.3.2
    w_Number.Put('MAX_VALUE', _w(1.7976931348623157e308), flags = READ_ONLY | DONT_DELETE)

    # 15.7.3.3
    w_Number.Put('MIN_VALUE', _w(5e-320), flags = READ_ONLY | DONT_DELETE)

    # 15.7.3.4
    w_NAN = _w(NAN)
    w_Number.Put('NaN', w_NAN, flags = READ_ONLY | DONT_DELETE)

    # 15.7.3.5
    w_POSITIVE_INFINITY = _w(INFINITY)
    w_Number.Put('POSITIVE_INFINITY', w_POSITIVE_INFINITY, flags = READ_ONLY | DONT_DELETE)

    # 15.7.3.6
    w_NEGATIVE_INFINITY = _w(-INFINITY)
    w_Number.Put('NEGATIVE_INFINITY', w_NEGATIVE_INFINITY, flags = READ_ONLY | DONT_DELETE)

    #String
    # 15.5.1
    from js.jsobj import W_StringConstructor
    w_String = W_StringConstructor(ctx)
    w_Global.Put('String', w_String)

    # 15.5.4
    from js.jsobj import W_StringObject
    w_StringPrototype = W_StringObject('')
    w_StringPrototype._prototype_ = W__Object._prototype_

    # 15.5.3.1
    W_StringObject._prototype_ = w_StringPrototype

    # 15.5.4.1
    w_StringPrototype.Put('constructor', w_String)

    import js.builtins_string as string_builtins
    # 15.5.4.4
    put_native_function(w_StringPrototype, 'charAt', string_builtins.char_at)


    #put_values(w_StrPrototype, {
        #'constructor': w_String,
        #'__proto__': w_StrPrototype,
        #'toString': W_StringValueToString(),
        #'valueOf': get_value_of('String')(),
        #'charAt': W_CharAt(),
        #'charCodeAt': W_CharCodeAt(),
        #'concat': W_Concat(),
        #'indexOf': W_IndexOf(),
        #'lastIndexOf': W_LastIndexOf(),
        #'substring': W_Substring(),
        #'split': W_Split(),
        #'toLowerCase': W_ToLowerCase(),
        #'toUpperCase': W_ToUpperCase()
    #})
    #_register_builtin_prototype('String', w_StrPrototype)

    #w_String.Put('prototype', w_StrPrototype, flags=allon)
    #w_String.Put('fromCharCode', W_FromCharCode())
    #w_Global.Put('String', w_String)

    from js.jsobj import W_ArrayConstructor, W__Array
    w_Array = W_ArrayConstructor()
    w_Global.Put('Array', w_Array)

    # 15.4.4
    w_ArrayPrototype = W__Array()

    w_ArrayPrototype._prototype_ = W__Object._prototype_
    w_ArrayPrototype.Put('__proto__', w_ArrayPrototype._prototype_)

    # 15.4.3.1
    W__Array._prototype_ = w_ArrayPrototype

    # 15.4.4.1
    w_ArrayPrototype.Put('constructor', w_Array)

    import js.builtins_array as array_builtins
    # 15.4.4.2
    put_native_function(w_ArrayPrototype, 'toString', array_builtins.to_string)
    # 15.4.4.5
    put_native_function(w_ArrayPrototype, 'join', array_builtins.join)
    # 15.4.4.6
    put_native_function(w_ArrayPrototype, 'pop', array_builtins.pop)
    # 15.4.4.7
    put_native_function(w_ArrayPrototype, 'push', array_builtins.push)
    # 15.4.4.8
    put_native_function(w_ArrayPrototype, 'reverse', array_builtins.reverse)



    #Math
    from js.jsobj import W_Math
    # 15.8
    w_Math = W_Math()
    w_Global.Put('Math', w_Math)

    #w_math.Put('__proto__',  w_ObjPrototype)

    import js.builtins_math as math_builtins
    put_native_function(w_Math, 'abs', math_builtins.abs)
    put_native_function(w_Math, 'floor', math_builtins.floor)
    put_native_function(w_Math, 'round', math_builtins.round)
    put_native_function(w_Math, 'random', math_builtins.random)
    put_native_function(w_Math, 'min', math_builtins.min)
    put_native_function(w_Math, 'max', math_builtins.max)
    put_native_function(w_Math, 'pow', math_builtins.pow)
    put_native_function(w_Math, 'sqrt', math_builtins.sqrt)
    put_native_function(w_Math, 'log', math_builtins.log)

    # 15.8.1

    # 15.8.1.1
    w_Math.Put('E', _w(math_builtins.E), flags = allon)

    # 15.8.1.2
    w_Math.Put('LN10', _w(math_builtins.LN10), flags = allon)

    # 15.8.1.3
    w_Math.Put('LN2', _w(math_builtins.LN2), flags = allon)

    # 15.8.1.4
    w_Math.Put('LOG2E', _w(math_builtins.LOG2E), flags = allon)

    # 15.8.1.5
    w_Math.Put('LOG10E', _w(math_builtins.LOG10E), flags = allon)

    # 15.8.1.6
    w_Math.Put('PI', _w(math_builtins.PI), flags = allon)

    # 15.8.1.7
    w_Math.Put('SQRT1_2', _w(math_builtins.SQRT1_2), flags = allon)

    # 15.8.1.8
    w_Math.Put('SQRT2', _w(math_builtins.SQRT2), flags = allon)

    ##Date
    #w_Date = W_DateObject('Date', w_FncPrototype)

    #w_DatePrototype = create_object('Object', Value=W_String(''))
    #w_DatePrototype.Class = 'Date'

    #put_values(w_DatePrototype, {
        #'__proto__': w_DatePrototype,
        #'valueOf': get_value_of('Date')(),
        #'getTime': get_value_of('Date')()
    #})
    #_register_builtin_prototype('Date', w_DatePrototype)

    #w_Date.Put('prototype', w_DatePrototype, flags=allon)
    #w_Global.Put('Date', w_Date)

    # 15.1.1.1
    w_Global.Put('NaN', w_NAN, flags = DONT_ENUM | DONT_DELETE)

    # 15.1.1.2
    w_Global.Put('Infinity', w_POSITIVE_INFINITY, flags = DONT_ENUM | DONT_DELETE)

    # 15.1.1.3
    w_Global.Put('undefined', w_Undefined, flags = DONT_ENUM | DONT_DELETE)

    # 15.1.2.1
    w_Global.Put('eval', W__Eval(ctx))

    #w_Global.Put('parseInt', W_ParseInt())
    #w_Global.Put('parseFloat', W_ParseFloat())
    #w_Global.Put('isFinite', W_Builtin(isfinitejs))

    w_Global.Put('isNaN',new_native_function(ctx, isnanjs))
    w_Global.Put('print', new_native_function(ctx, printjs))

    #w_Global.Put('alert', W_Builtin(noop))
    #w_Global.Put('unescape', W_Builtin(unescapejs))

    w_Global.Put('this', w_Global)

    ## debugging
    if not we_are_translated():
        put_native_function(w_Global, 'pypy_repr', pypy_repr)

    put_native_function(w_Global, 'load', make_loadjs(interp))
    #w_Global.Put('load', W_Builtin(make_loadjs(interp)))

    #return (ctx, w_Global, w_Object)
    return (ctx, w_Global, None)

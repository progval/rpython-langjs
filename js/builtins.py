from js.jsobj import w_Undefined, W_IntNumber, w_Null, W_Boolean,\
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
from pypy.rlib.rfloat import NAN, INFINITY
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
    def f(this, args):
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

def new_native_function(function, name = None):
    from js.functions import JsNativeFunction
    from js.jsobj import W__Function

    scope = None
    jsfunc = JsNativeFunction(function, name)
    return W__Function(jsfunc, scope)

def setup_builtins(global_object):
    def put_native_function(obj, name, func, writable = False, configurable = False, enumerable = False):
        jsfunc = new_native_function(func, name)
        put_property(obj, name, jsfunc, writable = writable, configurable = configurable, enumerable = enumerable)

    # 15
    def put_property(obj, name, value, writable = True, configurable = False, enumerable = True):
        from js.jsobj import put_property as _put_property
        _put_property(obj, name, value, writable, configurable, enumerable)

    # Forward declaration
    # 15.2.3
    from js.jsobj import W_ObjectConstructor
    w_Object = W_ObjectConstructor()
    put_property(global_object, 'Object', w_Object)

    # 15.2.4
    from js.jsobj import W_BasicObject
    w_ObjectPrototype = W_BasicObject()

    # 15.3.2
    from js.jsobj import W_FunctionConstructor
    w_Function = W_FunctionConstructor()
    put_property(global_object, 'Function', w_Function)

    # 15.3.4
    import js.builtins_function as function_builtins
    w_FunctionPrototype = new_native_function(function_builtins.empty, 'Empty')

    # 15.2.4 Properties of the Object Prototype Object
    w_ObjectPrototype._prototype_ = w_Undefined

    # 15.3.4 Properties of the Function Prototype Object
    w_FunctionPrototype._prototype_ = w_ObjectPrototype

    # initial prototype
    from js.jsobj import W__Object, W__Function
    W__Object._prototype_ = w_ObjectPrototype
    W__Function._prototype_ = w_FunctionPrototype

    # 15.2 Object Objects
    # 15.2.3 Properties of the Object Constructor
    w_Object._prototype_ = w_FunctionPrototype

    put_property(w_Object, 'length', _w(1))

    # 15.2.3.1 Object.prototype
    put_property(w_Object, 'prototype', w_ObjectPrototype, writable = False, configurable = False, enumerable = False)

    # 14.2.4.1 Object.prototype.constructor
    put_property(w_ObjectPrototype, 'constructor', w_Object)

    import js.builtins_object as object_builtins
    # 15.2.4.2 Object.prototype.toString()
    put_native_function(w_ObjectPrototype, 'toString', object_builtins.to_string)
    put_native_function(w_ObjectPrototype, 'toLocaleString', object_builtins.to_string)

    # 15.2.4.3 Object.prototype.valueOf()
    put_native_function(w_ObjectPrototype, 'valueOf', object_builtins.value_of)

    # 15.3 Function Objects
    # 15.3.3 Properties of the Function Constructor

    # 15.3.3.1 Function.prototype
    put_property(w_Function, 'prototype', w_FunctionPrototype, writable = False, configurable = False, enumerable = False)

    # 15.3.3.2 Function.length
    put_property(w_Function, 'length', _w(1), writable = False, configurable = False, enumerable = False)

    # 14.3.4.1 Function.prototype.constructor
    put_property(w_FunctionPrototype, 'constructor', w_Function)

    # 15.3.4.2 Function.prototype.toString()
    import js.builtins_function as function_builtins
    put_native_function(w_FunctionPrototype, 'toString', function_builtins.to_string)

    # 15.3.4.3 Function.prototype.apply
    put_native_function(w_FunctionPrototype, 'apply', function_builtins.apply)

    # 15.3.4.4 Function.prototype.call
    put_native_function(w_FunctionPrototype, 'call', function_builtins.call)

    # 15.6.2
    from js.jsobj import W_BooleanConstructor
    w_Boolean = W_BooleanConstructor()
    put_property(global_object, 'Boolean', w_Boolean)

    # 15.6.3
    put_property(w_Boolean, 'length', _w(1), writable = False, enumerable = False, configurable = False)

    # 15.6.4
    from js.jsobj import W_BooleanObject
    w_BooleanPrototype = W_BooleanObject(False)
    w_BooleanPrototype._prototype_ = W__Object._prototype_

    # 15.6.3.1
    put_property(w_Boolean, 'prototype', w_BooleanPrototype, writable = False, enumerable = False, configurable = False)

    # 15.6.4.1
    put_property(w_BooleanPrototype, 'constructor', w_Boolean)

    import js.builtins_boolean as boolean_builtins
    # 15.6.4.2
    put_native_function(w_BooleanPrototype, 'toString', boolean_builtins.to_string)

    # 15.6.4.3
    put_native_function(w_BooleanPrototype, 'valueOf', boolean_builtins.value_of)

    # 15.6.3.1
    W_BooleanObject._prototype_ = w_BooleanPrototype

    # 15.7.2
    from js.jsobj import W_NumberConstructor
    w_Number = W_NumberConstructor()
    put_property(global_object, 'Number', w_Number)

    # 15.7.4
    from js.jsobj import W_NumericObject
    w_NumberPrototype = W_NumericObject(0)
    w_NumberPrototype._prototype_ = W__Object._prototype_

    # 15.7.4.1
    put_property(w_NumberPrototype, 'constructor', w_NumberPrototype)

    import js.builtins_number as number_builtins
    # 15.7.4.2
    put_native_function(w_NumberPrototype, 'toString', number_builtins.to_string)

    # 15.7.3.1
    put_property(w_Number, 'prototype', w_NumberPrototype)
    W_NumericObject._prototype_ = w_NumberPrototype

    # 15.7.3.2
    put_property(w_Number, 'MAX_VALUE', _w(1.7976931348623157e308), writable = False, configurable = False)

    # 15.7.3.3
    put_property(w_Number, 'MIN_VALUE', _w(5e-320), writable = False, configurable = False)

    # 15.7.3.4
    w_NAN = _w(NAN)
    put_property(w_Number, 'NaN', w_NAN, writable = False, configurable = False)

    # 15.7.3.5
    w_POSITIVE_INFINITY = _w(INFINITY)
    put_property(w_Number, 'POSITIVE_INFINITY', w_POSITIVE_INFINITY, writable = False, configurable = False)

    # 15.7.3.6
    w_NEGATIVE_INFINITY = _w(-INFINITY)
    put_property(w_Number, 'NEGATIVE_INFINITY', w_NEGATIVE_INFINITY, writable = False, configurable = False)

    #String
    # 15.5.1
    from js.jsobj import W_StringConstructor
    w_String = W_StringConstructor()
    put_property(global_object, 'String', w_String)

    import js.builtins_string as string_builtins
    # 15.5.3.2
    put_native_function(w_String, 'fromCharCode', string_builtins.from_char_code)

    # 15.5.4
    from js.jsobj import W_StringObject
    w_StringPrototype = W_StringObject('')
    w_StringPrototype._prototype_ = W__Object._prototype_

    # 15.5.3.1
    W_StringObject._prototype_ = w_StringPrototype

    # 15.5.4.1
    put_property(w_StringPrototype, 'constructor', w_String)

    # 15.5.4.4
    put_native_function(w_StringPrototype, 'charAt', string_builtins.char_at)

    # 15.5.4.5
    put_native_function(w_StringPrototype, 'charCodeAt', string_builtins.char_code_at)

    # 15.5.4.6
    put_native_function(w_StringPrototype, 'concat', string_builtins.concat)

    # 15.5.4.7
    put_native_function(w_StringPrototype, 'indexOf', string_builtins.index_of)

    # 15.5.4.8
    put_native_function(w_StringPrototype, 'lastIndexOf', string_builtins.last_index_of)

    # 15.5.4.14
    put_native_function(w_StringPrototype, 'split', string_builtins.split)

    # 15.5.4.15
    put_native_function(w_StringPrototype, 'substring', string_builtins.substring)

    # 15.5.4.16
    put_native_function(w_StringPrototype, 'toLowerCase', string_builtins.to_lower_case)

    # 15.5.4.18
    put_native_function(w_StringPrototype, 'toUpperCase', string_builtins.to_upper_case)

    from js.jsobj import W_ArrayConstructor, W__Array
    w_Array = W_ArrayConstructor()
    put_property(global_object, 'Array', w_Array)

    # 15.4.4
    w_ArrayPrototype = W__Array()

    w_ArrayPrototype._prototype_ = W__Object._prototype_
    put_property(w_ArrayPrototype, '__proto__', w_ArrayPrototype._prototype_)

    # 15.4.3.1
    W__Array._prototype_ = w_ArrayPrototype

    # 15.4.4.1
    put_property(w_ArrayPrototype, 'constructor', w_Array)

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
    put_property(global_object, 'Math', w_Math)

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
    put_property(w_Math, 'E', _w(math_builtins.E), writable = False, enumerable = False, configurable = False)

    # 15.8.1.2
    put_property(w_Math, 'LN10', _w(math_builtins.LN10), writable = False, enumerable = False, configurable = False)

    # 15.8.1.3
    put_property(w_Math, 'LN2', _w(math_builtins.LN2), writable = False, enumerable = False, configurable = False)

    # 15.8.1.4
    put_property(w_Math, 'LOG2E', _w(math_builtins.LOG2E), writable = False, enumerable = False, configurable = False)

    # 15.8.1.5
    put_property(w_Math, 'LOG10E', _w(math_builtins.LOG10E), writable = False, enumerable = False, configurable = False)

    # 15.8.1.6
    put_property(w_Math, 'PI', _w(math_builtins.PI), writable = False, enumerable = False, configurable = False)

    # 15.8.1.7
    put_property(w_Math, 'SQRT1_2', _w(math_builtins.SQRT1_2), writable = False, enumerable = False, configurable = False)

    # 15.8.1.8
    put_property(w_Math, 'SQRT2', _w(math_builtins.SQRT2), writable = False, enumerable = False, configurable = False)

    ##Date

    # 15.9.5
    from js.jsobj import W_DateObject, W_DateConstructor

    w_DatePrototype = W_DateObject(w_NAN)
    w_DatePrototype._prototype_ = W__Object._prototype_

    W_DateObject._prototype_ = w_DatePrototype

    import js.builtins_date as date_builtins
    # 15.9.5.9
    put_native_function(w_DatePrototype, 'getTime', date_builtins.get_time)

    # 15.9.3
    w_Date = W_DateConstructor()
    put_property(global_object, 'Date', w_Date)

    # 15.1.1.1
    put_property(global_object, 'NaN', w_NAN, enumerable = False, configurable = False)

    # 15.1.1.2
    put_property(global_object, 'Infinity', w_POSITIVE_INFINITY, enumerable = False, configurable = False)

    # 15.1.1.3
    put_property(global_object, 'undefined', w_Undefined, enumerable = False, configurable = False)

    # 15.1.2.1
    put_property(global_object, 'eval', W__Eval())

    import js.builtins_global as global_builtins

    # 15.1.2.2
    put_native_function(global_object, 'parseInt', global_builtins.parse_int)

    # 15.1.2.3
    put_native_function(global_object, 'parseFloat', global_builtins.parse_float)

    # 15.1.2.4
    put_native_function(global_object, 'isNaN', global_builtins.is_nan)

    # 15.1.2.5
    put_native_function(global_object, 'isFinite', global_builtins.is_finite)

    put_native_function(global_object, 'alert', global_builtins.alert)

    put_native_function(global_object, 'print', global_builtins.printjs)

    put_native_function(global_object, 'unescape', global_builtins.unescape)

    put_native_function(global_object, 'version', global_builtins.version)

    #put_property(global_object, 'this', global_object)

    ## debugging
    if not we_are_translated():
        put_native_function(global_object, 'pypy_repr', global_builtins.pypy_repr)
        put_native_function(global_object, 'inspect', global_builtins.inspect)

    #put_native_function(global_object, 'load', make_loadjs(interp))

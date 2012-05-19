from js.jsobj import w_Undefined, W_IntNumber, w_Null, W_Boolean,\
     W_FloatNumber, W_String, newbool, isnull_or_undefined, W_Number, _w
from js.execution import ThrowException, JsTypeError

from js.jsparser import parse, ParseError
from js.astbuilder import make_ast_builder, make_eval_ast_builder
from js.jscode import JsCode

from pypy.rlib.objectmodel import specialize
from pypy.rlib.listsort import TimSort
from pypy.rlib.rarithmetic import r_uint
from pypy.rlib.objectmodel import we_are_translated

from pypy.rlib import jit
from js.builtins_number import w_NAN
from js.builtins_number import w_POSITIVE_INFINITY

class Sorter(TimSort):
    def __init__(self, list, listlength=None, compare_fn=None):
        TimSort.__init__(self, list, listlength)
        self.compare_fn = compare_fn

    def lt(self, a, b):
        if self.compare_fn:
            result = self.compare_fn.Call([a, b]).ToInt32()
            return result == -1
        return a.ToString() < b.ToString()

def new_native_function(function, name = None, params = []):
    from js.functions import JsNativeFunction
    from js.jsobj import W__Function

    scope = None
    jsfunc = JsNativeFunction(function, name)
    return W__Function(jsfunc, formal_parameter_list = params)

# 15
def put_native_function(obj, name, func, writable = True, configurable = True, enumerable = False, params = []):
    jsfunc = new_native_function(func, name, params)
    put_property(obj, name, jsfunc, writable = writable, configurable = configurable, enumerable = enumerable)

# 15
def put_intimate_function(obj, name, func, writable = True, configurable = True, enumerable = False):
    from js.functions import JsIntimateFunction
    from js.jsobj import W__Function

    scope = None
    jsfunc = JsIntimateFunction(func, name)
    w_func = W__Function(jsfunc)
    put_property(obj, name, w_func, writable = writable, configurable = configurable, enumerable = enumerable)

# 15
def put_property(obj, name, value, writable = True, configurable = True, enumerable = False):
    from js.jsobj import put_property as _put_property
    _put_property(obj, name, value, writable, configurable, enumerable)

def setup_builtins(global_object):

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
    w_ObjectPrototype._prototype_ = w_Null

    # 15.3.4 Properties of the Function Prototype Object
    w_FunctionPrototype._prototype_ = w_ObjectPrototype

    # initial prototype
    from js.jsobj import W__Object, W__Function, W_BasicFunction
    W__Object._prototype_ = w_ObjectPrototype

    W__Function._prototype_ = w_FunctionPrototype
    W_BasicFunction._prototype_ = w_FunctionPrototype

    # 15.2 Object Objects
    # 15.2.3 Properties of the Object Constructor
    w_Object._prototype_ = w_FunctionPrototype
    del(w_Object._properties_['__proto__'])
    put_property(w_Object, '__proto__', w_Object._prototype_)

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

    import js.builtins_function as function_builtins

    # 15.3.4.2 Function.prototype.toString()
    put_native_function(w_FunctionPrototype, 'toString', function_builtins.to_string)

    # 15.3.4.3 Function.prototype.apply
    put_native_function(w_FunctionPrototype, 'apply', function_builtins.apply)

    # 15.3.4.4 Function.prototype.call
    put_intimate_function(w_FunctionPrototype, 'call', function_builtins.call)

    import js.builtins_boolean
    js.builtins_boolean.setup(global_object)

    import js.builtins_number
    js.builtins_number.setup(global_object)

    import js.builtins_string
    js.builtins_string.setup(global_object)

    import js.builtins_array
    js.builtins_array.setup(global_object)

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

    import js.builtins_date
    js.builtins_date.setup(global_object)

    # 15.1.1.1
    put_property(global_object, 'NaN', w_NAN, writable = False, enumerable = False, configurable = False)

    # 15.1.1.2
    put_property(global_object, 'Infinity', w_POSITIVE_INFINITY, writable = False, enumerable = False, configurable = False)

    # 15.1.1.3
    put_property(global_object, 'undefined', w_Undefined, writable = False, enumerable = False, configurable = False)

    import js.builtins_global as global_builtins

    # 15.1.2.1
    #put_property(global_object, 'eval', W__Eval())
    put_intimate_function(global_object, 'eval', global_builtins.js_eval)

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

    #put_intimate_function(global_object, 'load', global_builtins.js_load)

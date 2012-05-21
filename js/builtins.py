from js.jsobj import w_Undefined, W_IntNumber, w_Null, W_Boolean,\
     W_FloatNumber, W_String, newbool, isnull_or_undefined, W_Number, _w
from js.execution import ThrowException, JsTypeError

from js.jsparser import parse, ParseError
from js.astbuilder import make_ast_builder, make_eval_ast_builder
from js.jscode import JsCode

from pypy.rlib.objectmodel import specialize
from pypy.rlib.listsort import TimSort
from pypy.rlib.rarithmetic import r_uint

from pypy.rlib import jit

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
def put_intimate_function(obj, name, func, writable = True, configurable = True, enumerable = False, params = []):
    from js.functions import JsIntimateFunction
    from js.jsobj import W__Function

    scope = None
    jsfunc = JsIntimateFunction(func, name)
    w_func = W__Function(jsfunc, formal_parameter_list = params)
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
    #w_Object._prototype_ = w_FunctionPrototype
    #del(w_Object._properties_['__proto__'])
    #put_property(w_Object, '__proto__', w_Object._prototype_)

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
    import js.builtins_math
    js.builtins_math.setup(global_object)

    import js.builtins_date
    js.builtins_date.setup(global_object)

    import js.builtins_global
    js.builtins_global.setup(global_object)

def get_arg(args, index, default = w_Undefined):
    if len(args) > index:
        return args[index]
    return default

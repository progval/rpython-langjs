from js.object_space import _w

#from pypy.rlib import jit


def new_native_function(function, name=u'', params=[]):
    from js.functions import JsNativeFunction
    from js.object_space import object_space

    jsfunc = JsNativeFunction(function, name)
    obj = object_space.new_func(jsfunc, formal_parameter_list=params)
    return obj


# 15
def put_native_function(obj, name, func, writable=True, configurable=True, enumerable=False, params=[]):
    jsfunc = new_native_function(func, name, params)
    put_property(obj, name, jsfunc, writable=writable, configurable=configurable, enumerable=enumerable)


# 15
def put_intimate_function(obj, name, func, writable=True, configurable=True, enumerable=False, params=[]):
    from js.functions import JsIntimateFunction
    from js.object_space import object_space

    jsfunc = JsIntimateFunction(func, name)
    w_func = object_space.new_func(jsfunc, formal_parameter_list=params)
    put_property(obj, name, w_func, writable=writable, configurable=configurable, enumerable=enumerable)


# 15
def put_property(obj, name, value, writable=True, configurable=True, enumerable=False):
    from js.jsobj import put_property as _put_property
    _put_property(obj, name, value, writable, configurable, enumerable)


def setup_builtins(global_object):
    from js.object_space import object_space

    # 15.2.4 Properties of the Object Prototype Object
    from js.jsobj import W_BasicObject
    w_ObjectPrototype = W_BasicObject()
    object_space.proto_object = w_ObjectPrototype

    # 15.3.2
    from js.jsobj import W_FunctionConstructor
    w_Function = W_FunctionConstructor()
    put_property(global_object, u'Function', w_Function)

    # 15.3.4 Properties of the Function Prototype Object
    from js.functions import JsNativeFunction

    import js.builtins.function
    empty_func = JsNativeFunction(js.builtins.function.empty, u'Empty')
    w_FunctionPrototype = object_space.new_func(empty_func)
    object_space.assign_proto(w_FunctionPrototype, object_space.proto_object)
    object_space.proto_function = w_FunctionPrototype

    # 15.3.3
    object_space.assign_proto(w_Function, object_space.proto_function)

    # 15.2 Object Objects
    # 15.2.3 Properties of the Object Constructor
    from js.jsobj import W_ObjectConstructor
    w_Object = W_ObjectConstructor()
    object_space.assign_proto(w_Object, object_space.proto_function)

    put_property(w_Object, u'length', _w(1))

    put_property(global_object, u'Object', w_Object)

    # 15.2.3.1 Object.prototype
    put_property(w_Object, u'prototype', w_ObjectPrototype, writable=False, configurable=False, enumerable=False)

    # 14.2.4.1 Object.prototype.constructor
    put_property(w_ObjectPrototype, u'constructor', w_Object)

    import js.builtins.object
    # 15.2.4.2 Object.prototype.toString()
    put_native_function(w_ObjectPrototype, u'toString', js.builtins.object.to_string)
    put_native_function(w_ObjectPrototype, u'toLocaleString', js.builtins.object.to_string)

    # 15.2.4.3 Object.prototype.valueOf()
    put_native_function(w_ObjectPrototype, u'valueOf', js.builtins.object.value_of)

    # 15.3 Function Objects
    # 15.3.3 Properties of the Function Constructor

    # 15.3.3.1 Function.prototype
    put_property(w_Function, u'prototype', w_FunctionPrototype, writable=False, configurable=False, enumerable=False)

    # 15.3.3.2 Function.length
    put_property(w_Function, u'length', _w(1), writable=False, configurable=False, enumerable=False)

    # 14.3.4.1 Function.prototype.constructor
    put_property(w_FunctionPrototype, u'constructor', w_Function)

    # 15.3.4.2 Function.prototype.toString()
    put_native_function(w_FunctionPrototype, u'toString', js.builtins.function.to_string)

    # 15.3.4.3 Function.prototype.apply
    put_intimate_function(w_FunctionPrototype, u'apply', js.builtins.function.js_apply)

    # 15.3.4.4 Function.prototype.call
    put_intimate_function(w_FunctionPrototype, u'call', js.builtins.function.js_call)

    import js.builtins.boolean
    js.builtins.boolean.setup(global_object)

    import js.builtins.number
    js.builtins.number.setup(global_object)

    import js.builtins.string
    js.builtins.string.setup(global_object)

    import js.builtins.array
    js.builtins.array.setup(global_object)

    import js.builtins.js_math
    js.builtins.js_math.setup(global_object)

    import js.builtins.date
    js.builtins.date.setup(global_object)

    import js.builtins.js_global
    js.builtins.js_global.setup(global_object)


from js.object_space import newundefined


def get_arg(args, index, default=newundefined()):
    if len(args) > index:
        return args[index]
    return default

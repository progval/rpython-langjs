from pypy.rlib.objectmodel import specialize


@specialize.argtype(0)
def _w(value):
    from js.jsobj import w_Null, newbool, W_IntNumber, W_FloatNumber, W_String, W_Root, put_property
    if value is None:
        return w_Null
    elif isinstance(value, W_Root):
        return value
    elif isinstance(value, bool):
        return newbool(value)
    elif isinstance(value, int):
        return W_IntNumber(value)
    elif isinstance(value, float):
        return W_FloatNumber(value)
    elif isinstance(value, unicode):
        return W_String(value)
    elif isinstance(value, str):
        u_str = unicode(value)
        return W_String(u_str)
    elif isinstance(value, list):
        a = object_space.new_array()
        for index, item in enumerate(value):
            put_property(a, unicode(str(index)), _w(item), writable=True, enumerable=True, configurable=True)
        return a

    raise TypeError("ffffuuu %s" % (value,))


class ObjectSpace(object):
    def __init__(self):
        from js.jsobj import w_Null
        self.global_context = None
        self.global_object = None
        self.proto_function = w_Null
        self.proto_boolean = w_Null
        self.proto_number = w_Null
        self.proto_string = w_Null
        self.proto_array = w_Null
        self.proto_date = w_Null
        self.proto_object = w_Null
        self.interpreter = None

    def get_global_environment(self):
        return self.global_context.variable_environment()

    def assign_proto(self, obj, proto=None):
        from js.jsobj import W_BasicFunction, W_DateObject, W_BooleanObject, W_StringObject, W_NumericObject, W__Array
        if proto is not None:
            obj._prototype_ = proto
            return obj

        if isinstance(obj, W_BasicFunction):
            obj._prototype_ = self.proto_function
        elif isinstance(obj, W_BooleanObject):
            obj._prototype_ = self.proto_boolean
        elif isinstance(obj, W_NumericObject):
            obj._prototype_ = self.proto_number
        elif isinstance(obj, W_StringObject):
            obj._prototype_ = self.proto_string
        elif isinstance(obj, W__Array):
            obj._prototype_ = self.proto_array
        elif isinstance(obj, W_DateObject):
            obj._prototype_ = self.proto_date
        else:
            obj._prototype_ = self.proto_object
        return obj

    def new_obj(self):
        from js.jsobj import W__Object
        obj = W__Object()
        self.assign_proto(obj)
        return obj

    def new_func(self, function_body, formal_parameter_list=[], scope=None, strict=False):
        from js.jsobj import W__Function
        obj = W__Function(function_body, formal_parameter_list, scope, strict)
        self.assign_proto(obj)
        return obj

    def new_date(self, value):
        from js.jsobj import W_DateObject
        obj = W_DateObject(value)
        self.assign_proto(obj)
        return obj

    def new_array(self, length=_w(0)):
        from js.jsobj import W__Array
        obj = W__Array(length)
        self.assign_proto(obj)
        return obj

    def new_bool(self, value):
        from js.jsobj import W_BooleanObject
        obj = W_BooleanObject(value)
        self.assign_proto(obj)
        return obj

    def new_string(self, value):
        from js.jsobj import W_StringObject
        obj = W_StringObject(value)
        self.assign_proto(obj)
        return obj

    def new_number(self, value):
        from js.jsobj import W_NumericObject
        obj = W_NumericObject(value)
        self.assign_proto(obj)
        return obj


object_space = ObjectSpace()


def w_return(fn):
    def f(*args):
        return _w(fn(*args))
    return f


def hide_on_translate(*args):
    default = None

    def _wrap(f):
        def _wrapped_f(*args):
            from pypy.rlib.objectmodel import we_are_translated
            if not we_are_translated():
                return f(*args)

            return default
        return _wrapped_f

    if len(args) == 1 and callable(args[0]):
        return _wrap(args[0])
    else:
        default = args[0]
        return _wrap

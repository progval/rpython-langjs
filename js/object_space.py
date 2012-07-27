from js.jsobj import _w, W_BasicObject, W__Object, W_BasicFunction, W__Function, W_DateObject, W_BooleanObject, W_StringObject, W_NumericObject, W__Array, w_Null

class ObjectSpace(object):
    def __init__(self):
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
        self.DEBUG = False

    def get_global_environment(self):
        return self.global_context.variable_environment()

    def assign_proto(self, obj, proto = None):
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
        obj = W__Object()
        self.assign_proto(obj)
        return obj

    def new_func(self, function_body, formal_parameter_list=[], scope=None, strict=False):
        obj = W__Function(function_body, formal_parameter_list, scope, strict)
        self.assign_proto(obj)
        return obj

    def new_date(self, value):
        obj = W_DateObject(value)
        self.assign_proto(obj)
        return obj

    def new_array(self, length = _w(0)):
        obj = W__Array(length)
        self.assign_proto(obj)
        return obj

    def new_bool(self, value):
        obj = W_BooleanObject(value)
        self.assign_proto(obj)
        return obj

    def new_string(self, value):
        obj = W_StringObject(value)
        self.assign_proto(obj)
        return obj

    def new_number(self, value):
        obj = W_NumericObject(value)
        self.assign_proto(obj)
        return obj

object_space = ObjectSpace()

def w_return(fn):
    def f(*args):
        from js.jsobj import _w
        return _w(fn(*args))
    return f

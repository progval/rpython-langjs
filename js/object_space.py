class ObjectSpace(object):
    def get_global_object(self):
        return self.global_object

    def get_global_environment(self):
        return self.global_context.variable_environment()

    def new_obj_with_proto(self, cls, proto, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj._prototype_ = proto
        return obj

    def new_obj(self, cls, *args, **kwargs):
        from js.jsobj import W_BasicFunction, W_BooleanObject, W_StringObject, W_NumericObject, W_DateObject, W__Array
        obj = cls(*args, **kwargs)

        if issubclass(cls, W_BasicFunction):
            obj._prototype_ = self.proto_function
        elif issubclass(cls, W_BooleanObject):
            obj._prototype_ = self.proto_boolean
        elif issubclass(cls, W_StringObject):
            obj._prototype_ = self.proto_string
        elif issubclass(cls, W_NumericObject):
            obj._prototype_ = self.proto_number
        elif issubclass(cls, W_DateObject):
            obj._prototype_ = self.proto_date
        elif issubclass(cls, W__Array):
            obj._prototype_ = self.proto_array
        else:
            obj._prototype_ = self.proto_object

        return obj

object_space = ObjectSpace()

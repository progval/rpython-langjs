from js.utils import StackMixin, MapMixin, MapDictMixin, DynamicMapDictMixin
from js.jsobj import DONT_DELETE

class JSContext(MapMixin, MapDictMixin):
    def __init__(self, parent=None):
        self._init_js_context(parent)

    def _init_js_context(self, parent=None):
        self._init_map_dict(0)
        self.parent = parent
        self.ctx_obj = None

    def resolve_identifier(self, ctx, identifier):
        try:
            return self.get_property_value(identifier)
        except KeyError:
            from js.jsobj import W_String
            from js.execution import ThrowException
            raise ThrowException(W_String("ReferenceError: %s is not defined" % identifier))

    def get_property_value(self, name):
        return self._get_property(name).value

    def get_property_flags(self, name):
        return self._get_property(name).flags

    def _get_property(self,name):
        from js.jsobj import Property
        p = self._identifier_get(name)
        assert isinstance(p, Property)
        return p

    def assign(self, name, value):
        from js.jsobj import RO, Property
        assert name is not None
        try:
            p = self._get_property(name)
            if p.flags & RO:
                return
            p.value = value
        except KeyError:
            self.get_global_context().put(name, value, flags=0)

    def declare_variable(self, identifier, flags=DONT_DELETE):
        from js.jsobj import w_Undefined, Property
        self._map_addname(identifier)
        p = Property(identifier, w_Undefined, flags)
        self._identifier_set_local(identifier, p)

    def get_local_value(self, idx):
        val = self._map_dict_getindex(idx)
        if val is None:
            raise KeyError
        return val.value

    def _identifier_set_local(self, identifier, value):
        self._map_dict_set(identifier, value)

    def _identifier_get_local(self, identifier):
        return self._map_dict_get(identifier)

    def _identifier_is_local(self, identifier):
        return self._map_indexof(identifier) != self._MAP_NOT_FOUND

    def _identifier_set(self, identifier, value):
        try:
            self._identifier_set_if_local(identifier, value)
        except KeyError:
            self._identifier_set_local(identifier, value)

    def _identifier_set_if_local(self, identifier, value):
        if self._identifier_is_local(identifier):
            self._identifier_set_local(identifier, value)
            return
        elif self.parent:
            self.parent._identifier_set_if_local(identifier, value)
            return
        raise KeyError

    def _identifier_get(self, identifier):
        try:
            return self._identifier_get_local(identifier)
        except KeyError:
            if self.parent:
                return self.parent._identifier_get(identifier)
        raise KeyError

    def assign_local(self, idx, value):
        prop = self._map_dict_getindex(idx)
        prop.value = value

    def get_global(self):
        return self.get_global_context().to_context_object()

    def get_global_context(self):
        if self.parent:
            return self.parent.get_global_context()
        else:
            return self

    def to_context_object(self):
        from jsobj import W_ContextObject
        return W_ContextObject(self)

    def put(self, name, value, flags=DONT_DELETE):
        self.declare_variable(name, flags)
        self.assign(name, value)

    def delete_identifier(self, name):
        self._map_dict_delete(name)
        return True

class ActivationContext(JSContext):
    def __init__(self, parent, this, args):
        self._init_acitvation_context(parent, this, args)

    def _init_acitvation_context(self, parent, this, args):
        self._init_js_context(parent)
        self._map_dict_values_init_with_size(2)

        if this is not None:
            self.put('this', this)

        self.put('arguments', args)

class ExecutionContext(JSContext, StackMixin):
    #_virtualizable2_ = ['stack[*]', 'stack_pointer', '_map_dict_values[*]', '_map_next_index']
    def __init__(self, parent=None):
        self._init_execution_context(parent)

    def _init_execution_context(self, parent):
        self._init_js_context(parent)
        self._init_stack()

class GlobalContext(DynamicMapDictMixin, ExecutionContext):
    def __init__(self, parent=None):
        self._init_global_context(parent)

    def _init_global_context(self, parent):
        self._init_execution_context(parent)
        # TODO size of gloabl context
        self._init_dynamic_map_dict()

class WithExecutionContext(ExecutionContext):
    def __init__(self, parent, obj):
        self._init_with_execution_context(parent, obj)

    def _init_with_execution_context(self, parent, obj):
        self._init_execution_context(parent)
        self.ctx_obj = obj
        self.stack = parent.stack
        self.stack_pointer = parent.stack_pointer

    def resolve_identifier(self, ctx, identifier):
        if self.ctx_obj.HasProperty(identifier):
            return self.ctx_obj.Get(ctx, identifier);
        return ExecutionContext.resolve_identifier(self, ctx, identifier)

class FunctionContext(ExecutionContext):
    def __init__(self, parent, func):
        self._init_function_context(parent, func)

    def _init_function_context(self, parent, func):
        self._init_execution_context(parent)
        if func.scope:
            self._init_map_dict_with_map(func.scope.local_variables)

class CatchContext(ExecutionContext):
    def __init__(self, parent, param, exception):
        self._init_catch_context(parent, param, exception)

    def _init_catch_context(self, parent, param, exception):
        self._init_execution_context(parent)
        self._map_dict_values_init_with_size(1)
        self.put(param, exception)

from js.utils import StackMixin, MapMixin, MapDictMixin
from js.jsobj import DONT_DELETE

from pypy.rlib import jit, debug

class ExecutionContext(MapDictMixin, MapMixin, StackMixin):
    _virtualizable2_ = ['stack[*]', 'stack_pointer', '_map_dict_values[*]', '_map_next_index']
    def __init__(self, parent=None):
        self._init_execution_context(parent)

    def resolve_identifier(self, ctx, identifier):
        if self.ctx_obj is not None and self.ctx_obj.HasProperty(identifier):
            return self.ctx_obj.Get(ctx, identifier);

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

    def _init_execution_context(self, parent):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self._init_map_dict(0)
        self.parent = parent
        self.ctx_obj = None
        self._init_stack()

    def _init_function_context(self, parent, func):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self._init_execution_context(parent)
        if func.scope:
            self._init_map_dict_with_map(func.scope.local_variables)

    def _init_acitvation_context(self, parent, this, args):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self._init_execution_context(parent)
        self._map_dict_values_init_with_size(2)

        if this is not None:
            self.put('this', this)

        self.put('arguments', args)

    def _init_catch_context(self, parent, param, exception):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self._init_execution_context(parent)
        self._map_dict_values_init_with_size(1)
        self.put(param, exception)

    def _init_with_execution_context(self, parent, obj):
        self = jit.hint(self, access_directly=True, fresh_virtualizable=True)
        self._init_execution_context(parent)
        self.ctx_obj = obj
        self._init_stack(len(parent.stack))

    def _init_global_context(self):
        self._init_execution_context(None)
        # TODO size of gloabl context
        self._init_dynamic_map_dict()

def make_activation_context(parent, this, args):
    ctx = ExecutionContext()
    ctx._init_acitvation_context(parent, this, args)
    return ctx

def make_global_context():
    ctx = ExecutionContext()
    ctx._init_global_context()
    return ctx

def make_with_context(parent, obj):
    ctx = ExecutionContext()
    ctx._init_with_execution_context(parent, obj)
    return ctx

def make_function_context(parent, func):
    ctx = ExecutionContext()
    ctx._init_function_context(parent, func)
    return ctx

def make_catch_context(parent, param, exception):
    ctx = ExecutionContext()
    ctx._init_catch_context(parent, param, exception)
    return ctx

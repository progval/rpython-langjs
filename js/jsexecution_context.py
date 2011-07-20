from js.jsobj import RO, Property
from js.utils import MapDict

class ExecutionContext(object):
    def __init__(self, parent=None):
        self.values = MapDict()
        self.parent = parent

    def resolve_identifier(self, ctx, identifier):
        try:
            p = self._identifier_get(identifier)
            assert isinstance(p, Property)
            return p.value
        except KeyError:
            from js.jsobj import W_String
            from js.execution import ThrowException
            raise ThrowException(W_String("ReferenceError: %s is not defined" % identifier))

    def assign(self, name, value):
        assert name is not None
        try:
            p = self._identifier_get(name)
            assert isinstance(p, Property)
            if p.flags & RO:
                return
            p.value = value
        except KeyError:
            p = Property(identifier, value)
            self._identifier_set(identifier, p)

    def declare_variable(self, identifier):
        from js.jsobj import w_Undefined, DD
        self.values.addname(identifier)
        p = Property(identifier, w_Undefined, flags = DD)
        self._identifier_set_local(identifier, p)

    def _identifier_set_local(self, identifier, value):
        self.values.set(identifier, value)

    def _identifier_get_local(self, identifier):
        return self.values.get(identifier)

    def _identifier_is_local(self, identifier):
        return self.values.indexof(identifier) != self.values.NOT_FOUND

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

from js.object_map import new_map


class EnvironmentRecord(object):
    def __init__(self):
        pass

    def has_binding(self, identifier):
        return False

    def create_mutuable_binding(self, identifier, deletable):
        raise NotImplementedError

    def set_mutable_binding(self, identifier, value, strict):
        raise NotImplementedError

    def get_binding_value(self, identifier, strict=False):
        raise NotImplementedError

    def delete_binding(self, identifier):
        raise NotImplementedError

    def implicit_this_value(self):
        raise NotImplementedError


class DeclarativeEnvironmentRecord(EnvironmentRecord):
    _immutable_fields_ = ['_binding_slots_', '_binding_resize_']

    def __init__(self, size=0, resize=True):
        EnvironmentRecord.__init__(self)
        self._binding_map_ = new_map()
        self._binding_slots_ = [None] * size
        self._binding_resize_ = resize
        self._mutable_bindings_map_ = new_map()
        self._deletable_bindings_map_ = new_map()

    def _is_mutable_binding(self, identifier):
        return self._mutable_bindings_map_.contains(identifier)

    def _set_mutable_binding(self, identifier):
        self._mutable_bindings_map_ = self._mutable_bindings_map_.add(identifier)

    def _is_deletable_binding(self, identifier):
        return self._deletable_bindings_map_.contains(identifier)

    def _set_deletable_binding(self, identifier):
        self._deletable_bindings_ = self._deletable_bindings_map_.add(identifier)

    # 10.2.1.1.1
    def has_binding(self, identifier):
        return self._binding_map_.contains(identifier)

    def _get_binding(self, name):
        idx = self._binding_map_.lookup(name)
        binding = self._binding_slots_[idx]
        return binding

    def _add_binding(self, name, value):
        idx = self._binding_map_.lookup(name)

        if self._binding_map_.not_found(idx):
            self._binding_map_ = self._binding_map_.add(name)
            idx = self._binding_map_.index

        if self._binding_resize_ is True:
            if idx >= len(self._binding_slots_):
                self._binding_slots_ += ([None] * (1 + idx - len(self._binding_slots_)))

        self._binding_slots_[idx] = value

    def _set_binding(self, name, value):
        idx = self._binding_map_.lookup(name)
        self._binding_slots_[idx] = value

    def _del_binding(self, name):
        idx = self._binding_map_.lookup(name)

        if self._binding_map_.not_found(idx):
            return

        assert idx >= 0
        i = (idx + 1)
        assert i >= 0

        self._binding_slots_ = self._binding_slots_[:idx] + self._binding_slots_[i:]  # len(self._binding_slots_)]
        self._binding_map_ = self._binding_map_.delete(name)

    # 10.2.1.1.2
    def create_mutuable_binding(self, identifier, deletable):
        from js.object_space import newundefined
        assert identifier is not None and isinstance(identifier, unicode)
        assert not self.has_binding(identifier)
        self._add_binding(identifier, newundefined())
        self._set_mutable_binding(identifier)
        if deletable:
            self._set_deletable_binding(identifier)

    # 10.2.1.1.3
    def set_mutable_binding(self, identifier, value, strict):
        assert identifier is not None and isinstance(identifier, unicode)
        assert self.has_binding(identifier)
        if not self._is_mutable_binding(identifier):
            from js.exception import JsTypeError
            raise JsTypeError(u'immutable binding')
        self._set_binding(identifier, value)

    # 10.2.1.1.4
    def get_binding_value(self, identifier, strict=False):
        from js.object_space import newundefined
        assert identifier is not None and isinstance(identifier, unicode)
        if not self.has_binding(identifier):
            if strict:
                from js.exception import JsReferenceError
                raise JsReferenceError(identifier)
            else:
                return newundefined()
        return self._get_binding(identifier)

    # 10.2.1.1.5
    def delete_binding(self, identifier):
        assert identifier is not None and isinstance(identifier, unicode)
        if not self.has_binding(identifier):
            return True
        if self._is_mutable_binding(identifier) is False:
            return False
        if self._is_deletable_binding(identifier) is False:
            return False
        self._deletable_bindings_map_ = self._deletable_bindings_map_.delete(identifier)
        self._mutable_bindings_map_ = self._mutable_bindings_map_.delete(identifier)
        self._del_binding(identifier)
        return False

    # 10.2.1.1.6
    def implicit_this_value(self):
        from js.object_space import newundefined
        return newundefined()

    # 10.2.1.1.7
    def create_immutable_bining(self, identifier):
        raise NotImplementedError(self.__class__)

    def initialize_immutable_binding(self, identifier, value):
        raise NotImplementedError(self.__class__)


class ObjectEnvironmentRecord(EnvironmentRecord):
    _immutable_fields_ = ['binding_object']

    provide_this = False

    def __init__(self, obj, provide_this=False):
        self.binding_object = obj
        if provide_this is True:
            self.provide_this = True

    # 10.2.1.2.1
    def has_binding(self, n):
        assert n is not None and isinstance(n, unicode)
        bindings = self.binding_object
        return bindings.has_property(n)

    # 10.2.1.2.2
    def create_mutuable_binding(self, n, d):
        assert n is not None and isinstance(n, unicode)
        bindings = self.binding_object
        assert bindings.has_property(n) is False
        if d is True:
            config_value = False
        else:
            config_value = True

        from js.jsobj import PropertyDescriptor
        from js.object_space import newundefined
        desc = PropertyDescriptor(value=newundefined(), writable=True, enumerable=True, configurable=config_value)
        bindings.define_own_property(n, desc, True)

    # 10.2.1.2.3
    def set_mutable_binding(self, n, v, s):
        assert n is not None and isinstance(n, unicode)
        bindings = self.binding_object
        bindings.put(n, v, s)

    # 10.2.1.2.4
    def get_binding_value(self, n, s=False):
        from js.object_space import newundefined
        assert n is not None and isinstance(n, unicode)
        bindings = self.binding_object
        value = bindings.has_property(n)
        if value is False:
            if s is False:
                return newundefined()
            else:
                from js.exception import JsReferenceError
                raise JsReferenceError(self.__class__)

        return bindings.get(n)

    # 10.2.1.2.5
    def delete_binding(self, n):
        assert n is not None and isinstance(n, unicode)
        bindings = self.binding_object
        return bindings.delete(n, False)

    # 10.2.1.2.6
    def implicit_this_value(self):
        from js.object_space import newundefined
        if self.provide_this is True:
            return self.binding_object
        return newundefined()


class GlobalEnvironmentRecord(ObjectEnvironmentRecord):
    pass

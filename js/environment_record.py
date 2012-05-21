from js.jsobj import w_Undefined

class EnvironmentRecord(object):
    def __init__(self):
        pass

    def has_binding(self, identifier):
        return False

    def create_mutuable_binding(self, identifier, deletable):
        pass

    def set_mutable_binding(self, identifier, value, strict=False):
        pass

    def get_binding_value(self, identifier, strict=False):
        pass

    def delete_binding(self, identifier):
        pass

    def implicit_this_value(self):
        pass

class DeclarativeEnvironmentRecord(EnvironmentRecord):
    def __init__(self):
        EnvironmentRecord.__init__(self)
        self.bindings = {}
        self.mutable_bindings = {}
        self.deletable_bindings = {}

    def _is_mutable_binding(self, identifier):
        return self.mutable_bindings.get(identifier, False) == True

    def _set_mutable_binding(self, identifier):
        self.mutable_bindings[identifier] = True

    def _is_deletable_binding(self, identifier):
        return self.deletable_bindings.get(identifier, False) == True

    def _set_deletable_binding(self, identifier):
        self.deletable_bindings[identifier] = True

    # 10.2.1.1.1
    def has_binding(self, identifier):
        return self.bindings.has_key(identifier)

    # 10.2.1.1.2
    def create_mutuable_binding(self, identifier, deletable):
        assert not self.has_binding(identifier)
        self.bindings[identifier] = w_Undefined
        self._set_mutable_binding(identifier)
        if deletable:
            self._set_deletable_binding(identifier)

    # 10.2.1.1.3
    def set_mutable_binding(self, identifier, value, strict=False):
        assert self.has_binding(identifier)
        if not self._is_mutable_binding(identifier):
            raise JsTypeError('immutable binding')
        self.bindings[identifier] = value

    # 10.2.1.1.4
    def get_binding_value(self, identifier, strict=False):
        assert self.has_binding(identifier)
        if not identifier in self.bindings:
            if strict:
                raise JsReferenceError
            else:
                return w_Undefined
        return self.bindings.get(identifier)

    # 10.2.1.1.5
    def delete_binding(self, identifier):
        if not self.has_binding(identifier):
            return True
        if self._is_mutable_binding(identifier) is False:
            return False
        if self._is_deletable_binding(identifier) is False:
            return False
        del(self.delete_binding[identifier])
        del(self.mutable_bindings[identifier])
        del(self.bindings[identifier])
        return False

    # 10.2.1.1.6
    def implicit_this_value(self):
        return w_Undefined

    # 10.2.1.1.7
    def create_immutable_bining(self, identifier):
        raise NotImplementedError(self.__class__)

    def initialize_immutable_binding(self, identifier, value):
        raise NotImplementedError(self.__class__)

class ObjectEnvironmentRecord(EnvironmentRecord):
    provide_this = False

    def __init__(self, obj, provide_this = False):
        self.binding_object = obj
        if provide_this is True:
            self.provide_this = True

    # 10.2.1.2.1
    def has_binding(self, n):
        bindings = self.binding_object
        return bindings.has_property(n)

    # 10.2.1.2.2
    def create_mutuable_binding(self, n, d):
        bindings = self.binding_object
        assert bindings.has_property(n) is False
        if d is True:
            config_value = False
        else:
            config_value = True

        from js.jsobj import PropertyDescriptor
        desc = PropertyDescriptor(value = w_Undefined, writable = True, enumerable = True, configurable = config_value)
        bindings.define_own_property(n, desc, True)

    # 10.2.1.2.3
    def set_mutable_binding(self, n, v, s = False):
        bindings = self.binding_object
        bindings.put(n, v, s)

    # 10.2.1.2.4
    def get_binding_value(self, n, s = False):
        bindings = self.binding_object
        value = bindings.has_property(n)
        if value is False:
            if s is False:
                return w_Undefined
            else:
                raise JsReferenceError(self.__class__)

        return bindings.get(n)

    # 10.2.1.2.5
    def delete_binding(self, n):
        bindings = self.binding_object
        return bindings.delete(n, False)

    # 10.2.1.2.6
    def implicit_this_value(self):
        if self.provide_this is True:
            return self.binding_object
        return w_Undefined

class GlobalEnvironmentRecord(ObjectEnvironmentRecord):
    pass

#from rpython.rlib import jit
#from rpython.rlib.objectmodel import enforceargs
from js.property_descriptor import PropertyDescriptor, DataPropertyDescriptor, AccessorPropertyDescriptor

NOT_SET = -1


# 8.6.1
class Property(object):
    _immutable_fields_ = ['value', 'writable', 'getter', 'setter', 'enumerable', 'configurable']

    def __init__(self, value=None, writable=NOT_SET, getter=None, setter=None, enumerable=NOT_SET, configurable=NOT_SET):
        self.value = value
        self.writable = writable
        self.getter = getter
        self.setter = setter
        self.enumerable = enumerable
        self.configurable = configurable

    def is_data_property(self):
        return False

    def is_accessor_property(self):
        return False

    def update_with_descriptor(self, desc):
        raise NotImplementedError(self.__class__)

    def to_property_descriptor(self):
        return PropertyDescriptor(enumerable=self.enumerable, configurable=self.configurable)


class DataProperty(Property):
    def __init__(self, value=None, writable=NOT_SET, enumerable=NOT_SET, configurable=NOT_SET):
        Property.__init__(self, value=value, writable=writable, enumerable=enumerable, configurable=configurable)

    def is_data_property(self):
        return True

    def update_with_descriptor(self, desc):
        assert isinstance(desc, PropertyDescriptor)

        if desc.has_set_value():
            value = desc.value
        else:
            value = self.value

        if desc.has_set_writable():
            writable = desc.writable
        else:
            writable = self.writable

        if desc.has_set_enumerable():
            enumerable = desc.enumerable
        else:
            enumerable = self.enumerable

        if desc.has_set_configurable():
            configurable = desc.configurable
        else:
            configurable = self.configurable

        return DataProperty(value, writable, enumerable, configurable)

    def to_property_descriptor(self):
        return DataPropertyDescriptor(self.value, self.writable, self.enumerable, self.configurable)


class AccessorProperty(Property):
    def __init__(self, getter=None, setter=None, enumerable=NOT_SET, configurable=NOT_SET):
        Property.__init__(self, getter=getter, setter=setter, enumerable=enumerable, configurable=configurable)

    def is_accessor_property(self):
        return True

    def update_with_descriptor(self, desc):
        assert isinstance(desc, PropertyDescriptor)

        if desc.has_set_getter():
            getter = desc.getter
        else:
            getter = self.getter

        if desc.has_set_setter():
            setter = desc.setter
        else:
            setter = self.setter

        if desc.has_set_enumerable():
            enumerable = desc.enumerable
        else:
            enumerable = self.enumerable

        if desc.has_set_configurable():
            configurable = desc.configurable
        else:
            configurable = self.configurable

        return AccessorProperty(getter, setter, enumerable, configurable)

    def to_property_descriptor(self):
        return AccessorPropertyDescriptor(self.getter, self.setter, self.enumerable, self.configurable)

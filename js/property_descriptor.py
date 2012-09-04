#from pypy.rlib import jit


def is_data_descriptor(desc):
    if desc is None:
        return False
    return desc.is_data_descriptor()


def is_accessor_descriptor(desc):
    if desc is None:
        return False
    return desc.is_accessor_descriptor()


def is_generic_descriptor(desc):
    if desc is None:
        return False
    return desc.is_generic_descriptor()

NOT_SET = -1


# 8.10
class PropertyDescriptor(object):
    _immutable_fields_ = ['value', 'writable', 'getter', 'setter', 'configurable', 'enumerable']

    def __init__(self, value=None, writable=NOT_SET, getter=None, setter=None, configurable=NOT_SET, enumerable=NOT_SET):
        self.value = value
        self.writable = writable
        self.getter = getter
        self.setter = setter
        self.configurable = configurable
        self.enumerable = enumerable

    def is_accessor_descriptor(self):
        return self.has_set_getter() and self.has_set_setter()

    def is_data_descriptor(self):
        return self.has_set_value() and self.has_set_writable()

    def is_generic_descriptor(self):
        return self.is_accessor_descriptor() is False and self.is_data_descriptor() is False

    def has_set_writable(self):
        return self.writable is not NOT_SET

    def has_set_configurable(self):
        return self.configurable is not NOT_SET

    def has_set_enumerable(self):
        return self.enumerable is not NOT_SET

    def has_set_value(self):
        return self.value is not None

    def has_set_getter(self):
        return self.getter is not None

    def has_set_setter(self):
        return self.setter is not None

    def is_empty(self):
        if self.has_set_writable():
            return False

        if self.has_set_value():
            return False

        if self.has_set_getter():
            return False

        if self.has_set_setter():
            return False

        if self.has_set_configurable():
            return False

        if self.has_set_enumerable():
            return False

        return True

    def __eq__(self, other):
        if not isinstance(other, PropertyDescriptor):
            return False

        if self.has_set_setter() and self.setter != other.setter:
            return False

        if self.has_set_getter() and self.getter != other.getter:
            return False

        if self.has_set_writable() and self.writable != other.writable:
            return False

        if self.has_set_value() and self.value != other.value:
            return False

        if self.has_set_configurable() and self.configurable != other.configurable:
            return False

        if self.has_set_enumerable() and self.enumerable != other.enumerable:
            return False

        return True

    def copy(self):
        return PropertyDescriptor(value=self.value,
                                  writable=self.writable,
                                  getter=self.getter,
                                  setter=self.setter,
                                  configurable=self.configurable,
                                  enumerable=self.enumerable)


class DataPropertyDescriptor(PropertyDescriptor):
    def __init__(self, value, writable, enumerable, configurable):
        PropertyDescriptor.__init__(self, value=value, writable=writable, enumerable=enumerable, configurable=configurable)

    def copy(self):
        return DataPropertyDescriptor(self.value, self.writable, self.enumerable, self.configurable)


class AccessorPropertyDescriptor(PropertyDescriptor):
    def __init__(self, getter, setter, enumerable, configurable):
        PropertyDescriptor.__init__(self, getter=getter, setter=setter, enumerable=enumerable, configurable=configurable)

    def copy(self):
        return AccessorPropertyDescriptor(self.getter, self.setter, self.enumerable, self.configurable)

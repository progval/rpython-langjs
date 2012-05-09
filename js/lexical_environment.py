from js.jsobj import w_Undefined
from js.execution import JsReferenceError

def get_identifier_reference(lex, identifier, strict = False):
    if lex is None:
        return Reference(w_Undefined, identifier, strict)

    envRec = lex.environment_record
    exists = envRec.has_binding(identifier)
    if exists:
        return Reference(envRec, identifier, strict)
    else:
        outer = lex.outer_environment
        return get_identifier_reference(outer, identifier, strict)

class LexicalEnvironment(object):
    def __init__(self, outer_environment = None):
        assert isinstance(outer_environment, LexicalEnvironment) or outer_environment is None
        self.outer_environment = outer_environment
        self.environment_record = None

    def get_identifier_reference(self, identifier, strict=False):
        return get_identifier_reference(self, identifier, strict)

class DeclarativeEnvironment(LexicalEnvironment):
    def __init__(self, outer_environment = None):
        LexicalEnvironment.__init__(self, outer_environment)
        from js.environment_record import DeclarativeEnvironmentRecord
        self.environment_record = DeclarativeEnvironmentRecord()

class ObjectEnvironment(LexicalEnvironment):
    def __init__(self, obj, outer_environment = None):
        LexicalEnvironment.__init__(self, outer_environment)
        from js.environment_record import ObjectEnvironmentRecord
        self.environment_record = ObjectEnvironmentRecord(obj)

class Reference(object):
    def __init__(self, base_value, referenced, strict):
        self.base_value = base_value
        self.referenced = referenced
        self.strict = strict

    def get_base(self):
        return self.base_value

    def get_referenced_name(self):
        return self.referenced

    def is_strict_reference(self):
        return self.strict

    def has_primitive_base(self):
        b = self.base_value
        from js.jsobj import W_Boolean, W_String, W_Number
        if isinstance(b, W_Boolean) or isinstance(b, W_String) or isinstance(b, W_Number):
            return True
        return False

    def is_property_reference(self):
        from js.jsobj import W_BasicObject
        if isinstance(self.base_value, W_BasicObject) or self.has_primitive_base() == True:
            return True
        return False

    def is_unresolvable_reference(self):
        if self.base_value == w_Undefined:
            return True
        return False

    def get_value(self):
        return get_value(self)

    def put_value(self, value):
        put_value(self, value)

# 8.7.1
def get_value(v):
    if not isinstance(v, Reference):
        return ref

    base = v.get_base()

    if v.is_unresolvable_reference():
        referenced = v.get_referenced_name()
        raise JsReferenceError(referenced)

    if v.is_property_reference():
        raise NotImplementedError('8.7.1 4.')
    else:
        from js.environment_record import EnvironmentRecord
        assert isinstance(base, EnvironmentRecord)
        name = v.get_referenced_name()
        strict = v.is_strict_reference()
        return base.get_binding_value(name, strict)

# 8.7.2
def put_value(v, w):
    if not isinstance(v, Reference):
        raise JsReferenceError()

    base = v.get_base()
    if v.is_unresolvable_reference():
        if v.is_strict_reference():
            referenced = v.get_referenced_name()
            raise JsReferenceError(referenced)
        else:
            name = v.get_referenced_name()
            # TODO how to solve this ????
            from js.execution_context import get_global_object
            global_object = get_global_object()

            global_object.put(name, w, throw = False)
    elif v.is_property_reference():
        raise NotImplementedError('8.7.2 4.')
    else:
        from js.environment_record import EnvironmentRecord
        assert isinstance(base, EnvironmentRecord)
        name = v.get_referenced_name()
        strict = v.is_strict_reference()
        base.set_mutable_binding(name, w, strict)


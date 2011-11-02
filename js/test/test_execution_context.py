import py

from js.jsexecution_context import ExecutionContext
from js.execution import ThrowException
from js.jsobj import w_Undefined

def new_context(parent = None, size=3):
    context = ExecutionContext(parent)
    context._map_dict_values_init_with_size(size)
    return context

class TestExecutionContext(object):
    def test_identifier_set_local(self):
        context = new_context()
        context._identifier_set_local('foo', 1)
        assert context._map_dict_get('foo') == 1

    def test_identifier_get_local(self):
        context = new_context()
        context._map_dict_set('foo', 1)
        assert context._identifier_get_local('foo') == 1

    def test_identifier_is_local(sefl):
        context = new_context()
        context._map_dict_set('foo', 1)
        assert context._identifier_is_local('foo') is True
        assert context._identifier_is_local('bar') is False

    def test_identifier_get(self):
        context = new_context()
        context._identifier_set_local('foo', 1)
        context._identifier_set_local('bar', 2)
        assert context._identifier_get('foo') == 1
        assert context._identifier_get('bar') == 2

    def test_identifier_get_from_parent(self):
        parent = new_context()
        context = new_context(parent)

        parent._identifier_set_local('foo', 1)
        context._identifier_set_local('bar', 2)

        assert context._identifier_get('foo') == 1
        assert context._identifier_get('bar') == 2

    def test_identifier_get_from_parents(self):
        grandparent = new_context()
        parent = new_context(grandparent)
        context = new_context(parent)

        grandparent._identifier_set_local('foo', 0)
        parent._identifier_set_local('foo', 1)
        parent._identifier_set_local('bar', 2)

        assert context._identifier_get('foo') == 1
        assert context._identifier_get('bar') == 2

    def test_identifier_get_local_precedence(self):
        parent = new_context()
        context = new_context(parent)

        parent._identifier_set_local('foo', 1)
        context._identifier_set_local('foo', 2)

        assert context._identifier_get('foo') == 2
        assert parent._identifier_get('foo') == 1

    def test_identifier_get_undefined_identifier(self):
        parent = new_context()
        context = new_context(parent)
        py.test.raises(KeyError, context._identifier_get, 'foo')
        py.test.raises(KeyError, parent._identifier_get, 'foo')

    def test_identifier_set_if_local(self):
        context = new_context()

        context._identifier_set_local('foo', 0)
        context._identifier_set_if_local('foo', 1)

        assert context._identifier_get_local('foo') == 1

    def test_identifier_set_if_local_not_local(self):
        context = new_context()
        py.test.raises(KeyError, context._identifier_set_if_local, 'foo', 1)

    def test_identifier_set_if_local_on_parent(self):
        parent = new_context()
        context = new_context(parent)

        parent._identifier_set_local('foo', None)

        context._identifier_set_if_local('foo', 1)
        assert parent._identifier_get_local('foo') == 1

    def test_identifier_set_if_local_not_in_parent(self):
        parent = new_context()
        context = new_context(parent)
        py.test.raises(KeyError, context._identifier_set_if_local, 'foo', 1)

    def test_identifier_set_if_local_on_parents(self):
        grandparent = new_context()
        parent = new_context(grandparent)
        context = new_context(parent)

        grandparent._identifier_set_local('foo', 0)
        parent._identifier_set_local('foo', 1)

        context._identifier_set_if_local('foo', 99)

        assert context._identifier_get('foo') == 99
        assert parent._identifier_get('foo') == 99

        py.test.raises(KeyError, context._identifier_get_local,'foo')
        assert parent._identifier_get_local('foo') == 99
        assert grandparent._identifier_get_local('foo') == 0

    def test_resolve_identifier(self):
        parent = new_context()
        context = new_context(parent)
        parent._identifier_set_local('foo', 0)
        context._identifier_set_local('bar', 1)

        ctx = None
        assert context.resolve_identifier(ctx, 'foo') == 0
        assert context.resolve_identifier(ctx, 'bar') == 1
        py.test.raises(ThrowException, context.resolve_identifier, ctx, 'baz')

    def test_assign(self):
        parent = new_context()
        context = new_context(parent)
        parent._identifier_set_local('foo', 0)
        context._identifier_set_local('bar', 1)

        context.assign('foo', 4)
        context.assign('bar', 8)

        assert context.get_property_value('foo') == 4
        assert context.get_property_value('bar') == 8

    def test_assign_local_precedence(self):
        parent = new_context()
        context = new_context(parent)
        parent._identifier_set_local('foo', 0)
        context._identifier_set_local('foo', 1)

        context.assign('foo', 42)

        assert parent.get_property_value('foo') == 0
        assert context.get_property_value('foo') == 42

    def test_declare_variable(self):
        ctx = None
        parent = new_context()
        context = new_context(parent)

        parent._identifier_set_local('foo', 0)

        assert context.resolve_identifier(ctx, 'foo') == 0

        context.declare_variable('foo')
        assert context.resolve_identifier(ctx, 'foo') == w_Undefined

        context.assign('foo', 42)

        assert parent.get_property_value('foo') == 0
        assert context._identifier_get_local('foo') == 42
        assert context.resolve_identifier(ctx, 'foo') == 42

    def test_get_local_value(self):
        context = new_context()
        context.declare_variable('foo')
        context.declare_variable('bar')

        context.assign('foo', 0)
        assert context.get_local_value(0) == 0

        context.assign('foo', 42)
        assert context.get_local_value(0) == 42

        context.assign('bar', 1)
        assert context.get_local_value(1) == 1

    def test_get_local_value_is_local(self):
        parent = new_context()
        context = new_context(parent)

        parent._identifier_set_local('foo', 0)
        py.test.raises(KeyError, context.get_local_value, 0)

    def test_assign_global_default(self):
        global_ctx = new_context()
        parent = new_context(global_ctx)
        context = new_context(parent)

        context.assign('foo', 23)
        py.test.raises(KeyError, context._identifier_get_local, 'foo')
        py.test.raises(KeyError, parent._identifier_get_local, 'foo')
        assert global_ctx._identifier_get_local('foo') == 23
        parent.assign('bar', 42)
        py.test.raises(KeyError, context._identifier_get_local, 'bar')
        py.test.raises(KeyError, parent._identifier_get_local, 'bar')
        assert global_ctx._identifier_get_local('bar') == 42

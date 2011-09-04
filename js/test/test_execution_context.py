import py

from js.jsexecution_context import ExecutionContext
from js.execution import ThrowException
from js.jsobj import Property, w_Undefined

class TestExecutionContext(object):
    def test_identifier_set_local(self):
        context = ExecutionContext()
        context._identifier_set_local('foo', 1)
        assert context.values.get('foo') == 1

    def test_identifier_get_local(self):
        context = ExecutionContext()
        context.values.set('foo', 1)
        assert context._identifier_get_local('foo') == 1

    def test_identifier_is_local(sefl):
        context = ExecutionContext()
        context.values.set('foo', 1)
        assert context._identifier_is_local('foo') is True
        assert context._identifier_is_local('bar') is False


    def test_identifier_get(self):
        context = ExecutionContext()
        context._identifier_set_local('foo', 1)
        context._identifier_set_local('bar', 2)
        assert context._identifier_get('foo') == 1
        assert context._identifier_get('bar') == 2

    def test_identifier_get_from_parent(self):
        parent = ExecutionContext()
        parent._identifier_set_local('foo', 1)
        context = ExecutionContext(parent)
        context._identifier_set_local('bar', 2)
        assert context._identifier_get('foo') == 1
        assert context._identifier_get('bar') == 2

    def test_identifier_get_from_parents(self):
        grandparent = ExecutionContext()
        parent = ExecutionContext(grandparent)
        context = ExecutionContext(parent)

        grandparent._identifier_set_local('foo', 0)
        parent._identifier_set_local('foo', 1)
        parent._identifier_set_local('bar', 2)

        assert context._identifier_get('foo') == 1
        assert context._identifier_get('bar') == 2

    def test_identifier_get_local_precedence(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        parent._identifier_set_local('foo', 1)
        context._identifier_set_local('foo', 2)
        assert context._identifier_get('foo') == 2
        assert parent._identifier_get('foo') == 1

    def test_identifier_get_undefined_identifier(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        py.test.raises(KeyError, context._identifier_get, 'foo')
        py.test.raises(KeyError, parent._identifier_get, 'foo')

    def test_identifier_set_if_local(self):
        context = ExecutionContext()
        context._identifier_set_local('foo', 0)
        context._identifier_set_if_local('foo', 1)
        assert context._identifier_get_local('foo') == 1

    def test_identifier_set_if_local_not_local(self):
        context = ExecutionContext()
        py.test.raises(KeyError, context._identifier_set_if_local, 'foo', 1)

    def test_identifier_set_if_local_on_parent(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        parent._identifier_set_local('foo', None)

        context._identifier_set_if_local('foo', 1)
        assert parent._identifier_get_local('foo') == 1

    def test_identifier_set_if_local_not_in_parent(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        py.test.raises(KeyError, context._identifier_set_if_local, 'foo', 1)

    def test_identifier_set_if_local_on_parents(self):
        grandparent = ExecutionContext()
        parent = ExecutionContext(grandparent)
        context = ExecutionContext(parent)

        grandparent._identifier_set_local('foo', 0)
        parent._identifier_set_local('foo', 1)

        context._identifier_set_if_local('foo', 99)

        assert context._identifier_get('foo') == 99
        assert parent._identifier_get('foo') == 99

        py.test.raises(KeyError, context._identifier_get_local,'foo')
        assert parent._identifier_get_local('foo') == 99
        assert grandparent._identifier_get_local('foo') == 0

    def test_resolve_identifier(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        parent._identifier_set_local('foo', Property('foo', 0))
        context._identifier_set_local('bar', Property('foo', 1))

        ctx = None
        assert context.resolve_identifier(ctx, 'foo') == 0
        assert context.resolve_identifier(ctx, 'bar') == 1
        py.test.raises(ThrowException, context.resolve_identifier, ctx, 'baz')

    def test_assign(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        p_foo = Property('foo', 0)
        p_bar = Property('foo', 1)
        parent._identifier_set_local('foo', p_foo)
        context._identifier_set_local('bar', p_bar)

        context.assign('foo', 4)
        context.assign('bar', 8)

        assert p_foo.value == 4
        assert p_bar.value == 8

    def test_assign_local_precedence(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)
        p_foo_0 = Property('foo', 0)
        p_foo_1 = Property('foo', 1)
        parent._identifier_set_local('foo', p_foo_0)
        context._identifier_set_local('foo', p_foo_1)

        context.assign('foo', 42)

        assert p_foo_0.value == 0
        assert p_foo_1.value == 42

    def test_declare_variable(self):
        ctx = None
        parent = ExecutionContext()
        context = ExecutionContext(parent)

        p_foo = Property('foo', 0)
        parent._identifier_set_local('foo', p_foo)

        assert context.resolve_identifier(ctx, 'foo') == 0

        context.declare_variable('foo')
        assert context.resolve_identifier(ctx, 'foo') == w_Undefined

        context.assign('foo', 42)

        assert p_foo.value == 0
        assert context._identifier_get_local('foo').value == 42
        assert context.resolve_identifier(ctx, 'foo') == 42

    def test_get_local_value(self):
        context = ExecutionContext()
        context.declare_variable('foo')
        context.declare_variable('bar')

        context.assign('foo', 0)
        assert context.get_local_value(0) == 0

        context.assign('foo', 42)
        assert context.get_local_value(0) == 42

        context.assign('bar', 1)
        assert context.get_local_value(1) == 1

    def test_get_local_value_is_local(self):
        parent = ExecutionContext()
        context = ExecutionContext(parent)

        p_foo = Property('foo', 0)
        parent._identifier_set_local('foo', p_foo)
        py.test.raises(KeyError, context.get_local_value, 0)

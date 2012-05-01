import py
from js.lexical_environment import DeclarativeEnvironment, ObjectEnvironment
from js.jsobj import w_Undefined, W_BasicObject

class TestDeclarativeEnvironment(object):
    def test_get_identifier_reference_empty(self):
        lex_env = DeclarativeEnvironment()
        ref = lex_env.get_identifier_reference('foo')

        assert ref.base_value == w_Undefined
        assert ref.referenced == 'foo'

    def test_get_identifier_reference(self):
        lex_env = DeclarativeEnvironment()

        env_rec = lex_env.environment_record
        env_rec.create_mutuable_binding('foo', True)

        ref = lex_env.get_identifier_reference('foo')
        assert ref.base_value == env_rec
        assert ref.referenced == 'foo'

    def test_get_identifier_reference_from_parent(self):
        outer_lex_env = DeclarativeEnvironment()
        outer_env_rec = outer_lex_env.environment_record
        outer_env_rec.create_mutuable_binding('foo', True)

        lex_env = DeclarativeEnvironment(outer_lex_env)

        ref = lex_env.get_identifier_reference('foo')
        assert ref.base_value == outer_env_rec
        assert ref.referenced == 'foo'

    def test_get_identifier_reference_overwrite_parent(self):
        outer_lex_env = DeclarativeEnvironment()
        outer_env_rec = outer_lex_env.environment_record
        outer_env_rec.create_mutuable_binding('foo', True)

        lex_env = DeclarativeEnvironment(outer_lex_env)
        env_rec = lex_env.environment_record
        env_rec.create_mutuable_binding('foo', True)

        ref = lex_env.get_identifier_reference('foo')
        assert ref.base_value == env_rec
        assert ref.referenced == 'foo'

class TestObjectEnvironment(object):
    def test_get_identifier_reference_empty(self):
        obj = W_BasicObject()
        lex_env = ObjectEnvironment(obj)
        ref = lex_env.get_identifier_reference('foo')

        assert ref.base_value == w_Undefined
        assert ref.referenced == 'foo'

    def test_get_identifier_reference(self):
        obj = W_BasicObject()
        lex_env = ObjectEnvironment(obj)

        env_rec = lex_env.environment_record
        env_rec.create_mutuable_binding('foo', True)

        ref = lex_env.get_identifier_reference('foo')
        assert ref.base_value == env_rec
        assert ref.referenced == 'foo'

    def test_get_identifier_reference_from_parent(self):
        outer_lex_env = DeclarativeEnvironment()
        outer_env_rec = outer_lex_env.environment_record
        outer_env_rec.create_mutuable_binding('foo', True)

        obj = W_BasicObject()
        lex_env = ObjectEnvironment(obj, outer_lex_env)

        ref = lex_env.get_identifier_reference('foo')
        assert ref.base_value == outer_env_rec
        assert ref.referenced == 'foo'

    def test_get_identifier_reference_overwrite_parent(self):
        outer_lex_env = DeclarativeEnvironment()
        outer_env_rec = outer_lex_env.environment_record
        outer_env_rec.create_mutuable_binding('foo', True)

        obj = W_BasicObject()
        lex_env = ObjectEnvironment(obj, outer_lex_env)
        env_rec = lex_env.environment_record
        env_rec.create_mutuable_binding('foo', True)

        ref = lex_env.get_identifier_reference('foo')
        assert ref.base_value == env_rec
        assert ref.referenced == 'foo'


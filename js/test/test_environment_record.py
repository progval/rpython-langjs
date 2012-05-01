import py
from js.environment_record import DeclarativeEnvironmentRecord, ObjectEnvironmentRecord
from js.jsobj import W__Object

class TestDeclarativeEnvironmentRecord(object):
    def test_create_mutable_binding(self):
        env_rec = DeclarativeEnvironmentRecord()
        env_rec.create_mutuable_binding('foo', True)
        assert env_rec.has_binding('foo') == True

    def test_set_and_get_mutable_binding(self):
        env_rec = DeclarativeEnvironmentRecord()
        env_rec.create_mutuable_binding('foo', True)
        env_rec.set_mutable_binding('foo', 42)
        assert env_rec.get_binding_value('foo') == 42

class TestObjectEnvironmentRecord(object):
    def test_create_mutable_binding(self):
        obj = W__Object()
        env_rec = ObjectEnvironmentRecord(obj)

        assert env_rec.has_binding('foo') == False
        env_rec.create_mutuable_binding('foo', True)
        assert env_rec.has_binding('foo') == True

    def test_set_and_get_mutable_binding(self):
        obj = W__Object()
        env_rec = ObjectEnvironmentRecord(obj)

        env_rec.create_mutuable_binding('foo', True)
        env_rec.set_mutable_binding('foo', 42)
        assert env_rec.get_binding_value('foo') == 42

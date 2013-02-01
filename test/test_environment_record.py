from js.environment_record import DeclarativeEnvironmentRecord, ObjectEnvironmentRecord
from js.jsobj import W__Object


class TestDeclarativeEnvironmentRecord(object):
    def test_create_mutable_binding(self):
        env_rec = DeclarativeEnvironmentRecord(size=1)
        env_rec.create_mutuable_binding(u'foo', True)
        assert env_rec.has_binding(u'foo') is True

    def test_set_and_get_mutable_binding(self):
        env_rec = DeclarativeEnvironmentRecord(size=1)
        env_rec.create_mutuable_binding(u'foo', True)
        env_rec.set_mutable_binding(u'foo', 42, False)
        assert env_rec.get_binding_value(u'foo') == 42


class TestObjectEnvironmentRecord(object):
    def test_create_mutable_binding(self):
        obj = W__Object()
        env_rec = ObjectEnvironmentRecord(obj)

        assert env_rec.has_binding(u'foo') is False
        env_rec.create_mutuable_binding(u'foo', True)
        assert env_rec.has_binding(u'foo') is True

    def test_set_and_get_mutable_binding(self):
        obj = W__Object()
        env_rec = ObjectEnvironmentRecord(obj)

        env_rec.create_mutuable_binding(u'foo', True)
        env_rec.set_mutable_binding(u'foo', 42, False)
        assert env_rec.get_binding_value(u'foo') == 42

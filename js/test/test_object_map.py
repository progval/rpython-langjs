import py

from js.object_map import Map, MapRoot, MapNode


class TestMap(object):
    def setup_class(cls):
        pass

    def setup_method(cls, func):
        pass

    def test_root(self):
        m = MapRoot()
        assert m.index == Map.NOT_FOUND

    def test_lookup_empty_root(self):
        m = MapRoot()
        assert m.lookup('foo') == Map.NOT_FOUND

    def test_lookup(self):
        a = MapRoot()
        b = MapNode(a, 'foo')
        c = MapNode(b, 'bar')
        d = MapNode(b, 'baz')
        e = MapNode(a, 'bar')

        assert a.lookup('foo') == Map.NOT_FOUND
        assert a.lookup('bar') == Map.NOT_FOUND
        assert a.lookup('baz') == Map.NOT_FOUND
        assert b.lookup('foo') == 0
        assert b.lookup('bar') == Map.NOT_FOUND
        assert b.lookup('baz') == Map.NOT_FOUND
        assert c.lookup('foo') == 0
        assert c.lookup('bar') == 1
        assert c.lookup('baz') == Map.NOT_FOUND
        assert d.lookup('foo') == 0
        assert d.lookup('bar') == Map.NOT_FOUND
        assert d.lookup('baz') == 1
        assert e.lookup('bar') == 0

    def test_add_node(self):
        a = MapRoot()
        b = a.add('foo')
        assert b._key() in a.forward_pointers
        assert a.forward_pointers[b._key()] == b
        assert b.index == 0
        assert b.back == a

        c = b.add('bar')
        assert c.lookup('bar') == 1

        d = b.add('baz')
        assert d.lookup('baz') == 1
        assert c.lookup('baz') == Map.NOT_FOUND

        py.test.raises(AssertionError, c.add, 'bar')

    def test_add_duplicate(self):
        r = MapRoot()
        a = r.add('foo')
        b = r.add('foo')
        assert a == b

        a = a.add('bar')
        b = b.add('bar')

        assert a == b

    def test_keys(self):
        m = MapRoot()
        a = m.add('foo')
        a = a.add('bar')
        a = a.add('baz')

        b = m.add('baz')
        b = b.add('bar')

        assert a.keys() == ['foo', 'bar', 'baz']
        assert b.keys() == ['baz', 'bar']

    def test_delete(self):
        m = MapRoot()
        m = m.add('foo')
        m = m.add('bar')
        m = m.add('baz')

        b = m.delete('foo')
        c = m.delete('bar')

        assert b.lookup('foo') == Map.NOT_FOUND
        assert b.lookup('bar') == 0
        assert b.lookup('baz') == 1
        assert b.keys() == ['bar', 'baz']

        assert m.lookup('foo') == 0
        assert m.lookup('bar') == 1
        assert m.lookup('baz') == 2
        assert m.keys() == ['foo', 'bar', 'baz']

        assert c.lookup('foo') == 0
        assert c.lookup('bar') == Map.NOT_FOUND
        assert c.lookup('baz') == 1
        assert c.keys() == ['foo', 'baz']

    def test_delete_add(self):
        m = MapRoot()
        m = m.add('foo')
        m = m.add('bar')
        m = m.add('baz')

        b = m.delete('foo')
        b = b.add('foo')

        assert b.lookup('foo') == 2
        assert b.lookup('bar') == 0
        assert b.lookup('baz') == 1
        assert b.keys() == ['bar', 'baz', 'foo']

    def test_delete_duplicate(self):
        r = MapRoot()
        a = r.add('bar')
        a = a.add('baz')

        b = r.add('foo')
        b = b.add('bar')
        b = b.add('baz')
        b = b.delete('foo')

        assert b.lookup('foo') == Map.NOT_FOUND
        assert b.lookup('bar') == 0
        assert b.lookup('baz') == 1

        assert a.lookup('bar') == 0
        assert a.lookup('baz') == 1

        assert a == b

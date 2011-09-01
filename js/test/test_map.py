import py

from js.utils import Map, MapDict

class TestMap(object):
    def test_addname(self):
        m = Map()
        m.addname('foo')
        m.addname('bar')
        assert m.indexes['foo'] == 0
        assert m.indexes['bar'] == 1

    def test_addname_return_index(self):
        m = Map()
        assert m.addname('foo') == 0
        assert m.addname('bar') == 1

    def test_indexof(self):
        m = Map()
        m.addname('foo')
        m.addname('bar')
        assert m.indexof('foo') == 0
        assert m.indexof('bar') == 1
        assert m.indexof('baz') == Map.NOT_FOUND

    def test_delname(self):
        m = Map()
        m.addname('foo')
        assert m.indexof('foo') is not None
        m.delname('foo')
        assert m.indexof('foo') == Map.NOT_FOUND

    def test_delname_monotone(self):
        m = Map()
        m.addname('foo')
        index_of_foo = m.indexof('foo')
        assert index_of_foo is not None
        m.delname('foo')
        assert m.indexof('foo') == Map.NOT_FOUND
        m.addname('foo')
        assert index_of_foo != m.indexof('foo')

    def test_delname_monotone2(self):
        m = Map()
        m.addname('foo')
        m.addname('bar')
        index_of_foo = m.indexof('foo')
        assert index_of_foo is not None
        m.delname('foo')
        assert m.indexof('foo') == Map.NOT_FOUND
        m.addname('foo')
        assert index_of_foo != m.indexof('foo')
        assert m.indexof('bar') != m.indexof('foo')

class TestMapDict(object):
    def test_set(self):
        m = MapDict(2)
        m.set('foo', 4)
        m.set('bar', 8)
        assert m.indexes['foo'] == 0
        assert m.indexes['bar'] == 1
        assert m.values[0] == 4
        assert m.values[1] == 8

    def test_set_max_size(self):
        m = MapDict(2)
        m.set('foo', 4)
        m.set('bar', 8)
        py.test.raises(IndexError, m.set, 'baz', 15)

    def test_setindex(self):
        m = MapDict(2)
        m.setindex(0, 4)
        m.setindex(1, 8)
        assert m.values[0] == 4
        assert m.values[1] == 8

    def test_get(self):
        m = MapDict(2)
        m.indexes['foo'] = 0
        m.indexes['bar'] = 1
        m.values[0] = 4
        m.values[1] = 8
        assert m.get('foo') == 4
        assert m.get('bar') == 8

    def test_getindex(self):
        m = MapDict(2)
        m.values[0] = 4
        m.values[1] = 8
        assert m.getindex(0) == 4
        assert m.getindex(1) == 8
        assert m.getindex(1) == 8

    def test_get_key_error(self):
        m = MapDict(2)
        py.test.raises(KeyError, m.getindex, Map.NOT_FOUND)
        py.test.raises(KeyError, m.get, 'foo')

# encoding: utf-8
from pypy.rlib.jit import hint
from pypy.rlib import jit, debug

class StackMixin(object):
    _mixin_ = True
    def __init__(self):
        self.stack = [None]
        self.stack_pointer = 0

    def pop(self):
        e = self.top()
        i = self.stack_pointer - 1
        assert i >= 0
        self.stack[i] = None
        self.stack_pointer = i
        return e

    def top(self):
        i = self.stack_pointer - 1
        if i < 0:
            raise IndexError
        return self.stack[i]

    def append(self, element):
        from js.jsobj import W_Root
        assert isinstance(element, W_Root)
        i = self.stack_pointer
        assert i >= 0
        self.stack[i] = element
        self.stack_pointer = i + 1

    @jit.unroll_safe
    def pop_n(self, n):
        l = [None] * n
        for i in range(n-1, -1, -1):
            l[i] = self.pop()
        debug.make_sure_not_resized(l)
        return l

    def check_stack(self):
        assert self.stack_pointer == 1

class MapMixin(object):
    _MAP_NOT_FOUND = -1
    _mixin_ = True

    def __init__(self):
        self._map_indexes = {}
        self._map_next_index = 0

    def _map_get_next_index(self):
        index = self._map_next_index
        self._map_next_index += 1
        return index

    def _map_indexof(self, name):
        return self._map_indexes.get(name, self._MAP_NOT_FOUND)

    def _map_addname(self, name):
        if self._map_indexof(name) == self._MAP_NOT_FOUND:
            self._map_indexes[name] = self._map_get_next_index()
        return self._map_indexof(name)

    def _map_delname(self, name):
        self._map_indexes[name] = self._MAP_NOT_FOUND


class Map(MapMixin):
    NOT_FOUND = MapMixin._MAP_NOT_FOUND
    def __init__(self):
        MapMixin.__init__(self)

    def __repr__(self):
        return "%s:\n  %s" %(object.__repr__(self), repr(self._map_indexes))

    def indexof(self, name):
        return self._map_indexof(name)

    def addname(self, name):
        return self._map_addname(name)

    def delname(self, name):
        self._map_delname(name)

class MapDictMixin(object):
    _mixin_ = True
    def __init__(self, size = 99):
        MapMixin.__init__(self)
        self._map_dict_values_init_with_size(size)

    def _map_dict_values_init_with_size(self, size):
        self._map_dict_values = [None] * size

    def _map_dict_get(self, name):
        idx = self._map_indexof(name)
        return self._map_dict_getindex(idx)

    def _map_dict_getindex(self, idx):
        if idx < 0:
            raise KeyError
        return self._map_dict_values[idx]

    def _map_dict_set(self, name, value):
        idx = self._map_addname(name)
        self._map_dict_setindex(idx, value)

    def _map_dict_delete(self, name):
        self._map_dict_set(name, None)
        self._map_delname(name)

    def _map_dict_setindex(self, idx, value):
        self._map_dict_values[idx] = value

class MapDict(Map, MapDictMixin):
    def __init__(self, size = 99):
        Map.__init__(self)
        MapDictMixin.__init__(self, size)

    #@classmethod
    #def with_map(cls, m):
        #self = cls(len(m.indexes))
        #self.indexes = m.indexes
        #self.next_index = m.next_index
        #return self

    def __repr__(self):
        return "%s;\n  %s" %(Map.__repr__(self), repr(self._map_dict_values))

    def get(self, name):
        return self._map_dict_get(name)

    def getindex(self, idx):
        return self._map_dict_getindex(idx)

    def set(self, name, value):
        self._map_dict_set(name, value)

    def delete(self, name):
        self._map_dict_delete(name)

    def setindex(self, idx, value):
        self._map_dict_setindex(idx, value)

class DynamicMapDictMixin(object):
    _mixin_ = True
    def __init__(self):
        MapDictMixin.__init__(self, 0)

    def _map_addname(self, name):
        while len(self._map_dict_values) <= self._map_next_index:
            self._map_dict_values.append(None)
        return MapMixin._map_addname(self, name)

class DynamicMapDict(DynamicMapDictMixin, MapDict):
    def __init__(self):
        DynamicMapDictMixin.__init__(self)

def mapdict_with_map(m):
    assert isinstance(m, Map)
    indexes = m._map_indexes
    md = MapDict(len(indexes))
    md._map_indexes = indexes
    md._map_next_index = m._map_next_index
    return md

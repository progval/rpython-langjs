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

class Map(object):
    NOT_FOUND = -1
    def __init__(self):
        self.indexes = {}
        self.next_index = 0

    def _get_next_index(self):
        index = self.next_index
        self.next_index += 1
        return index

    def __repr__(self):
        return "%s:\n  %s" %(object.__repr__(self), repr(self.indexes))

    def indexof(self, name):
        return self.indexes.get(name, self.NOT_FOUND)

    def addname(self, name):
        if self.indexof(name) == self.NOT_FOUND:
            self.indexes[name] = self._get_next_index()
        return self.indexof(name)

    def delname(self, name):
        self.indexes[name] = self.NOT_FOUND

class MapDict(Map):
    def __init__(self, size = 99):
        Map.__init__(self)
        self.values = [None] * size

    def __repr__(self):
        return "%s;\n  %s" %(Map.__repr__(self), repr(self.values))

    def get(self, name):
        idx = self.indexof(name)
        return self.getindex(idx)

    def getindex(self, idx):
        if idx < 0:
            raise KeyError
        return self.values[idx]

    def set(self, name, value):
        idx = self.addname(name)
        self.setindex(idx, value)

    def delete(self, name):
        self.set(name, None)
        self.delname(name)

    def setindex(self, idx, value):
        self.values[idx] = value

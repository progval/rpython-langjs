from pypy.rlib import jit

class Map(object):
    NOT_FOUND = -1
    _immutable_fields_ = ['index', 'back', 'name', 'flags']
    def __init__(self):
        self.index = self.NOT_FOUND
        self.forward_pointers = {}
        self.back = None
        self.name = None
        self.flags = 0

    def __repr__(self):
        return "%s : %s:%d -> %s" % (object.__repr__(self), self.name, self.flags, repr(self.back) )

    def lookup(self, name):
        jit.promote(self)
        node = self._find_node_with_name(name)
        if node is not None:
            return node.index
        return self.NOT_FOUND

    def lookup_flag(self, name):
        jit.promote(self)
        node = self._find_node_with_name(name)
        if node is not None:
            return node.flags
        return self.NOT_FOUND

    def _find_node_with_name(self, name):
        if self.name == name:
            return self
        if self.back is not None:
            return self.back._find_node_with_name(name)

    def _find_node_with_name_and_flags(self, name, flags):
        if self.name == name and self.flags == flags:
            return self
        node = None
        if self.back is not None:
            node = self.back._find_node_with_name_and_flags(name, flags)
        if node is None:
            return self.forward_pointers.get((name, flags), None)

    def _key(self):
        return (self.name, self.flags)

    @jit.elidable
    def add(self, name, flags=0):
        assert self.lookup(name) == self.NOT_FOUND
        node = self.forward_pointers.get((name, flags), None)
        if node is None:
            node = MapNode(self, name, flags)
            self.forward_pointers[node._key()] = node
        return node

    def keys(self):
        if self.name is None:
            return []

        k = [self.name]
        if self.back is not None:
            return self.back.keys() + k

        return k

    def set_flags(self, name, flags):
        return self

    def delete(self, key):
        return self

class MapRoot(Map):
    pass

class MapNode(Map):
    def __init__(self, back, name, flags = 0):
        Map.__init__(self)
        self.back = back
        self.name = name
        self.index = back.index + 1
        self.flags = flags

    def delete(self, name):
        if self.name == name:
            return self.back
        else:
            n = self.back.delete(name)
            return n.add(self.name, self.flags)

    def set_flags(self, name, flags):
        if self.name == name:
            if self.flags == flags:
                return self
            else:
                return self.back.add(name, flags)
        else:
            n = self.back.set_flags(name, flags)
            return n.add(self.name, self.flags)

ROOT_MAP = MapRoot()

def root_map():
    return ROOT_MAP

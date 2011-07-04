import py

from js.utils import StackMixin
from js.jsobj import W_IntNumber

one   = W_IntNumber(1)
two   = W_IntNumber(2)
three = W_IntNumber(3)

class Stack(StackMixin):
    def __init__(self, size):
        StackMixin.__init__(self)
        self.stack = [None] * size

def test_stack_push():
    s = Stack(99)
    assert len(s.stack) == 99
    assert s.stack == [None] * 99

    s = Stack(99)
    s.append(one)
    assert s.stack[0] == one
    assert s.stack_pointer == 1

    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    assert s.stack[0] == one
    assert s.stack[1] == two
    assert s.stack[2] == three
    assert s.stack_pointer == 3

def test_stack_pop():
    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    assert s.pop() == three
    assert s.stack_pointer == 2
    assert s.stack[2] == None

    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    assert s.pop() == three
    assert s.pop() == two
    assert s.pop() == one

def test_stack_last():
    s = Stack(99)
    s.append(one)
    assert s.top() == one

    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    assert s.top() == three

def test_stack_popn():
    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    x = s.pop_n(2)
    assert x == [two, three]
    assert s.stack_pointer == 1
    assert s.stack[1] == None
    assert s.stack[2] == None

def test_stack_max():
    s = Stack(2)
    s.append(one)
    s.append(one)
    py.test.raises(IndexError, s.append,one)

import py

from js.utils import Stack
from js.jsobj import W_IntNumber

one   = W_IntNumber(1)
two   = W_IntNumber(2)
three = W_IntNumber(3)

def test_stack_push():
    s = Stack(99)
    assert len(s.content) == 99
    assert s.content == [None] * 99

    s = Stack(99)
    s.append(one)
    assert s.content[0] == one
    assert s.pointer == 1

    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    assert s.content[0] == one
    assert s.content[1] == two
    assert s.content[2] == three
    assert s.pointer == 3

def test_stack_pop():
    s = Stack(99)
    s.append(one)
    s.append(two)
    s.append(three)
    assert s.pop() == three
    assert s.pointer == 2
    assert s.content[2] == None

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
    assert s.pointer == 1
    assert s.content[1] == None
    assert s.content[2] == None

def test_stack_max():
    s = Stack(2)
    s.append(one)
    s.append(one)
    py.test.raises(IndexError, s.append,one)

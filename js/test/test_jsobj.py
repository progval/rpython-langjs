import pytest
from js.jsobj import W_IntNumber, W_FloatNumber, W_Null

def test_intnumber():
    n = W_IntNumber(0x80000000)
    assert n.ToInt32() == -0x80000000
    assert n.ToUInt32() == 0x80000000

def test_floatnumber():
    n = W_FloatNumber(0x80000000)
    assert n.ToInt32() == -0x80000000
    assert n.ToUInt32() == 0x80000000

def test_type_null():
    assert W_Null().type() == 'null'

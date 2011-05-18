import pytest
from js.jsobj import W_IntNumber, W_FloatNumber, W_Null
from js import interpreter

def test_intnumber():
    n = W_IntNumber(0x80000000)
    jsint = interpreter.Interpreter()
    ctx = jsint.w_Global
    assert n.ToInt32(ctx) == -0x80000000
    assert n.ToUInt32(ctx) == 0x80000000

def test_floatnumber():
    n = W_FloatNumber(0x80000000)
    jsint = interpreter.Interpreter()
    ctx = jsint.w_Global
    assert n.ToInt32(ctx) == -0x80000000
    assert n.ToUInt32(ctx) == 0x80000000

def test_type_null():
    assert W_Null().type() == 'null'

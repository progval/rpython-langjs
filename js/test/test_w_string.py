import py

from js.jsobj import W_String

def test_string_to_number():
    assert W_String(u'').ToNumber() == 0
    assert W_String(u' ').ToNumber() == 0
    assert W_String(u'\t').ToNumber() == 0
    assert W_String(u'\n').ToNumber() == 0
    assert W_String(u'\r').ToNumber() == 0
    assert W_String(u'\r\n').ToNumber() == 0

def test_isspace():
    from js.jsobj import _isspace
    assert _isspace(' ') is True
    assert _isspace('    ') is True
    assert _isspace('  \t\t\r\n  ') is True
    assert _isspace('  \t\ts\r\n  ') is False

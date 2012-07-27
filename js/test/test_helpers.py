import py

def test_hexing():
    from js.builtins_global import hexing
    assert u'%02X' % 4 == hexing(4, 2)
    assert u'%02X' % 8 == hexing(8, 2)
    assert u'%02X' % 16 == hexing(16, 2)
    assert u'%02X' % 32 == hexing(32, 2)
    assert u'%02X' % 64 == hexing(64, 2)
    assert u'%02X' % 128 == hexing(128, 2)
    assert u'%02X' % 256 == hexing(256, 2)

    assert u'%04X' % 4 == hexing(4, 4)
    assert u'%04X' % 8 == hexing(8, 4)
    assert u'%04X' % 16 == hexing(16, 4)
    assert u'%04X' % 32 == hexing(32, 4)
    assert u'%04X' % 64 == hexing(64, 4)
    assert u'%04X' % 128 == hexing(128, 4)
    assert u'%04X' % 256 == hexing(256, 4)
    assert u'%04X' % 1024 == hexing(1024, 4)

def test_string_match_chars():
    from js.builtins_global import _string_match_chars
    assert _string_match_chars(u'abccab', u'abc') is True
    assert _string_match_chars(u'ABCcba', u'abc') is True
    assert _string_match_chars(u'2921', u'0123456789') is True
    assert _string_match_chars(u'abcdabcd', u'abc') is False
    assert _string_match_chars(u'29x21', u'0123456789') is False

def test_unescape():
    from js import runistr
    assert runistr.unicode_unescape(u'\\u0041B\\u0043') == u'ABC'
    assert runistr.unicode_unescape(u'\\u004X\\u004') == u'u004Xu004'
    assert runistr.unicode_unescape(u'\\x4F\\x4G') == u'Ox4G'
    assert runistr.unicode_unescape(u'\\A\\B\\C') == u'ABC'
    assert runistr.unicode_unescape(u'ABC') == u'ABC'

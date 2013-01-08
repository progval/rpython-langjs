def test_string_match_chars():
    from js.builtins.js_global import _string_match_chars
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

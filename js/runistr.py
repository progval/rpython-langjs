from rpython.rlib.objectmodel import enforceargs
from rpython.rlib import runicode


@enforceargs(str)
def decode_str_utf8(string):
    result, consumed = runicode.str_decode_utf_8(string, len(string), "strict", True)
    return result


@enforceargs(unicode)
def encode_unicode_utf8(string):
    result = runicode.unicode_encode_utf_8(string, len(string), None)
    return result


@enforceargs(str)
def decode_unicode_escape(string):
    result, consumed = runicode.str_decode_unicode_escape(string, len(string), "strict", True)
    return result


def unescape_errorhandler(errors, encoding, msg, s, startingpos, endingpos):
    start = startingpos + 1
    assert start > 0
    assert endingpos > 0
    res = s[start:endingpos]
    return res, endingpos


# based on pypy.rlib.runicode str_decode_unicode_escape
@enforceargs(unicode)
def unicode_unescape(string):
    s = string
    size = len(string)
    errorhandler = unescape_errorhandler
    errors = 'strict'

    from rpython.rlib.rstring import UnicodeBuilder

    if size == 0:
        return u''

    builder = UnicodeBuilder(size)
    pos = 0
    while pos < size:
        ch = s[pos]

        # Non-escape characters are interpreted as Unicode ordinals
        if ch != '\\':
            builder.append(unichr(ord(ch)))
            pos += 1
            continue

        # - Escapes
        pos += 1
        if pos >= size:
            message = u"\\ at end of string"
            from js.exception import JsSyntaxError
            raise JsSyntaxError(message)

        ch = s[pos]
        pos += 1
        # \x escapes
        if ch == '\n':
            pass
        elif ch == '\\':
            builder.append(u'\\')
        elif ch == '\'':
            builder.append(u'\'')
        elif ch == '\"':
            builder.append(u'\"')
        elif ch == 'b':
            builder.append(u'\b')
        elif ch == 'f':
            builder.append(u'\f')
        elif ch == 't':
            builder.append(u'\t')
        elif ch == 'n':
            builder.append(u'\n')
        elif ch == 'r':
            builder.append(u'\r')
        elif ch == 'v':
            builder.append(u'\v')
        elif ch == 'a':
            builder.append(u'\a')
        elif '0' <= ch <= '7':
            x = ord(ch) - ord('0')
            if pos < size:
                ch = s[pos]
                if '0' <= ch <= '7':
                    pos += 1
                    x = (x << 3) + ord(ch) - ord('0')
                    if pos < size:
                        ch = s[pos]
                        if '0' <= ch <= '7':
                            pos += 1
                            x = (x << 3) + ord(ch) - ord('0')
            builder.append(unichr(x))
        # hex escapes
        # \xXX
        elif ch == 'x':
            digits = 2
            message = "truncated \\xXX escape"
            pos = hexescape(builder, s, pos, digits, "unicodeescape", errorhandler, message, errors)

        # \uXXXX
        elif ch == 'u':
            digits = 4
            message = "truncated \\uXXXX escape"
            pos = hexescape(builder, s, pos, digits, "unicodeescape", errorhandler, message, errors)

        else:
            #builder.append(u'\\')
            builder.append(unichr(ord(ch)))

    return builder.build()

hexdigits = "0123456789ABCDEFabcdef"


def hexescape(builder, s, pos, digits, encoding, errorhandler, message, errors):
    from rpython.rlib.rarithmetic import r_uint
    from rpython.rlib.runicode import MAXUNICODE, UNICHR

    chr = 0
    if pos + digits > len(s):
        message = "end of string in escape sequence"
        res, pos = errorhandler(errors, "unicodeescape", message, s, pos - 2, len(s))
        builder.append(res)
    else:
        try:
            chr = r_uint(int(str(s[pos:pos + digits]), 16))
        except ValueError:
            endinpos = pos
            while s[endinpos] in hexdigits:
                endinpos += 1
            res, pos = errorhandler(errors, encoding, message, s, pos - 2, endinpos + 1)
            builder.append(res)
        else:
            # when we get here, chr is a 32-bit unicode character
            if chr <= MAXUNICODE:
                builder.append(UNICHR(chr))
                pos += digits

            elif chr <= 0x10ffff:
                chr -= 0x10000L
                builder.append(unichr(0xD800 + (chr >> 10)))
                builder.append(unichr(0xDC00 + (chr & 0x03FF)))
                pos += digits
            else:
                message = "illegal Unicode character"
                res, pos = errorhandler(errors, encoding, message, s, pos - 2, pos + digits)
                builder.append(res)
    return pos

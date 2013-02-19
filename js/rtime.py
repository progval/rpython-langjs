# see pypy/module/rctime/interp_time.py
import os

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask
from pypy.module.rctime.interp_time import c_gmtime, c_localtime, c_mktime, glob_buf, _POSIX, _CYGWIN, _WIN, c_tzset, c_strftime

tmYEAR = 0
tmMONTH = 1
tmDAY = 2
tmHOUR = 3
tmMIN = 4
tmSEC = 5
tmWDAY = 6


def _tm_to_tuple(t):
    time_tuple = (
        rffi.getintfield(t, 'c_tm_year') + 1900,
        rffi.getintfield(t, 'c_tm_mon') + 1,  # want january == 1
        rffi.getintfield(t, 'c_tm_mday'),
        rffi.getintfield(t, 'c_tm_hour'),
        rffi.getintfield(t, 'c_tm_min'),
        rffi.getintfield(t, 'c_tm_sec'),
        ((rffi.getintfield(t, 'c_tm_wday') + 6) % 7),  # want monday == 0
        rffi.getintfield(t, 'c_tm_yday') + 1,  # want january, 1 == 1
        rffi.getintfield(t, 'c_tm_isdst'))
    return time_tuple


def _gettmarg(tup):
    if len(tup) != 9:
        raise Exception("argument must be sequence of length 9, not %d", len(tup))

    y = tup[0]
    tm_mon = tup[1]
    if tm_mon == 0:
        tm_mon = 1
    tm_mday = tup[2]
    if tm_mday == 0:
        tm_mday = 1
    tm_yday = tup[7]
    if tm_yday == 0:
        tm_yday = 1
    rffi.setintfield(glob_buf, 'c_tm_mon', tm_mon)
    rffi.setintfield(glob_buf, 'c_tm_mday', tm_mday)
    rffi.setintfield(glob_buf, 'c_tm_hour', tup[3])
    rffi.setintfield(glob_buf, 'c_tm_min', tup[4])
    rffi.setintfield(glob_buf, 'c_tm_sec', tup[5])
    rffi.setintfield(glob_buf, 'c_tm_wday', tup[6])
    rffi.setintfield(glob_buf, 'c_tm_yday', tm_yday)
    rffi.setintfield(glob_buf, 'c_tm_isdst', tup[8])
    if _POSIX:
        if _CYGWIN:
            pass
        else:
            # actually never happens, but makes annotator happy
            glob_buf.c_tm_zone = lltype.nullptr(rffi.CCHARP.TO)
            rffi.setintfield(glob_buf, 'c_tm_gmtoff', 0)

    if y < 1900:
        if 69 <= y <= 99:
            y += 1900
        elif 0 <= y <= 68:
            y += 2000
        else:
            raise Exception("year out of range")

    # tm_wday does not need checking of its upper-bound since taking "%
    #  7" in gettmarg() automatically restricts the range.
    if rffi.getintfield(glob_buf, 'c_tm_wday') < -1:
        raise Exception("day of week out of range")

    rffi.setintfield(glob_buf, 'c_tm_year', y - 1900)
    rffi.setintfield(glob_buf, 'c_tm_mon', rffi.getintfield(glob_buf, 'c_tm_mon') - 1)
    rffi.setintfield(glob_buf, 'c_tm_wday', (rffi.getintfield(glob_buf, 'c_tm_wday') + 1) % 7)
    rffi.setintfield(glob_buf, 'c_tm_yday', rffi.getintfield(glob_buf, 'c_tm_yday') - 1)

    return glob_buf


def gmtime(time_t):
    seconds = time_t
    t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
    t_ref[0] = seconds
    p = c_gmtime(t_ref)
    lltype.free(t_ref, flavor='raw')
    return _tm_to_tuple(p)


def localtime(time_t):
    seconds = time_t
    t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
    t_ref[0] = seconds
    p = c_localtime(t_ref)
    lltype.free(t_ref, flavor='raw')
    return _tm_to_tuple(p)


def mktime(tup):
    buf = _gettmarg(tup)
    rffi.setintfield(buf, "c_tm_wday", -1)
    tt = c_mktime(buf)
    if tt == -1 and rffi.getintfield(buf, "c_tm_wday") == -1:
        raise Exception('mktime argument out of range')

    return float(tt)


def tzset():
    c_tzset()


def timegm(tup):
    tz = os.environ.get('TZ')
    os.environ['TZ'] = ''
    tzset()

    try:
        tt = mktime(tup)
    finally:
        if tz:
            os.environ['TZ'] = tz
        else:
            del os.environ['TZ']
        tzset()

    return tt


def strftime(format, time_t):
    """strftime(format[, tuple]) -> string

    Convert a time tuple to a string according to a format specification.
    See the library reference manual for formatting codes. When the time tuple
    is not present, current time as returned by localtime() is used."""
    buf_value = _gettmarg(time_t)

    # Checks added to make sure strftime() does not crash Python by
    # indexing blindly into some array for a textual representation
    # by some bad index (fixes bug #897625).
    # No check for year since handled in gettmarg().
    if rffi.getintfield(buf_value, 'c_tm_mon') < 0 or rffi.getintfield(buf_value, 'c_tm_mon') > 11:
        raise Exception("month out of range")
    if rffi.getintfield(buf_value, 'c_tm_mday') < 1 or rffi.getintfield(buf_value, 'c_tm_mday') > 31:
        raise Exception("day of month out of range")
    if rffi.getintfield(buf_value, 'c_tm_hour') < 0 or rffi.getintfield(buf_value, 'c_tm_hour') > 23:
        raise Exception("hour out of range")
    if rffi.getintfield(buf_value, 'c_tm_min') < 0 or rffi.getintfield(buf_value, 'c_tm_min') > 59:
        raise Exception("minute out of range")
    if rffi.getintfield(buf_value, 'c_tm_sec') < 0 or rffi.getintfield(buf_value, 'c_tm_sec') > 61:
        raise Exception("seconds out of range")
    if rffi.getintfield(buf_value, 'c_tm_yday') < 0 or rffi.getintfield(buf_value, 'c_tm_yday') > 365:
        raise Exception("day of year out of range")
    if rffi.getintfield(buf_value, 'c_tm_isdst') < -1 or rffi.getintfield(buf_value, 'c_tm_isdst') > 1:
        raise Exception("daylight savings flag out of range")

    if _WIN:
        # check that the format string contains only valid directives
        length = len(format)
        i = 0
        while i < length:
            if format[i] == '%':
                i += 1
                if i < length and format[i] == '#':
                    # not documented by python
                    i += 1
                if i >= length or format[i] not in "aAbBcdHIjmMpSUwWxXyYzZ%":
                    raise Exception("invalid format string")
            i += 1

    i = 1024
    while True:
        outbuf = lltype.malloc(rffi.CCHARP.TO, i, flavor='raw')
        try:
            buflen = c_strftime(outbuf, i, format, buf_value)
            if buflen > 0 or i >= 256 * len(format):
                # if the buffer is 256 times as long as the format,
                # it's probably not failing for lack of room!
                # More likely, the format yields an empty result,
                # e.g. an empty format, or %Z when the timezone
                # is unknown.
                result = rffi.charp2strn(outbuf, intmask(buflen))
                return result
        finally:
            lltype.free(outbuf, flavor='raw')
        i += i

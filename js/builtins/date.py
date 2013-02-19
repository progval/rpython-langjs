from rpython.rlib.rfloat import NAN, isnan

from js.builtins import get_arg
from js.object_space import w_return, _w
from js import rtime

fMSEC = 1
fSEC = 2
fMIN = 3
fHOUR = 4
fDAY = 1
fMONTH = 2
fYEAR = 3


def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.jsobj import W_DateObject, W_DateConstructor
    from js.object_space import object_space

    ##Date
    # 15.9.5
    w_DatePrototype = W_DateObject(_w(NAN))
    # TODO
    #object_space.assign_proto(w_DatePrototype, object_space.proto_object)
    object_space.proto_date = w_DatePrototype

    put_native_function(w_DatePrototype, u'toString', to_string)

    put_native_function(w_DatePrototype, u'valueOf', value_of)
    put_native_function(w_DatePrototype, u'getTime', get_time)

    put_native_function(w_DatePrototype, u'getFullYear', get_full_year)
    put_native_function(w_DatePrototype, u'getUTCFullYear', get_utc_full_year)

    put_native_function(w_DatePrototype, u'getMonth', get_month)
    put_native_function(w_DatePrototype, u'getUTCMonth', get_utc_month)

    put_native_function(w_DatePrototype, u'getDate', get_date)
    put_native_function(w_DatePrototype, u'getUTCDate', get_utc_date)

    put_native_function(w_DatePrototype, u'getDay', get_day)
    put_native_function(w_DatePrototype, u'getUTCDay', get_utc_day)

    put_native_function(w_DatePrototype, u'getHours', get_hours)
    put_native_function(w_DatePrototype, u'getUTCHours', get_utc_hours)

    put_native_function(w_DatePrototype, u'getMinutes', get_minutes)
    put_native_function(w_DatePrototype, u'getUTCMinutes', get_utc_minutes)

    put_native_function(w_DatePrototype, u'getSeconds', get_seconds)
    put_native_function(w_DatePrototype, u'getUTCSeconds', get_utc_seconds)

    put_native_function(w_DatePrototype, u'getMilliseconds', get_milliseconds)
    put_native_function(w_DatePrototype, u'getUTCMilliseconds', get_utc_milliseconds)

    put_native_function(w_DatePrototype, u'getTimezoneOffset', get_timezone_offset)

    put_native_function(w_DatePrototype, u'setTime', set_time)

    put_native_function(w_DatePrototype, u'setMilliseconds', set_milliseconds)
    put_native_function(w_DatePrototype, u'setUTCMilliseconds', set_utc_milliseconds)

    put_native_function(w_DatePrototype, u'setSeconds', set_seconds)
    put_native_function(w_DatePrototype, u'setUTCSeconds', set_utc_seconds)

    put_native_function(w_DatePrototype, u'setMinutes', set_minutes)
    put_native_function(w_DatePrototype, u'setUTCMinutes', set_utc_minutes)

    put_native_function(w_DatePrototype, u'setHours', set_hours)
    put_native_function(w_DatePrototype, u'setUTCHours', set_utc_hours)

    put_native_function(w_DatePrototype, u'setDate', set_date)
    put_native_function(w_DatePrototype, u'setUTCDate', set_utc_date)

    put_native_function(w_DatePrototype, u'setMonth', set_month)
    put_native_function(w_DatePrototype, u'setUTCMonth', set_utc_month)

    put_native_function(w_DatePrototype, u'setFullYear', set_full_year)
    put_native_function(w_DatePrototype, u'setUTCFullYear', set_utc_full_year)

    put_native_function(w_DatePrototype, u'getYear', get_year)
    put_native_function(w_DatePrototype, u'setYear', set_year)

    put_native_function(w_DatePrototype, u'toUTCString', to_utc_string)
    put_native_function(w_DatePrototype, u'toGMTString', to_gmt_string)

    # 15.9.3
    w_Date = W_DateConstructor()
    object_space.assign_proto(w_Date, object_space.proto_function)
    put_property(global_object, u'Date', w_Date)

    put_property(w_Date, u'prototype', w_DatePrototype, writable=False, enumerable=False, configurable=False)

    put_native_function(w_Date, u'parse', parse)

    put_native_function(w_Date, u'now', now)

    put_native_function(w_Date, u'UTC', parse)

    # 15.9.5.1
    put_property(w_DatePrototype, u'constructor', w_Date)


@w_return
def now(this, args):
    import time
    return int(time.time() * 1000)


@w_return
def to_string(this, args):
    t = make_jstime(this)
    s = t.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)', local=True)
    return s


# 15.9.5.8
@w_return
def value_of(this, args):
    return get_time(this, args)


# 15.9.5.9
@w_return
def get_time(this, args):
    return this.PrimitiveValue()


# 15.9.5.10
@w_return
def get_full_year(this, args):
    t = make_jstime(this)
    return t.year(local=True)


# 15.9.5.11
@w_return
def get_utc_full_year(this, args):
    t = make_jstime(this)
    return t.year()


# 15.9.5.12
@w_return
def get_month(this, args):
    t = make_jstime(this)
    return t.month(local=True)


# 15.9.5.13
@w_return
def get_utc_month(this, args):
    t = make_jstime(this)
    return t.month()


# 15.9.5.14
@w_return
def get_date(this, args):
    t = make_jstime(this)
    return t.day(local=True)


# 15.9.5.15
@w_return
def get_utc_date(this, args):
    t = make_jstime(this)
    return t.day()


# 15.9.5.16
@w_return
def get_day(this, args):
    t = make_jstime(this)
    return t.wday(local=True)


# 15.9.5.17
@w_return
def get_utc_day(this, args):
    t = make_jstime(this)
    return t.wday()


# 15.9.5.18
@w_return
def get_hours(this, args):
    t = make_jstime(this)
    return t.hour(local=True)


# 15.9.5.19
@w_return
def get_utc_hours(this, args):
    t = make_jstime(this)
    return t.hour()


# 15.9.5.20
@w_return
def get_minutes(this, args):
    t = make_jstime(this)
    return t.min(local=True)


# 15.9.5.21
@w_return
def get_utc_minutes(this, args):
    t = make_jstime(this)
    return t.min()


# 15.9.5.22
@w_return
def get_seconds(this, args):
    t = make_jstime(this)
    return t.sec(local=True)


# 15.9.5.23
@w_return
def get_utc_seconds(this, args):
    t = make_jstime(this)
    return t.sec()


# 15.9.5.24
@w_return
def get_milliseconds(this, args):
    t = make_jstime(this)
    return t.msec(local=True)


# 15.9.5.25
@w_return
def get_utc_milliseconds(this, args):
    t = make_jstime(this)
    return t.msec()


# 15.9.5.26
@w_return
def get_timezone_offset(this, args):
    t = make_jstime(this)
    offset = -1 * t.utc_offset() / 60
    return offset


def _assert_date(obj):
    if obj.klass() != 'date':
        from js.exception import JsTypeError
        msg = '%s is not an instnace of Date'
        raise JsTypeError(unicode(msg))


# 15.9.5.27
@w_return
def set_time(this, args):
    _assert_date(this)
    from js.jsobj import W_DateObject
    assert isinstance(this, W_DateObject)
    arg0 = get_arg(args, 0)
    this._primitive_value_ = arg0
    return arg0


# 15.9.5.28
@w_return
def set_milliseconds(this, args):
    time_args = to_timeargs(args, fMSEC)
    return change_wdate(this, time_args, local=True)


# 15.9.5.29
@w_return
def set_utc_milliseconds(this, args):
    time_args = to_timeargs(args, fMSEC)
    return change_wdate(this, time_args)


# 15.9.5.30
@w_return
def set_seconds(this, args):
    time_args = to_timeargs(args, fSEC)
    return change_wdate(this, time_args, local=True)


# 15.9.5.30
@w_return
def set_utc_seconds(this, args):
    time_args = to_timeargs(args, fSEC)
    return change_wdate(this, time_args)


# 15.9.5.32
@w_return
def set_minutes(this, args):
    time_args = to_timeargs(args, fMIN)
    return change_wdate(this, time_args, local=True)


# 15.9.5.33
@w_return
def set_utc_minutes(this, args):
    time_args = to_timeargs(args, fMIN)
    return change_wdate(this, time_args)


# 15.9.5.34
@w_return
def set_hours(this, args):
    time_args = to_timeargs(args, fHOUR)
    return change_wdate(this, time_args, local=True)


# 15.9.5.35
@w_return
def set_utc_hours(this, args):
    time_args = to_timeargs(args, fHOUR)
    return change_wdate(this, time_args)


# 15.9.5.36
@w_return
def set_date(this, args):
    date_args = to_dateargs(args, fDAY)
    return change_wdate(this, date_args, local=True)


# 15.9.5.37
@w_return
def set_utc_date(this, args):
    date_args = to_dateargs(args, fDAY)
    return change_wdate(this, date_args)


# 15.9.5.38
@w_return
def set_month(this, args):
    date_args = to_dateargs(args, fMONTH)
    return change_wdate(this, date_args, local=True)


# 15.9.5.39
@w_return
def set_utc_month(this, args):
    date_args = to_dateargs(args, fMONTH)
    return change_wdate(this, date_args)


# 15.9.5.38
@w_return
def set_full_year(this, args):
    date_args = to_dateargs(args, fYEAR)
    return change_wdate(this, date_args, local=True)


# 15.9.5.39
@w_return
def set_utc_full_year(this, args):
    date_args = to_dateargs(args, fYEAR)
    return change_wdate(this, date_args)


# B.2.4
@w_return
def get_year(this, args):
    t = make_jstime(this)
    y = t.year(local=True) - 1900
    return y


# B.2.5
@w_return
def set_year(this, args):
    arg0 = get_arg(args, 0)
    year = arg0.ToInteger()

    if isnan(year) or year < 0 or year > 99:
        this.set_primitive_value(_w(NAN))
        return NAN

    y = year + 1900
    c = JsDateChange()
    c.set_year(y)
    change_wdate(this, c)
    return y


# 15.9.5.42
@w_return
def to_utc_string(this, args):
    t = make_jstime(this)
    s = t.strftime('%c %z')
    return s


# B.2.6
@w_return
def to_gmt_string(this, args):
    return to_utc_string(this, args)


# 15.9.4.2
@w_return
def parse(this, args):
    raise NotImplementedError()


# 15.9.4.3
@w_return
def utc(this, args):
    raise NotImplementedError()

####### helper


def to_timeargs(args, fill):
    a = w_argi(args)
    c = JsDateChange()
    ac = len(a)

    if fill == fMSEC:
        c.set_msecond(a[0])
    elif fill == fSEC:
        c.set_second(a[0])
        if ac > 1:
            c.set_msecond(a[1])
    elif fill == fMIN:
        c.set_minute(a[0])
        if ac > 1:
            c.set_second(a[1])
        if ac > 2:
            c.set_msecond(a[2])
    elif fill == fHOUR:
        c.set_hour(a[0])
        if ac > 1:
            c.set_minute(a[1])
        if ac > 2:
            c.set_second(a[2])
        if ac > 3:
            c.set_msecond(a[3])

    return c


def to_dateargs(args, fill):
    a = w_argi(args)
    c = JsDateChange()
    ac = len(a)

    if fill == fDAY:
        c.set_day(a[0])
    elif fill == fMONTH:
        c.set_month(a[0])
        if ac > 1:
            c.set_day(a[1])
    elif fill == fYEAR:
        c.year = a[0]
        if ac > 1:
            c.set_month(a[1])
        if ac > 2:
            c.set_day(a[2])

    return c


class JsDateChange(object):
    year = 0
    has_year = False
    month = 0
    has_month = False
    day = 0
    has_day = False
    hour = 0
    has_hour = False
    minute = 0
    has_minute = False
    second = 0
    has_second = False
    msecond = 0
    has_msecond = False

    def set_year(self, year):
        self.has_year = True
        self.year = year

    def set_month(self, month):
        self.has_month = True
        self.month = month

    def set_day(self, day):
        self.has_day = True
        self.day = day

    def set_hour(self, hour):
        self.has_hour = True
        self.hour = hour

    def set_minute(self, minute):
        self.has_minute = True
        self.minute = minute

    def set_second(self, second):
        self.has_second = True
        self.second = second

    def set_msecond(self, msecond):
        self.has_msecond = True
        self.msecond = msecond


def change_wdate(w_date, time_change, local=False):
    t = make_jstime(w_date)

    if time_change.has_year:
        t.set_year(time_change.year, local)

    if time_change.has_month:
        t.set_month(time_change.month, local)

    if time_change.has_day:
        t.set_day(time_change.day, local)

    if time_change.has_hour:
        t.set_hour(time_change.hour, local)

    if time_change.has_minute:
        t.set_min(time_change.minute, local)

    if time_change.has_second:
        t.set_sec(time_change.second, local)

    if time_change.has_msecond:
        t.set_msec(time_change.msecond, local)

    w_t = _w(t.to_msec_epoc())
    w_date.set_primitive_value(w_t)

    return w_t


def w_argi(args):
    argi = []
    for arg in args:
        a = arg.ToInteger()
        assert isinstance(a, int)
        argi += [a]
    return argi


def _change_tuple(t, idx, value):
    assert len(t) == 9
    l = list(t)
    l[idx] = value
    return (l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8])


def _get_tuple_at(t, idx):
    l = list(t)
    return l[idx]


class JsTime(object):
    def __init__(self, msec_timestamp):
        self._timep = msec_timestamp / 1000
        self._msec = msec_timestamp - self._timep * 1000

    def __str__(self):
        return 'JsTime(%d)' % (self.to_msec_epoc(), )

    def _get_time(self, local):
        if local:
            return self.localtime()
        return self.gmtime()

    def gmtime(self):
        return rtime.gmtime(self._timep)

    def localtime(self):
        return rtime.localtime(self._timep)

    def _set_time(self, tm, local):
        if local:
            self._timep = int(rtime.mktime(tm))
        else:
            self._timep = int(rtime.timegm(tm))

    def _update_time(self, component, value, local):
        tm = self._get_time(local)
        new_tm = _change_tuple(tm, component, value)
        self._set_time(new_tm, local)

    def _get_time_component(self, component, local):
        return _get_tuple_at(self._get_time(local), component)

    def _get_timestamp(self):
        return self._timep

    def to_msec_epoc(self):
        return (self._get_timestamp() * 1000) + (self.msec())

    def year(self, local=False):
        return self._get_time_component(rtime.tmYEAR, local)

    def set_year(self, year, local=False):
        self._update_time(rtime.tmYEAR, year, local)

    def month(self, local=False):
        return self._get_time_component(rtime.tmMONTH, local)

    def set_month(self, month, local=False):
        self._update_time(rtime.tmMONTH, month, local)

    def day(self, local=False):
        return self._get_time_component(rtime.tmDAY, local)

    def set_day(self, day, local=False):
        self._update_time(rtime.tmDAY, day, local)

    def hour(self, local=False):
        return self._get_time_component(rtime.tmHOUR, local)

    def set_hour(self, hour, local=False):
        self._update_time(rtime.tmHOUR, hour, local)

    def min(self, local=False):
        return self._get_time_component(rtime.tmMIN, local)

    def set_min(self, min, local=False):
        self._update_time(rtime.tmMIN, min, local)

    def sec(self, local=False):
        return self._get_time_component(rtime.tmSEC, local)

    def set_sec(self, sec, local=False):
        self._update_time(rtime.tmSEC, sec, local)

    def msec(self, local=False):
        return self._msec

    def set_msec(self, msec, local=False):
        assert msec < 1000
        self._msec = msec

    def wday(self, local=False):
        return self._get_time_component(rtime.tmWDAY, local)

    def strftime(self, format, local=False):
        tm = self._get_time(local)
        s = rtime.strftime(format, tm)
        return s

    def utc_offset(self):
        o = rtime.mktime(self.localtime()) - rtime.mktime(self.gmtime())
        return o


def make_jstime(w_obj):
    msecs = w_obj.PrimitiveValue().ToInteger()
    return JsTime(msecs)

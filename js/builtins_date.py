from pypy.rlib.rfloat import NAN, isnan
from js.jsobj import _w

import time
import datetime
from js.builtins import get_arg
from js.object_space import w_return, hide_on_translate
from pypy.rlib.objectmodel import we_are_translated


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

    put_property(w_Date, u'prototype', w_DatePrototype, writable = False, enumerable = False, configurable = False)

    put_native_function(w_Date, u'parse', parse)

    put_native_function(w_Date, u'UTC', parse)

@w_return
def to_string(this, args):
    if not we_are_translated():
        d = w_date_to_datetime(this)
        local = to_local(d)

        s = local.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)')
        return s

    return this.PrimitiveValue().to_string()

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
@hide_on_translate(0)
def get_full_year(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.year


# 15.9.5.11
@w_return
@hide_on_translate(0)
def get_utc_full_year(this, args):
    d = w_date_to_datetime(this)
    return d.year


# 15.9.5.12
@w_return
@hide_on_translate(0)
def get_month(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.month


# 15.9.5.13
@w_return
@hide_on_translate(0)
def get_utc_month(this, args):
    d = w_date_to_datetime(this)
    return d.day


# 15.9.5.14
@w_return
@hide_on_translate(0)
def get_date(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.day


# 15.9.5.15
@w_return
@hide_on_translate(0)
def get_utc_date(this, args):
    d = w_date_to_datetime(this)
    return d.day


# 15.9.5.16
@w_return
@hide_on_translate(0)
def get_day(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.weekday()


# 15.9.5.17
@w_return
@hide_on_translate(0)
def get_utc_day(this, args):
    d = w_date_to_datetime(this)
    return d.weekday()


# 15.9.5.18
@w_return
@hide_on_translate(0)
def get_hours(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.hour


# 15.9.5.19
@w_return
@hide_on_translate(0)
def get_utc_hours(this, args):
    d = w_date_to_datetime(this)
    return d.hour


# 15.9.5.20
@w_return
@hide_on_translate(0)
def get_minutes(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.minute


# 15.9.5.21
@w_return
@hide_on_translate(0)
def get_utc_minutes(this, args):
    d = w_date_to_datetime(this)
    return d.minute


# 15.9.5.22
@w_return
@hide_on_translate(0)
def get_seconds(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.second


# 15.9.5.23
@w_return
@hide_on_translate(0)
def get_utc_seconds(this, args):
    d = w_date_to_datetime(this)
    return d.second


# 15.9.5.24
@w_return
@hide_on_translate(0)
def get_milliseconds(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.microsecond / 1000


# 15.9.5.25
@w_return
@hide_on_translate(0)
def get_utc_milliseconds(this, args):
    d = w_date_to_datetime(this)
    return d.microsecond / 1000


# 15.9.5.26
@w_return
@hide_on_translate(0)
def get_timezone_offset(this, args):
    d = w_date_to_datetime(this)
    offset = -1 * (d.utcoffset().total_seconds() / 60)
    return offset


# 15.9.5.27
@w_return
def set_time(this, args):
    arg0 = get_arg(args, 0)
    this._primitive_value_ = arg0
    return arg0

# 15.9.5.28
@w_return
@hide_on_translate(0)
def set_milliseconds(this, args):
    time_args = to_timeargs(args, 1)
    return set_datetime(this, time_args)


# 15.9.5.29
@w_return
@hide_on_translate(0)
def set_utc_milliseconds(this, args):
    time_args = to_timeargs(args, 1)
    return set_utc_datetime(this, time_args)


# 15.9.5.30
@w_return
@hide_on_translate(0)
def set_seconds(this, args):
    time_args = to_timeargs(args, 2)
    return set_datetime(this, time_args)


# 15.9.5.30
@w_return
@hide_on_translate(0)
def set_utc_seconds(this, args):
    time_args = to_timeargs(args, 2)
    return set_utc_datetime(this, time_args)


# 15.9.5.32
@w_return
@hide_on_translate(0)
def set_minutes(this, args):
    time_args = to_timeargs(args, 3)
    return set_datetime(this, time_args)


# 15.9.5.33
@w_return
@hide_on_translate(0)
def set_utc_minutes(this, args):
    time_args = to_timeargs(args, 3)
    return set_utc_datetime(this, time_args)


# 15.9.5.34
@w_return
@hide_on_translate(0)
def set_hours(this, args):
    time_args = to_timeargs(args, 4)
    return set_datetime(this, time_args)


# 15.9.5.35
@w_return
@hide_on_translate(0)
def set_utc_hours(this, args):
    time_args = to_timeargs(args, 4)
    return set_utc_datetime(this, time_args)


# 15.9.5.36
@w_return
@hide_on_translate(0)
def set_date(this, args):
    date_args = to_dateargs(args, 1)
    return set_datetime(this, date_args)


# 15.9.5.37
@w_return
@hide_on_translate(0)
def set_utc_date(this, args):
    date_args = to_dateargs(args, 1)
    return set_utc_datetime(this, date_args)


# 15.9.5.38
@w_return
@hide_on_translate(0)
def set_month(this, args):
    date_args = to_dateargs(args, 2)
    return set_datetime(this, date_args)


# 15.9.5.39
@w_return
@hide_on_translate(0)
def set_utc_month(this, args):
    date_args = to_dateargs(args, 2)
    return set_utc_datetime(this, date_args)


# 15.9.5.38
@w_return
@hide_on_translate(0)
def set_full_year(this, args):
    date_args = to_dateargs(args, 3)
    return set_datetime(this, date_args)


# 15.9.5.39
@w_return
@hide_on_translate(0)
def set_utc_full_year(this, args):
    date_args = to_dateargs(args, 3)
    return set_utc_datetime(this, date_args)


# B.2.4
@w_return
@hide_on_translate(0)
def get_year(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    y = local.year - 1900
    return y


# B.2.5
@w_return
@hide_on_translate(0)
def set_year(this, args):
    arg0 = get_arg(args, 0)
    year = arg0.ToInteger()

    if isnan(year) or year < 0 or year > 99:
        this.set_primitive_value(NAN)
        return NAN

    y = year + 1900

    return set_datetime(this, [y])


# 15.9.5.42
@w_return
@hide_on_translate(0)
def to_utc_string(this, args):
    d = w_date_to_datetime(this)
    s = d.strftime('%c %z')
    return s


# B.2.6
@w_return
@hide_on_translate(0)
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

def to_timeargs(args, count):
    a = argv(args)
    rfilled = rfill_args(a, count)
    lfilled = lfill_args(rfilled, 7)
    return lfilled

def to_dateargs(args, count):
    a = argv(args)
    rfilled = rfill_args(a, count)
    lfilled = lfill_args(rfilled, 3)
    return lfilled

def set_datetime(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    new_d = change_datetime(local, *args)

    u = datetime_to_msecs(new_d)
    this.set_primitive_value(u)

    return u

def set_utc_datetime(this, args):
    d = w_date_to_datetime(this)
    new_d = change_datetime(d, *args)

    u = datetime_to_msecs(new_d)
    this.set_primitive_value(u)

    return u

def argv(args):
    return [arg.ToInteger() for arg in args]

def lfill_args(args, count):
    if count > 0:
        missing = count - len(args)
        return ([None] * missing) + args
    return args

def rfill_args(args, count):
    if count > 0:
        missing = count - len(args)
        return args + ([None] * missing)

    return args

def change_datetime(d, year = None, month = None, day = None, hour = None, minute = None, second = None, ms = None ):
    args = {}
    if year is not None:
        args['year'] = year
    if month is not None:
        args['month'] = month
    if day is not None:
        args['day'] = day
    if hour is not None:
        args['hour'] = hour
    if minute is not None:
        args['minute'] = minute
    if second is not None:
        args['second'] = second
    if ms is not None:
        mu_sec = ms * 1000
        args['microsecond'] = mu_sec
    return d.replace(**args)

def w_date_to_datetime(w_date):
    msecs = w_date.PrimitiveValue().ToInteger()
    return msecs_to_datetime(msecs)

def msecs_to_datetime(timestamp_msecs):
    from dateutil.tz import tzutc

    seconds_since_epoch = timestamp_msecs / 1000
    msecs = timestamp_msecs - seconds_since_epoch * 1000
    timestamp = seconds_since_epoch + (msecs / 1000.0)
    utc = datetime.datetime.utcfromtimestamp(timestamp)
    utc = utc.replace(tzinfo = tzutc())

    return utc

def datetime_to_msecs(d):
    from time import mktime
    timestamp = int(mktime(d.utctimetuple()))
    msecs = timestamp * 1000
    msecs += (d.microsecond / 1000)
    return msecs

def to_local(datetime):
    from dateutil.tz import tzlocal
    return datetime.astimezone(tzlocal())

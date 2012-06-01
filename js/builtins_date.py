from pypy.rlib.rfloat import NAN, isnan

import time
import datetime
from js.builtins import get_arg

def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.builtins_number import w_NAN
    from js.jsobj import W_DateObject, W_DateConstructor, W__Object
    ##Date
    # 15.9.5

    w_DatePrototype = W_DateObject(w_NAN)
    w_DatePrototype._prototype_ = W__Object._prototype_

    W_DateObject._prototype_ = w_DatePrototype

    def putf(name, func):
        put_native_function(w_DatePrototype, name, func)

    putf('toString', to_string)

    putf('valueOf', value_of)

    putf('getTime', get_time)

    putf('getFullYear', get_full_year)
    putf('getUTCFullYear', get_utc_full_year)

    putf('getMonth', get_month)
    putf('getUTCMonth', get_utc_month)

    putf('getDate', get_date)
    putf('getUTCDate', get_utc_date)

    putf('getDay', get_day)
    putf('getUTCDay', get_utc_day)

    putf('getHours', get_hours)
    putf('getUTCHours', get_utc_hours)

    putf('getMinutes', get_minutes)
    putf('getUTCMinutes', get_utc_minutes)

    putf('getSeconds', get_seconds)
    putf('getUTCSeconds', get_utc_seconds)

    putf('getMilliseconds', get_milliseconds)
    putf('getUTCMilliseconds', get_utc_milliseconds)

    putf('getTimezoneOffset', get_timezone_offset)

    putf('setTime', set_time)

    putf('setMilliseconds', set_milliseconds)
    putf('setUTCMilliseconds', set_utc_milliseconds)

    putf('setSeconds', set_seconds)
    putf('setUTCSeconds', set_utc_seconds)

    putf('setMinutes', set_minutes)
    putf('setUTCMinutes', set_utc_minutes)

    putf('setHours', set_hours)
    putf('setUTCHours', set_utc_hours)

    putf('setDate', set_date)
    putf('setUTCDate', set_utc_date)

    putf('setMonth', set_month)
    putf('setUTCMonth', set_utc_month)

    putf('setFullYear', set_full_year)
    putf('setUTCFullYear', set_utc_full_year)

    putf('getYear', get_year)
    putf('setYear', set_year)

    putf('toUTCString', to_utc_string)
    putf('toGMTString', to_gmt_string)

    # 15.9.3
    w_Date = W_DateConstructor()
    put_property(global_object, 'Date', w_Date)

    put_property(w_Date, 'prototype', w_DatePrototype, writable = False, enumerable = False, configurable = False)

    put_native_function(w_Date, 'parse', parse)

    put_native_function(w_Date, 'UTC', parse)

def to_string(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    s = local.strftime('%c %z')
    return s

# 15.9.5.8
def value_of(this, args):
    return get_time(this, args)

# 15.9.5.9
def get_time(this, args):
    return this.PrimitiveValue()

# 15.9.5.10
def get_full_year(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.year

# 15.9.5.11
def get_utc_full_year(this, args):
    d = w_date_to_datetime(this)
    return d.year

# 15.9.5.12
def get_month(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.month

# 15.9.5.13
def get_utc_month(this, args):
    d = w_date_to_datetime(this)
    return d.day

# 15.9.5.14
def get_date(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.day

# 15.9.5.15
def get_utc_date(this, args):
    d = w_date_to_datetime(this)
    return d.day

# 15.9.5.16
def get_day(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.weekday()

# 15.9.5.17
def get_utc_day(this, args):
    d = w_date_to_datetime(this)
    return d.weekday()

# 15.9.5.18
def get_hours(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.hour

# 15.9.5.19
def get_utc_hours(this, args):
    d = w_date_to_datetime(this)
    return d.hour

# 15.9.5.20
def get_minutes(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.minute

# 15.9.5.21
def get_utc_minutes(this, args):
    d = w_date_to_datetime(this)
    return d.minute

# 15.9.5.22
def get_seconds(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.second

# 15.9.5.23
def get_utc_seconds(this, args):
    d = w_date_to_datetime(this)
    return d.second

# 15.9.5.24
def get_milliseconds(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    return local.microsecond / 1000

# 15.9.5.25
def get_utc_milliseconds(this, args):
    d = w_date_to_datetime(this)
    return d.microsecond / 1000

# 15.9.5.26
def get_timezone_offset(this, args):
    d = w_date_to_datetime(this)
    offset = -1 * (d.utcoffset().to_seconds() / 60)
    return offset

# 15.9.5.27
def set_time(this, args):
    arg0 = get_arg(args, 0)
    this._primitive_value_ = arg0
    return arg0

# 15.9.5.28
def set_milliseconds(this, args):
    time_args = to_timeargs(args, 1)
    return set_datetime(this, time_args)

# 15.9.5.29
def set_utc_milliseconds(this, args):
    time_args = to_timeargs(args, 1)
    return set_utc_datetime(this, time_args)

# 15.9.5.30
def set_seconds(this, args):
    time_args = to_timeargs(args, 2)
    return set_datetime(this, time_args)

# 15.9.5.30
def set_utc_seconds(this, args):
    time_args = to_timeargs(args, 2)
    return set_utc_datetime(this, time_args)

# 15.9.5.32
def set_minutes(this, args):
    time_args = to_timeargs(args, 3)
    return set_datetime(this, time_args)

# 15.9.5.33
def set_utc_minutes(this, args):
    time_args = to_timeargs(args, 3)
    return set_utc_datetime(this, time_args)

# 15.9.5.34
def set_hours(this, args):
    time_args = to_timeargs(args, 4)
    return set_datetime(this, time_args)

# 15.9.5.35
def set_utc_hours(this, args):
    time_args = to_timeargs(args, 4)
    return set_utc_datetime(this, time_args)

# 15.9.5.36
def set_date(this, args):
    date_args = to_dateargs(args, 1)
    return set_datetime(this, date_args)

# 15.9.5.37
def set_utc_date(this, args):
    date_args = to_dateargs(args, 1)
    return set_utc_datetime(this, date_args)

# 15.9.5.38
def set_month(this, args):
    date_args = to_dateargs(args, 2)
    return set_datetime(this, date_args)

# 15.9.5.39
def set_utc_month(this, args):
    date_args = to_dateargs(args, 2)
    return set_utc_datetime(this, date_args)

# 15.9.5.38
def set_full_year(this, args):
    date_args = to_dateargs(args, 3)
    return set_datetime(this, date_args)

# 15.9.5.39
def set_utc_full_year(this, args):
    date_args = to_dateargs(args, 3)
    return set_utc_datetime(this, date_args)

# B.2.4
def get_year(this, args):
    d = w_date_to_datetime(this)
    local = to_local(d)
    y = local.year - 1900
    return y

# B.2.5
def set_year(this, args):
    arg0 = get_arg(args, 0)
    year = arg0.ToInteger()

    if isnan(year) or year < 0 or year > 99:
        this.set_primitive_value(NAN)
        return NAN

    y = year + 1900

    return set_datetime(this, [y])

# 15.9.5.42
def to_utc_string(this, args):
    d = w_date_to_datetime(d)
    s = d.strftime('%c %z')
    return s

# B.2.6

def to_gmt_string(this, args):
    return to_utc_string(this, args)

# 15.9.4.2
def parse(this, args):
    raise NotImplementedError()

# 15.9.4.3
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

from __future__ import print_function
import argparse
import datetime
import json
import os
import sys
import traceback

def enum(**enums):
    return type('Enum', (), enums)

Verbosity = enum(ERROR=0, INFO=1, DEBUG=2, TRACE=3)

_VERBOSE_LEVEL = 0

def get_verbosity(verbosity):
    if verbosity == Verbosity.ERROR:
        return 'ERROR'
    if verbosity == Verbosity.INFO:
        return 'INFO'
    if verbosity == Verbosity.DEBUG:
        return 'DEBUG'
    if verbosity == Verbosity.TRACE:
        return 'TRACE'
    return None

def verbose_print(verbosity, msg):
    if verbosity > _VERBOSE_LEVEL:
        return
    print('{0}: {1}'.format(get_verbosity(verbosity), msg))

_DATE_CONVERSION_FMT = '%Y-%m-%d'

def _from_date(value, include_weekday=False):
    if not include_weekday:
        fmt_str = '{0:' + _DATE_CONVERSION_FMT + '}'
        return fmt_str.format(value)
    else:
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fmt_str = '{0:' + _DATE_CONVERSION_FMT + '} ({1})'
        return fmt_str.format(value, weekdays[value.weekday()])

def _to_date(value):
    return datetime.datetime.strptime(value, _DATE_CONVERSION_FMT).date()

def _is_date(date_str):
    try:
        if date_str.lower() == 'today':
            return datetime.date.today()
        elif date_str.lower() == 'yesterday':
            return datetime.date.today() - datetime.timedelta(days=1)
        elif date_str.lower() == 'tomorrow':
            return datetime.date.today() + datetime.timedelta(days=1)
        else:
            return _to_date(date_str)
    except:
        raise argparse.ArgumentTypeError('date value is invalid')

def _is_percentage(percentage_str):
    try:
        percentage = int(percentage_str)
        if percentage < 1 or percentage > 100:
            raise 'error'
        return percentage_str
    except:
        raise argparse.ArgumentTypeError('percentage value is invalid (try a number between 1 and 100)')

def _parse_args():
    description = 'Calculate prescription refill date'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-d', '--days', metavar='<NUMBER>', default=30, type=int, help='total number of days in prescription')
    parser.add_argument('-s', '--start_date', metavar='<YYYY-MM-DD>', default=datetime.date.today(), type=_is_date, help='date of the usage')
    parser.add_argument('-p', '--percentage', metavar='<NUMBER>', default='80', type=_is_percentage, help='percentage of prescription before a refill')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')

    args = parser.parse_args()
    global _VERBOSE_LEVEL
    _VERBOSE_LEVEL = args.verbose
    verbose_print(Verbosity.INFO, 'verbose: {0}, days: {1}, start date: {2}, percentage: {3}' \
            .format(args.verbose, args.days, args.start_date, args.percentage))

    return args.days, args.start_date, int(args.percentage)

def _get_refill_date(days, start_date, percentage):
    num_days = (days * percentage) / 100
    return start_date + datetime.timedelta(days=num_days)

def main():
    days, start_date, percentage = _parse_args()
    
    try:
        print('Refill date: {0}'.format(_from_date(_get_refill_date(days, start_date, percentage), True)))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

from ansimarkup import AnsiMarkup, parse
import csv
import datetime
import operator
import os
from pathlib import Path
import re
import sys
import traceback

_VERBOSE = False
user_tags = {
    'error' : parse('<bold><red>'),
    'name'  : parse('<bold><cyan>'),
    'value' : parse('<bold><white>'),
}

am = AnsiMarkup(tags=user_tags)

def _assert_msg(msg):
    return am.ansistring(f'<error>{msg}</error>')

def _print_name_value(name, max_name_len, value, prefix=None, postfix=None):
    prefix = prefix if prefix is not None else ''
    postfix = postfix if postfix is not None else ''
    lh = am.ansistring(f'<name>{name}</name>')
    rh = am.ansistring(f'<value>{value}</value>')
    print(f'{prefix}{lh:{max_name_len + lh.delta}} {rh}{postfix}')

def _get_name_value_compact(name, max_name_len, value, prefix=None, postfix=None):
    prefix = prefix if prefix is not None else ''
    postfix = postfix if postfix is not None else ''
    return am.ansistring(f'{prefix}<name>{name}</name> <value>{value}</value>{postfix}')

def _get_timezone_info():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

def _convert_date_time(dt):
    return f'{dt:%d-%b-%Y %I:%M:%S%p %Z}'.replace('AM', 'am').replace('PM', 'pm')

def _parse_datetime(dt_str):
    dt = datetime.datetime.strptime(dt_str, '%m/%d/%Y %I:%M %p') # Example '11/08/2011 03:00 PM'
    tz = _get_timezone_info()
    return dt.replace(tzinfo=tz)

def _parse_datetime_row(row):
    return _parse_datetime(' '.join(row[2:4]))

def _parse_appointment_row(row, index):
    assert len(row) >= 4, _assert_msg(f'row {index} does not have 4 or more columns as required')
    appt_time = _parse_datetime(' '.join(row[2:4]))
    appt_type = row[0].title()
    doctor = row[1].title()
    return appt_time, appt_type, doctor

def parse_doctor_appointments(file_name):
    path = Path(os.path.expandvars(file_name))
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        sorted_rows = sorted(reader, key=lambda x: _parse_datetime_row(x))
        for index, row in enumerate(sorted_rows):
            yield _parse_appointment_row(row, index)

def get_doctors_appointments():
    MAX_WIDTH = len('Appointment:')
    file_name = '$HOME/Downloads/crump-visits.csv'
    for appt_time, appt_type, doctor in parse_doctor_appointments(file_name):
        s = _get_name_value_compact('Appointment:', None, _convert_date_time(appt_time), postfix=', ')
        s += _get_name_value_compact('Type:', None,  appt_type, postfix=', ')
        print(s + _get_name_value_compact('Doctor:', None, doctor))

def main(args):
    try:
        get_doctors_appointments()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

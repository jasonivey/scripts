#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import datetime
import datetime
import os
import sys
import traceback

import location_info
import network_info
import weather_info

def _get_current_time():
    local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    return [('Date & Time', '{:%A, %B %d %Y 🕰  %H:%M:%S %p (%Z)}'.format(datetime.datetime.now(local_timezone)))]

def get_login_info():
    datetime_info = _get_current_time()
    location = location_info.get_location()
    weather_report = weather_info.get_one_line_weather(location)
    weather_report = [tuple([part.strip() for part in weather_report.split(':')])] if weather_report else []
    system_info = network_info.get_system_info()
    return datetime_info + weather_report + system_info

def output_login_info(info):
    name_width = max([len(label) for (label, value) in info])
    for (label, value) in info:
        print(('%-' + str(name_width) + 's : %s') % (label, value))

def main():
    try:
        output_login_info(get_login_info())
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import json
import os
import re
import requests
import sys
import time
import traceback

import location_info

_TIME_OUT = 5.0
_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def _parse_args():
    descript = 'Get the weather info for the current area or one specified'
    parser = argparse.ArgumentParser(description=descript, formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=120))
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-f', '--full-report', action="store_true", help='output the full 3-day weather report instead of a nice one liner')
    location = parser.add_mutually_exclusive_group()
    location.add_argument('-z', '--zip-code', type=str, default=None, metavar='00000', help='the zip code')
    location.add_argument('-r', '--region', type=str, default=None, metavar='city state country', help='the general \'city state country\' region in quotes unless its a widely unique city like Paris')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    location = None
    if args.zip_code:
        location = args.zip_code
    elif args.region:
        location = args.region
    else:
        location = location_info.get_location()

    _verbose_print('INFO: args:\n  verbose: {}\n  full report: {}\n  zip code: {}\n  region: {}\n  location: {}' \
                   .format(args.verbose, args.full_report, args.zip_code, args.region, location))
    return location, args.full_report

def _call_uri(uri):
    try:
        _verbose_print('INFO: calling {} with a {} second timeout'.format(uri, _TIME_OUT))
        response = requests.get(uri, timeout=_TIME_OUT)
        response.raise_for_status()
        response_str = response.text.strip()
        return None if not response_str or response_str.find('Unknown location; please try') != -1 else response_str
    except requests.exceptions.RequestException as e:
        print('ERROR: error while calling {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
        return None

def _sun_event(match):
    #r'Sunrise: \g<1>, Sunset: \g<2>'
    sunrise_str = match.group('sunrise')
    sunrise = time.strptime(sunrise_str, '%H:%M:%S')
    sunrise_str = time.strftime('%I:%M:%S%p', sunrise).lower()
    sunset_str = match.group('sunset')
    sunset = time.strptime(sunset_str, '%H:%M:%S')
    sunset_str = time.strftime('%I:%M:%S%p', sunset).lower()
    return ', Sunrise: {},  Sunset: {}'.format(sunrise_str, sunset_str)

def get_one_line_weather(location):
    if location:
        uri = 'http://wttr.in/{}?u&format=%l:+%t+%c+%C+%w+%m+%S+%s&lang=en'.format(location.replace(' ', '%20'))
    else:
        uri =  'http://wttr.in/?u&format=%l:+%t+%c+%C+%w+%m+%S+%s&lang=en'
    report = _call_uri(uri)
    if not report: return None
    pattern = r'(?P<sunrise>\d{2}:\d{2}:\d{2}) (?P<sunset>\d{2}:\d{2}:\d{2})'
    weather_report = re.sub(pattern, _sun_event, report)
    return weather_report

def get_weather(location):
    if location:
        uri = 'http://wttr.in/{}?lang=en'.format(location.replace(' ', '%20'))
    else:
        uri = 'http://wttr.in/?lang=en'
    return _call_uri(uri)

def main():
    location, full_report = _parse_args()
    try:
        weather = get_weather(location) if full_report else get_one_line_weather(location)
        print(weather if weather else '')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())



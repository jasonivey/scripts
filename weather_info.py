#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import json
import os
import requests
import sys
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
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        print('ERROR: error while calling {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
        return None

def get_one_line_weather(location):
    uri = 'http://wttr.in/{}?format=%l:+%t+%c+%C+%w+%m&lang=en'.format(location.replace(' ', '%20'))
    return _call_uri(uri)

def get_weather(location):
    uri = 'http://wttr.in/{}?lang=en'.format(location.replace(' ', '%20'))
    return _call_uri(uri)

def main():
    location, full_report = _parse_args()
    try:
        weather = get_weather(location) if full_report else get_one_line_weather(location)
        if weather:
            print(weather)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())



#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import json
import os
import requests
import sys
import traceback

_ACCESS_KEY = '763cf4d76a80630696226732e87a186a'
_JSON_DATA = None
_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def _parse_args():
    parser = argparse.ArgumentParser(description='Get the IP address and location of where this script is running')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-i', '--ip-address', action="store_true", help='output the ip address')
    parser.add_argument('-l', '--location', action="store_true", help='output the location')
    #parser.add_argument('variable', nargs='*', help='specify which variables to print, if none are specified PATH will be printed')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    _verbose_print('INFO: args:\n  verbose: {}\n  ip address: {}\n  location: {}'.format(args.verbose, args.ip_address, args.location))
    return args.ip_address, args.location

def _call_ipstack_impl():
    json_data = None
    uri = 'http://api.ipstack.com/check?access_key={}&language=en&output=json'.format(_ACCESS_KEY)
    try:
        response = requests.get(uri, timeout=0.5)
        response.raise_for_status()
        json_data = response.json()
    except requests.exceptions.RequestException as e:
        print('ERROR: error while calling http://api.ipstack.com/check', file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
        return None
    except ValueError as e:
        print('ERROR: error while converting return body of http://api.ipstack.com/check into json', file=sys.stderr)
        return None
    return json_data

def _call_ipstack():
    global _JSON_DATA
    if not _JSON_DATA:
        _JSON_DATA = _call_ipstack_impl()
    if _JSON_DATA:
        _verbose_print('JSON Data from http://api.ipstack.com/check\n{}\n' \
                       .format(json.dumps(_JSON_DATA, sort_keys=True, indent=4)))
    return _JSON_DATA 

def get_ip_address():
    json_data = _call_ipstack()
    if not json_data: return None
    if 'ip' not in json_data:
        print('ERROR: ip address was not returned from call to http://api.ipstack.com/check', sys.stderr)
        return None
    external_ip = json_data['ip']
    _verbose_print('Router IP Address: {}'.format(external_ip))
    return external_ip

def get_location():
    json_data = _call_ipstack()
    if 'city' not in json_data or 'region_name' not in json_data or 'country_code' not in json_data:
        print('ERROR: \'city\' or \'region_name\' or \'country_code\' was not returned from call to http://api.ipstack.com/check', sys.stderr)
        return None
    location = '{} {} {}'.format(json_data['city'], json_data['region_name'], json_data['country_code'])
    _verbose_print('location: {}'.format(location))
    return location

def main():
    want_ip_address, want_location = _parse_args()
    try:
        if want_ip_address:
            ip_address = get_ip_address()
            if ip_address:
                print('Router IP Address: {}'.format(ip_address))
        if want_location:
            location = get_location()
            if location:
                print(location)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())


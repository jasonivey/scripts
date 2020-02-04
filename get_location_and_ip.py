#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import json
import os
import requests
import sys
import traceback

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

def _get_information(get_ip_address, get_location):
    ACCESS_KEY = '763cf4d76a80630696226732e87a186a'
    uri = 'http://api.ipstack.com/check?access_key={}&language=en&output=json'.format(ACCESS_KEY)
    response = requests.get(uri)
    response_json = json.loads(response.text)

    retval = ''
    if get_ip_address:
        if 'ip' not in response_json:
            raise Exception('ip address was not returned from call to http://api.ipstack.com/check')
        else:
            retval = 'External IP Address: {}'.format(response_json['ip'])
    if get_location:
        if 'city' not in response_json or 'region_name' not in response_json or 'country_code' not in response_json:
            raise Exception('location info was not returned from call to http://api.ipstack.com/check')
        else:
            if len(retval) > 0:
                retval += '\n{} {} {}'.format(response_json['city'], response_json['region_name'], response_json['country_code'])
            else:
                retval = '{} {} {}'.format(response_json['city'], response_json['region_name'], response_json['country_code'])
    if len(retval) == 0:
        retval = json.dumps(response_json, sort_keys=True, indent=4)

    return retval

def main():
    get_ip_address, get_location = _parse_args()
    try:
        print(_get_information(get_ip_address, get_location))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import json
import os
import requests
import sys
import traceback

_ACCESS_KEY = '763cf4d76a80630696226732e87a186a'
_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def _parse_args():
    parser = argparse.ArgumentParser(description='Get the IP address and location of where this script is running')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-i', '--info', nargs='+', action='append', help='Specify which ' \
                        'information to be retrieved.  Valid options are \'ip\',  \'location\' and \'geo\'.  Other options ' \
                        'will be ignored.')

    # The following command line produces args.info [[]]
    # For example:
    #  location_info.py -v -i ip location -i geo
    #  produces: args.info => [['ip', 'location'], ['geo']]
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    ip_address = any('ip' in info for info in args.info)
    location = any('location' in info for info in args.info)
    geo = any('geo' in info for info in args.info)

    _verbose_print('INFO: args:\n  verbose: {}\n  info: {}\n  ip address: {}\n  location: {}\n  geo: {}'
                   .format(args.verbose, args.info, ip_address, location, geo))

    if not ip_address and not location and not geo:
        parser.error(message='ERROR: the --info argument must be used with either \'ip\', \'location\', \'geo\'')

    return ip_address, location, geo

def _call_ipstack():
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

def _get_ip_address(json_data):
    if not json_data: return None
    if 'ip' not in json_data:
        print('ERROR: ip address was not returned from call to http://api.ipstack.com/check', sys.stderr)
        return None
    external_ip = json_data['ip']
    _verbose_print('Router IP Address: {}'.format(external_ip))
    return external_ip

def get_ip_address():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_ip_address(json_data)

def _get_location(json_data):
    if 'city' not in json_data or 'region_name' not in json_data or 'country_code' not in json_data:
        print('ERROR: \'city\' or \'region_name\' or \'country_code\' was not returned from call to http://api.ipstack.com/check', sys.stderr)
        return None
    location = '{} {} {}'.format(json_data['city'], json_data['region_name'], json_data['country_code'])
    _verbose_print('location: {}'.format(location))
    return location

def get_location():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_location(json_data)

def _get_geo_location(json_data):
    if 'latitude' not in json_data or 'longitude' not in json_data:
        print('ERROR: \'latitude\' or \'longitude\' was not returned from call to http://api.ipstack.com/check', sys.stderr)
        return None
    geo_location = '{},{}'.format(json_data['latitude'], json_data['longitude'])
    _verbose_print('geo location: {}'.format(geo_location))
    return geo_location

def get_geo_location():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_geo_location(json_data)

def get_information(want_ip_address, want_location, want_geo):
    json_data = _call_ipstack()
    if not json_data:
        return None

    _verbose_print('JSON Data from http://api.ipstack.com/check\n{}\n' \
                   .format(json.dumps(json_data, sort_keys=True, indent=4)))

    if want_ip_address:
        ip_address = _get_ip_address(json_data)
        if ip_address:
            print('Router IP Address: {}'.format(ip_address))
    if want_location:
        location = _get_location(json_data)
        if location:
            print(location)
    if want_geo:
        geo_location = _get_geo_location(json_data)
        if geo_location:
            print(geo_location)

def main():
    want_ip_address, want_location, want_geo = _parse_args()
    try:
        get_information(want_ip_address, want_location, want_geo)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())


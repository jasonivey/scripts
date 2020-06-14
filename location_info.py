#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import ipaddress
import json
import os
import requests
import sys
import traceback

_VERBOSE = False

_ACCESS_KEY = '763cf4d76a80630696226732e87a186a'

_EXTERNAL_IPV4_URLS = ['http://v4.showip.spamt.net/',
                       'http://ipecho.net/plain',
                       'http://ident.me/v4'
                       'http://ipv4.icanhazip.com',
                       'http://checkip.amazonaws.com',
                       'http://ifconfigme.com',]

_EXTERNAL_IPV6_URLS = ['http://smart-ip.net/myip',
                       'http://ident.me/v6',
                       'http://icanhazip.com',
                       'http://ipv6.icanhazip.com',]

_IP_STACK_URI = 'http://api.ipstack.com/check?access_key={}&language=en&output=json'.format(_ACCESS_KEY)

_IP_ADDRESS_V4 = 1
_IP_ADDRESS_V6 = 2
_IP_ADDRESS_EITHER = 4

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def _parse_args():
    parser = argparse.ArgumentParser(description='Query various location information about where this script is running')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-i', '--info', nargs='+', action='append', required=True, choices=['ip', 'location', 'zip-code', 'gps'],
                        help='Specify which information should to be queried.')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    ip_address = any('ip' in info for info in args.info)
    location = any('location' in info for info in args.info)
    zip_code = any('zip-code' in info for info in args.info)
    gps = any('gps' in info for info in args.info)

    _verbose_print('INFO: args:\n  verbose: {}\n  info: {}\n  ip address: {}\n  location: {}\n  zip code: {}\n  gps: {}'
                   .format(args.verbose, args.info, ip_address, location, zip_code, gps))

    return ip_address, location, zip_code, gps

def _make_http_call(uri):
    try:
        response = requests.get(uri, timeout=0.5)
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        _verbose_print('ERROR: error while calling {}'.format(uri))
        _verbose_print('ERROR: {}'.format(e))
    return None

def _call_ipstack():
    response = _make_http_call(_IP_STACK_URI)
    return None if not response else json.loads(response)


def get_public_ip_address(version=_IP_ADDRESS_V4):
    if version == _IP_ADDRESS_V4:
        addresses = _EXTERNAL_IPV4_URLS[:]
    elif version == _IP_ADDRESS_V6:
        addresses = _EXTERNAL_IPV6_URLS[:]
    elif version == _IP_ADDRESS_EITHER:
        addresses = _EXTERNAL_IPV4_URLS[:] + _EXTERNAL_IPV6_URLS[:]

    for url in addresses:
        response = _make_http_call(url)
        if not response:
            _verbose_print('ERROR: error querying ip address while calling {}'.format(url))
            continue
        ip = ipaddress.ip_address(response)
        if version == _IP_ADDRESS_V4 and ip.version == 6:
            _verbose_print('ERROR: ip ({}) returned from {} is an IPv6 when IPv4 was requested'.format(ip, url))
            continue
        elif version == _IP_ADDRESS_V6 and ip.version == 4:
            _verbose_print('ERROR: ip ({}) returned from {} is an IPv4 when IPv6 was requested'.format(ip, url))
            continue
        else:
            _verbose_print('INFO: successfully found {} version IPv{} from {}'.format(ip, ip.version, url))
            return ip

def _parse_ipstack_json(json_data, parse_ip=False, parse_location=False, parse_zip_code=False, parse_gps=False):
    if not json_data: return dict()
    parsed_data = {}
    if parse_ip:
        if 'ip' not in json_data:
            _verbose_print('ERROR: ip address was not returned from call to {}'.format(_IP_STACK_URI), sys.stderr)
            return dict()
        parsed_data['ip'] = ipaddress.ip_address(json_data['ip'])
    if parse_location:
        if 'city' not in json_data or 'region_name' not in json_data or 'country_code' not in json_data:
            _verbose_print('ERROR: \'city\' or \'region_name\' or \'country_code\' was not returned from call to {}'.format(_IP_STACK_URI), sys.stderr)
            return dict()
        parsed_data['location'] = '{} {} {}'.format(json_data['city'], json_data['region_name'], json_data['country_code'])
    if parse_zip_code:
        if 'zip' not in json_data:
            _verbose_print('ERROR: zip code was not returned from call to {}'.format(_IP_STACK_URI), sys.stderr)
            return dict()
        parsed_data['zip_code'] = json_data['zip']
    if parse_gps:
        if 'latitude' not in json_data or 'longitude' not in json_data:
            _verbose_print('ERROR: \'latitude\' or \'longitude\' was not returned from call to {}'.format(_IP_STACK_URI), sys.stderr)
            return dict()
        parsed_data['gps'] = '{},{}'.format(json_data['latitude'], json_data['longitude'])
    return parsed_data

def _get_ip_address(json_data):
    parsed_data = _parse_ipstack_json(json_data, parse_ip=True)
    public_ip = parsed_data['ip'] if 'ip' in parsed_data else None
    if not public_ip or public_ip.version == 6:
        updated_ip = get_public_ip_address()
        if updated_ip:
            public_ip = updated_ip
    _verbose_print('public ip: {}'.format(public_ip))
    return str(public_ip)

def get_ip_address():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_ip_address(json_data)

def _get_location(json_data):
    parsed_data = _parse_ipstack_json(json_data, parse_location=True)
    location = parsed_data['location'] if 'location' in parsed_data else None
    _verbose_print('location: {}'.format(location))
    return location

def get_location():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_location(json_data)

def _get_zip_code(json_data):
    parsed_data = _parse_ipstack_json(json_data, parse_zip_code=True)
    zip_code = parsed_data['zip_code'] if 'zip_code' in parsed_data else None
    _verbose_print('zip code: {}'.format(zip_code))
    return zip_code

def get_zip_code():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_zip_code(json_data)

def _get_gps_location(json_data):
    parsed_data = _parse_ipstack_json(json_data, parse_gps=True)
    gps_location = parsed_data['gps'] if 'gps' in parsed_data else None
    _verbose_print('gps location: {}'.format(gps_location))
    return gps_location

def get_gps_location():
    json_data = _call_ipstack()
    if not json_data:
        return None
    return _get_gps_location(json_data)

def get_information(want_ip_address, want_location, want_zip_code, want_gps):
    json_data = _call_ipstack()
    if not json_data:
        return None

    _verbose_print('JSON Data from {}\n{}\n'.format(_IP_STACK_URI, json.dumps(json_data, sort_keys=True, indent=4)))

    if want_ip_address:
        ip_address = _get_ip_address(json_data)
        if ip_address:
            print('Public IP: {}'.format(ip_address))
    if want_location:
        location = _get_location(json_data)
        if location:
            print(location)
    if want_zip_code:
        zip_code = _get_zip_code(json_data)
        if zip_code:
            print(zip_code)
    if want_gps:
        gps_location = _get_gps_location(json_data)
        if gps_location:
            print(gps_location)

def main():
    want_ip_address, want_location, want_zip_code, want_gps = _parse_args()
    try:
        get_information(want_ip_address, want_location, want_zip_code, want_gps)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


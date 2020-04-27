#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import getpass
from lxml import etree
import os
import pprint
import requests
import sys
import traceback

import plex_auth_token

_VERBOSE = False

_TIME_OUT = 5.0
_SERVER_INFO_URI = 'https://plex.tv/pms/servers?X-Plex-Token={}'
_SERVER_INFO_XPATH = '/MediaContainer//Server'
_SERVER_ATTR_XPATH = ['@name', '@version', '@scheme', '@port',  '@localAddresses',
                      '@address',  '@machineIdentifier', '@createdAt', '@updatedAt']
_SERVER_ATTRS = ['name', 'version', 'scheme', 'port',  'localAddresses',
                 'address',  'machineIdentifier', 'createdAt', 'updatedAt']

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def create_argparse():
    auth_token_parser = plex_auth_token.create_argparse()
    descript = 'Call the local plex server to find how many people are logged in watching something'
    parser = argparse.ArgumentParser(description=descript, parents=[auth_token_parser], conflict_handler='resolve',
                                     formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=120))
    parser.add_argument('-t', '--token', metavar='TOKEN', default=None, help='a current plex auth token to avoid logging in agin')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    return parser

def get_plex_server_xml(token):
    uri = _SERVER_INFO_URI.format(token)
    try:
        _verbose_print('INFO: calling {} with a {} second timeout'.format(uri, _TIME_OUT))
        response = requests.get(uri, timeout=_TIME_OUT)
        response.raise_for_status()
        _verbose_print('INFO: body of request\n{}'.format(response.text.strip()))
        _verbose_print('INFO: response.headers: {}'.format(pprint.pformat(response.headers, compact=True)))
        if 'Content-Type' not in response.headers or response.headers['Content-Type'].find('xml') == -1:
            print('ERROR: the body of the http response was not xml as expected', file=sys.stderr)
            return None
        _verbose_print('INFO: treating response body as XML')
        root = etree.fromstring(response.text.strip().encode('utf-8'))
        etree.indent(root, level=0)
        _verbose_print('INFO: XML response body\n{}'.format(etree.tostring(root, pretty_print=True).decode('utf-8')))
        return root
    except Exception as e:
        print('ERROR: Exception raised while calling or processing GET {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
    return None

def parse_plex_server_xml(server_xml):
    properties = []
    find = etree.XPath(_SERVER_INFO_XPATH)
    for server in find(server_xml):
        properties.append({})
        #print('attributes: {}'.format(pprint.pformat(server.items())))
        for name, value in server.items():
            if name in _SERVER_ATTRS:
                properties[-1][name] = value
    for prop_dict in properties:
        prop_dict['localServerUrl'] = '{}://{}:{}'.format(prop_dict['scheme'], prop_dict['localAddresses'], prop_dict['port'])
        prop_dict['externalServerUrl'] = '{}://{}:{}'.format(prop_dict['scheme'], prop_dict['address'], prop_dict['port'])
    return properties

def get_plex_auth_token(username, password, token):
    return token if token else plex_auth_token.get_plex_auth_token(username, password)

def get_max_column_width(columns):
    return len(max(columns, key=len))

def parse_args(parser):
    args = parser.parse_args()
    token = args.token
    username = password = None
    if not token:
        username, password = plex_auth_token.parse_args(args=args)
    global _VERBOSE
    _VERBOSE = args.verbose
    token = args.token
    _verbose_print('Args:\n  Verbose: {}\n  User Name: {}\n  Password: {}\n  Token: {}' \
                   .format(_VERBOSE, username, password, token))
    return username, password, token

def main():
    parser = create_argparse()
    username, password, token = parse_args(parser)
    try:
        token = get_plex_auth_token(username, password, token)
        if not token:
            print('ERROR: no auth token was returned', file=sys.stderr)
            return 1
        xml_properties = get_plex_server_xml(token)
        servers_properties = parse_plex_server_xml(xml_properties)
        for server_properties in servers_properties:
            name_width = get_max_column_width(server_properties.keys())
            format_str = '{:>' + str(name_width) +'} : {}'
            print(format_str.format('Server', server_properties['name']))
            for name, value in server_properties.items():
                print(format_str.format(name, value))
            print("")
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())

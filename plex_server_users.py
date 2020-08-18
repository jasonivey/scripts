#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import getpass
import json
from lxml import etree
import os
import pprint
import re
import requests
import sys
import traceback

import plex_auth_token

_TIME_OUT = 5.0
_VERBOSE = False

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

def parse_args(parser):
    args = parser.parse_args()
    token = args.token
    username = password = None
    if not token:
        username, password = plex_auth_token.parse_args(args=args)
    global _VERBOSE
    _VERBOSE = args.verbose
    token = args.token
    printable_password = '*' * len(password) if password else ''
    _verbose_print(f'Args:\n  Verbose: {_VERBOSE}\n  User Name: {username}\n  Password: {printable_password}\n  Token: {token}')
    return username, password, token

def get_plex_auth_token(username, password, token):
    return token if token else plex_auth_token.get_plex_auth_token(username, password)

def _find_users(media_container):
    users = {}
    find = etree.XPath('/MediaContainer/*/User')
    for user in find(media_container):
        _verbose_print('INFO: found a user')
        user_id = user_name = None
        user_items = user.items()
        for user_item in user_items:
            if user_item[0] == 'id':
                user_id = int(user_item[1])
            elif user_item[0] == 'title':
                user_name = user_item[1]
        if user_id and user_name:
            _verbose_print('INFO: user id {}, user name {}'.format(user_id, user_name))
            if user_id not in users:
                users[user_id] = (user_name, 1)
            else:
                count = users[user_id][1]
                users[user_id] = (user_name, count + 1)
    return users

def get_plex_current_users(token):
    uri = 'http://192.168.1.180:32400/status/sessions?X-Plex-Token={}'.format(token)
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
        return _find_users(root)
    except Exception as e:
        print('ERROR: Exception raised while calling or processing GET {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
    return None

def main():
    parser = create_argparse()
    username, password, token = parse_args(parser)
    try:
        token = get_plex_auth_token(username, password, token)
        if not token:
            print('ERROR: no auth token was returned', file=sys.stderr)
            return 1
        users = get_plex_current_users(token)
        _verbose_print('INFO: users: {}'.format(pprint.pformat(users, compact=True)))
        print('Users:')
        if users == None or len(users) == 0:
            print('  no users online currently{}'.format('' if _is_verbose_mode_on() else ' (use --verbose for more information)'))
            users = {}
        for user_id, user_name_count in users.items():
            user_name = user_name_count[0]
            user_count = user_name_count[1]
            print('  {}: logged in {} time(s)'.format(user_name, user_count))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


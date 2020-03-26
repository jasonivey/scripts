#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import getpass
import json
import os
import pprint
import re
import requests
import sys
import traceback
import uuid

#http --form POST https://plex.tv/users/sign_in.json user[password]='stimpy01' user[login]='jasonivey@gmail.com' Content-Type:"application/x-www-form-urlencoded; charset=utf-8" X-Plex-Version:"1.18.8.2527" X-Plex-Product:"Plex Media Server" X-Plex-Client-Identifier:"$(uuidgen -r | sed s/-//g)"
#{"user":{"id":392288,"uuid":"50b305b32363dbc5","email":"jasonivey@gmail.com","joined_at":"2012-11-01T06:37:02Z","username":"jasonivey","title":"jasonivey","thumb":"https://plex.tv/users/50b305b32363dbc5/avatar?c=1565583099","hasPassword":true,"authToken":"gMo5mcFD33WdZMGxQt-x","authentication_token":"gMo5mcFD33WdZMGxQt-x","subscription":{"active":true,"status":"Active","plan":"yearly","features":["webhooks","camera_upload","home","pass","dvr","trailers","session_bandwidth_restrictions","music_videos","content_filter","adaptive_bitrate","sync","lyrics","cloudsync","premium_music_metadata","hardware_transcoding","session_kick","photos-metadata-edition","collections","radio","tuner-sharing","photos-favorites","hwtranscode","photosV6-tv-albums","photosV6-edit","federated-auth","item_clusters","livetv","Android - PiP","photos-v5","unsupportedtuners","kevin-bacon","client-radio-stations","imagga-v2","silence-removal","boost-voices","volume-leveling","sweet-fades","sleep-timer","TREBLE-show-features","web_server_dashboard","visualizers","premium-dashboard","conan_redirect_qa","conan_redirect_alpha","conan_redirect_beta","conan_redirect_public","news_local_now","nominatim","transcoder_cache","live-tv-support-incomplete-segments","dvr-block-unsupported-countries","companions_sonos","allow_dvr","signin_notification","signin_with_apple","drm_support","epg-recent-channels","spring_serve_ad_provider","conan_redirect_nightlies","conan_redirect_nightly"]},"roles":{"roles":["plexpass"]},"entitlements":["ios","all","roku","android","xbox_one","xbox_360","windows","windows_phone"],"confirmedAt":"2012-11-01T08:05:58Z","forumId":null,"rememberMe":false,"country":"US"}}

_TIME_OUT = 5.0
_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def _request_username():
    return input('User/email:')

def _request_password():
    return getpass.getpass()

def _parse_args():
    descript = 'Log into the plex.tv main app to retrieve the auth token for further API usage. User name/email and ' \
               'password are optional command line arguments. If they are missing they wil be safely prompted for later.'
    parser = argparse.ArgumentParser(description=descript, formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=120))
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-u', '--username', metavar='USER', help='the username/email to use to use to authorize')
    parser.add_argument('-p', '--password', metavar='PASSWORD', help='the password to use to authorize')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose
    username = args.username if args.username else _request_username()
    password = args.password if args.password else _request_password()
    _verbose_print('Args:\n  Verbose: {}\n  User Name: {}\n  Password: {}'.format(_VERBOSE, username, password))
    return username, password

def _generate_form_data(username, password):
    data = {}
    data['user[login]'] = username
    data['user[password]'] = password
    _verbose_print('data: {}'.format(pprint.pformat(data, compact=True)))
    return data

def _generate_headers():
    headers = {}
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8' 
    headers['X-Plex-Version'] = '1.18.8.2527'
    headers['X-Plex-Product'] = 'Plex Media Server'
    headers['X-Plex-Client-Identifier'] = str(uuid.uuid4()).replace('-', '')
    _verbose_print('headers: {}'.format(pprint.pformat(headers, compact=True)))
    return headers

def get_plex_auth_token(username, password):
    uri = 'https://plex.tv/users/sign_in.json' 
    headers = _generate_headers()
    data = _generate_form_data(username, password)
    try:
        _verbose_print('INFO: calling {} with a {} second timeout'.format(uri, _TIME_OUT))
        response = requests.post(uri, headers=headers, data=data, timeout=_TIME_OUT)
        response.raise_for_status()
        response_data = response.text.strip()
        _verbose_print('INFO: response.headers: {}'.format(pprint.pformat(response.headers, compact=True)))
        if 'Content-Type' in response.headers and response.headers['Content-Type'].find('json') != -1:
            _verbose_print('INFO: treating response data as JSON')
            response_data = response.json()
            _verbose_print('INFO: response data:\n{}'.format(json.dumps(response_data, sort_keys=True, indent=2)))
            if 'user' in response_data and 'authToken' in response_data['user']:
                return response_data['user']['authToken']
            else:
                print('ERROR: unable to find authToken in the JSON response')
        else:
            _verbose_print('INFO: treating response data as a regular string')
            response_data = response.text.strip()
            _verbose_print('INFO: response data:\n{}'.format(response_data))
            match = re.search(r'"authToken":"(?P<token>[^"]*)"', response_data)
            if match:
                return match.group('token')
            else:
                print('ERROR: did not find the authToken in the response', file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print('ERROR: error while calling {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
    except ValueError as e:
        print('ERROR: error while converting response to JSON from {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
    return None

def main():
    username, password = _parse_args()
    try:
        auth_token = get_plex_auth_token(username, password) 
        if auth_token:
            print('Auth Token: {}'.format(auth_token))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())


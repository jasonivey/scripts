#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import base64
import distro
import getpass
import json
import os
import platform
import pprint
import re
import requests
import sys
import subprocess
import traceback
import uuid

#http --form POST https://plex.tv/users/sign_in.json user[password]='********' user[login]='jasonivey@gmail.com' Content-Type:"application/x-www-form-urlencoded; charset=utf-8" X-Plex-Version:"1.18.8.2527" X-Plex-Product:"Plex Media Server" X-Plex-Client-Identifier:"$(uuidgen -r | sed s/-//g)"
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

def create_argparse():
    descript = 'Log into the plex.tv main app to retrieve the auth token for further API usage. User name/email and ' \
               'password are optional command line arguments. If they are missing they wil be safely prompted for later.'
    parser = argparse.ArgumentParser(description=descript, formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=120))
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-u', '--username', metavar='USER', help='the username/email to use to use to authorize')
    parser.add_argument('-p', '--password', metavar='PASSWORD', help='the password to use to authorize')
    return parser

def parse_args(parser=None, args=None):
    args = args if args else parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose
    username = args.username if args.username else _request_username()
    password = args.password if args.password else _request_password()
    _verbose_print('Args:\n  Verbose: {}\n  User Name: {}\n  Password: {}'.format(_VERBOSE, username, password))
    return username, password

def _generate_version_and_client_id():
    if sys.platform != 'linux':
        return '1.1.1.1', str(uuid.uuid4()).replace('-', '')

    command = 'dpkg -l | rg plexmediaserver | awk \'{ print $3 }\''
    process = subprocess.Popen(command, shell=True, bufsize=1, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdoutdata, stderrdata = process.communicate()
    plex_package_name = None if process.wait() != 0 else stdoutdata.decode('utf-8').strip()

    if plex_package_name and plex_package_name.find('-') != -1:
        version, client_id = plex_package_name.split('-')
    else:
        print('ERROR: retreiving Plex version', file=sys.stderr)
        print('ERROR: {}'.format(stderrdata.decode('utf-8').strip()), file=sys.stderr)
        version = '1.1.1.1'
        client_id = str(uuid.uuid4()).replace('-', '')
        _verbose_print('INFO: due to inability to find Plex version will now default to version {}, client id:{}' \
                       .format(version, client_id))

    _verbose_print('INFO: plex version {}, client id {}'.format(version, client_id))
    return version, client_id

def _generate_headers(username, password):
    version, client_id = _generate_version_and_client_id()
    distro_info = distro.linux_distribution()

    headers = {}
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8' 
    headers['X-Plex-Version'] = version 
    headers['X-Plex-Product'] = 'Plex Media Server'
    headers['X-Plex-Provides'] = 'server'
    headers['X-Plex-Platform'] = platform.system()
    headers['X-Plex-Platform-Version'] = platform.uname().release 
    headers['X-Plex-Device-Name'] = 'PlexMediaServer'
    headers['X-Plex-Device'] = '{} {}'.format(distro_info[0], distro_info[1])
    headers['X-Plex-Client-Identifier'] = client_id
    authorization_str = base64.b64encode('{}:{}'.format(username, password).encode('utf-8')).decode('utf-8')
    headers['Authorization'] = 'Basic {}'.format(authorization_str)
    _verbose_print('headers: {}'.format(pprint.pformat(headers, compact=True)))

    return headers

def get_plex_auth_token(username, password):
    uri = 'https://plex.tv/users/sign_in.json'
    headers = _generate_headers(username, password)

    try:
        _verbose_print('INFO: calling {} with a {} second timeout'.format(uri, _TIME_OUT))
        response = requests.post(uri, headers=headers, timeout=_TIME_OUT)
        response.raise_for_status()
        _verbose_print('INFO: response.headers: {}'.format(pprint.pformat(response.headers, compact=True)))
        if 'Content-Type' in response.headers and response.headers['Content-Type'].find('json') != -1:
            _verbose_print('INFO: treating response data as JSON')
            response_data = response.json()
            _verbose_print('INFO: response data:\n{}'.format(json.dumps(response_data, separators=(',', ':'),
                                                                        sort_keys=True, indent=None)))
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
                print('ERROR: unable to find the authToken in the response', file=sys.stderr)
    except Exception as e:
        print('ERROR: Exception raised while calling or processing POST {}'.format(uri), file=sys.stderr)
        print('ERROR: {}'.format(e), file=sys.stderr)
    return None

def main():
    parser = create_argparse()
    username, password = parse_args(parser=parser)
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


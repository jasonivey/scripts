#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import contextlib
import json
import os
import sys
import re
import subprocess
import traceback
import urllib2


def _parse_args():
    description = 'Validate version endpoints for dynamux URL\'s'
    parser = argparse.ArgumentParser(description=description)
#     parser.add_argument('-c', '--compiler', metavar='<compiler>', required=True, help='name of compiler (gcc/g++/clang++)')
#     parser.add_argument('-l', '--stdlib', metavar='<stdlib>', default='libstdc++', help='the standard library to use (libstdc++ or libc++)')
#     parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('-o', '--only-valid', default=False, action='store_true', help='Display only valid endpoints')
#     parser.add_argument('-f', '--option-file', type=_is_valid_file, help='path to .clang_complete file style file')
#     parser.add_argument('-o', '--option', nargs='*', help='specify an option to be passed to the compiler')
#     parser.add_argument('-k', '--keep', default=False, action='store_true', help='keep the generated source file when compiling header')
#     parser.add_argument('-b', '--break', dest='break_on_error', default=False, action='store_true', help='stop the compile after the first error')
#     parser.add_argument('source', type=_is_valid_source, nargs='+', help='source file or directory')
    args = parser.parse_args()
#     return args.compiler, args.stdlib, args.preprocessor, args.option_file, args.option, args.keep, args.break_on_error, args.source
    return args.only_valid

def _get_dynamux_raw_paths():
    paths = {
        'Keystore': ['d-gp2-ks-1.dev.movenetworks.com', None, 'key'], 
        'Keystore': ['d-gp2-ks-1.dev.movenetworks.com', None, None], 
        'DynaPack': ['d-gp2-dynpak-1.dev.movenetworks.com', 8000, None],
        'DynaAdmin': ['d-gp2-dynadm-1.dev.movenetworks.com', None, 'dyna_app'],
        'DynaPub': ['d-gp2-dynpub-1.dev.movenetworks.com', 5678, None],
        'Cliplist': ['d-gp2-dynclip-1.dev.movenetworks.com', None, 'cliplist'],
        'key-provider1': ['d-gp2-dynkp-1.dev.movenetworks.com', 8080, 'widevine'],
        'key-provider2': ['d-gp2-dynkp-2.dev.movenetworks.com', 8080, 'fairplay'],
        'PlayReady1': ['10.124.164.38', None, 'PlayReady'],
        'PlayReady2': ['10.124.164.39', None, 'PlayReady'],
    }
    return paths

def _create_uri(hostname, port, path, endpoint):
    uri = ''
    if not hostname.startswith('http'):
        uri = 'http://'
    uri += hostname.rstrip('/')
    if port:
        uri += ':%s' % str(port)
    if path:
        uri += '/%s' % path
    uri += '/%s' % endpoint
    return uri

def _test_endpoint(uri):
    try:
        with contextlib.closing(urllib2.urlopen(uri)) as request:
            return True, request.read()
    except urllib2.HTTPError as http_err:
        err = { http_err.code : http_err.reason }
        return False, json.dumps(err, sort_keys=True, indent=4, separators=(',', ': '))

def _test_dynamux_paths(output_valid):
    #endpoints = ['version', '_version', 'status', 'status.json', '_status', '_status.json'
    for name, parts in _get_dynamux_raw_paths().items():
        assert len(parts) == 3, 'dynamux raw path is malformed (%s)' % parts
        for raw_endpoint in ['version', 'status']:
            for variations in ['%s', '_%s', '%s.json', '_%s.json']:
                endpoint = variations % raw_endpoint
                uri = _create_uri(parts[0], parts[1], parts[2], endpoint)
                retval, details = _test_endpoint(uri)
                if retval:
                    print('SUCCESS: %s: %s' % (name, uri))
                elif not output_valid:
                    print('FAILURE: %s: %s' % (name, uri))

def main():
    output_valid = _parse_args()

    try:
        _test_dynamux_paths(output_valid)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import contextlib
import os
import sys
import traceback
import urllib.request, urllib.error, urllib.parse
import uuid

def enum(**enums):
    return type('Enum', (), enums)

Verbosity = enum(ERROR=0, INFO=1, DEBUG=2, TRACE=3)

_VERBOSE_LEVEL = 0

def get_verbosity(verbosity):
    if verbosity == Verbosity.ERROR:
        return 'ERROR'
    if verbosity == Verbosity.INFO:
        return 'INFO'
    if verbosity == Verbosity.DEBUG:
        return 'DEBUG'
    if verbosity == Verbosity.TRACE:
        return 'TRACE'
    return None

def verbose_print(verbosity, msg):
    if verbosity > _VERBOSE_LEVEL:
        return
    print('{0}: {1}'.format(get_verbosity(verbosity), msg))

def _parse_args():
    description = 'Create a list of arguments for the compiler'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('url', type=str, nargs='+', help='url to the file which contains the compiler switches')
    args = parser.parse_args()
    global _VERBOSE_LEVEL
    _VERBOSE_LEVEL = args.verbose
    verbose_print(Verbosity.INFO, 'verbose: {}, url: {}'.format(args.verbose, args.url))
    return args.url

def _retreive_data(url):
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as request:
            return request.read()
    except urllib.error.HTTPError:
        verbose_print(Verbosity.ERROR, 'reading data from {}'.format(url))

def _parse_compiler_data(data):
    args = {}
    #args = [] 
    for line in data.split('\n'):
        line_data = line.strip()
        if line_data.startswith('#'):
            continue
        index = line_data.find('#')
        if index != -1:
            line_data = line_data[:index]
            line_data = line_data.strip()
        if ' = ' in line_data:
            verbose_print(Verbosity.INFO, 'skipping {}'.format(line_data))
            continue
        args[line_data] = 0 
        #args.append(line_data)
    verbose_print(Verbosity.INFO, 'Args: {}'.format('\', \''.join(list(args.keys()))))
    #verbose_print(Verbosity.INFO, 'Args: {}'.format(' '.join(args)))
    return list(args.keys())
    #return args

def main():
    urls = _parse_args()
    try:
        for url in urls:
            data = _retreive_data(url)
            _parse_compiler_data(data)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

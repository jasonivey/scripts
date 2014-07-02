#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import pep8
import re
import sys
import traceback

class Foo(object):
    def __init__(self, number):
        self._number = number
    
    @property
    def number(self):
        return self._number
    
    def __hash__(self):
        return hash(self._number)
    
    def __str__(self):
        return str(self._number)

def _parse_args():
    parser = argparse.ArgumentParser(description='The script description is here...')

    # One of these two switches must be set
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-c', '--create', default=False, action='store_true', help='a default false flag')
    action_group.add_argument('-r', '--restore', default=False, action='store_true', help='a default false flag')

    # The are all optional parameters or flags
    parser.add_argument('-s', '--source', metavar='DIRECTORY', dest='source', required=True, help='source directory')
    parser.add_argument('-d', '--destination', metavar='DIRECTORY', dest='destination', required=False, help='destination directory')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show extra output')
    parser.add_argument('-vv', '--extra-verbose', default=False, action='store_true', help='show extra extra output')
    parser.add_argument('--simulated', default=False, action='store_true', help='do not actually execute the actions')

    args = parser.parse_args()

def process():
    print('hello world')

def main():
    _parse_args()
    try:
        process()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    metadata = '''# ss component

[component dependencies]
nlplib : code, 
PsFederator : code,

[misc]
targeted platforms: windows, linux, osx
terminal dependency:

[build tools]
rpmbuild: any, linux, rpmbuild --version, Run 'yum install rpm-build' on yum-based distros

[test tools]
valgrind: any, linux|osx, valgrind --version, Run 'yum install valgrind' on yum-based distros

[run tools]
''' 
    import ConfigParser
    config = ConfigParser.SafeConfigParser()
    config.optionxform = str
    filehandle = open(filename)
    #config.readfp(filehandle)
    config.readfp(io.BytesIO(metadata))
    for section in ['build tools', 'test tools', 'run tools']:
        for name, value in config.items(section):
            print(name, value)

	sys.exit(main())

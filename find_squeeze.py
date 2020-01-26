#!/usr/bin/env python

import os
import re
import sys
import traceback

def _does_cmake_file_have_squeeze_source(filename):
    filenames = []
    with open(filename, 'r') as handle:
        for data, i in enumerate(handle.readlines()):
            match = regex.match('Squeeze.*\.cpp', handle.read())
            filenames.append(data.strip())
    return filenames

def _does_cmake_file_have_squeeze_header(filename):
    filenames = []
    with open(filename, 'r') as handle:
        for data, i in enumerate(handle.readlines()):
            match = regex.match('Squeeze.*^(\.cpp)', handle.read())
            filenames.append(data.strip())
    return filenames

def _get_cmake_files():
    for root, dirs, files in os.walk(os.getcwd()):
        for file_name in files:
            filename = os.path.join(root, file_name)
            sources = _does_cmake_file_have_squeeze_source(filename)
            headers = _does_cmake_file_have_squeeze_header(filename)
            if len(sources) > 0 and len(headers) > 0:
                if len(sources) > 0:
                    print('  Sources:')
                print('%s:' % filename)
                for source in sources:
                    print('    %s' % source)
                if len(headers) > 0:
                    print('  Headers:')
                for header in headers:
                    print('    %s' % header)

def main():
    try:
        _get_cmake_files()
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
from __future__ import print_function
import os
import sys

if __name__ == '__main__':
    if len( sys.argv ) == 1:
        print('Usage: find_path.py filename1 [filename2] ...')

    paths = []
    for path in os.environ['PATH'].split(os.pathsep):
        if os.path.isdir(path):
            paths.append(os.path.abspath(path))

    for name in sys.argv[1:]:
        for path in [os.getcwd()] + paths:
            filename = os.path.abspath(os.path.join(path, name))
            #print(filename)
            if os.path.isfile(filename):
                print('  {0}'.format(filename))
            if 'PATHEXT' not in os.environ:
                continue
            for extension in os.environ['PATHEXT'].split(os.pathsep):
                #print(filename + extension)
                if os.path.isfile(filename + extension):
                    print('  {0}'.format(filename + extension))

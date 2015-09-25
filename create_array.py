from __future__ import print_function
import os
import sys
import traceback

def main():
    try:
        for filename in sys.argv[1:]:
            print('parsing {0}'.format(filename))
            with open(filename, 'r') as file:
                data = file.readlines()
            print('arry = [')
            for line in data:
                print('     \'{0}\', \\'.format(line.strip()))
            print('    ]')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

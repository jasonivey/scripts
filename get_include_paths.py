from __future__ import print_function
import argparse
import os
import sys
import traceback

_VERBOSE_OUTPUT = False

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _parse_args():
    description = 'Find the system include paths associated with a given compiler'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--compiler', metavar='<compiler>', required=True, help='name of compiler')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='output verbose debugging information')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = args.verbose
    return args.compiler

def _find_system_include_paths(compiler):
    command = '{0} -E -x c++ - -v < /dev/null'.format(compiler)
    paths = []
    found = False
    for line in os.popen4(command, 't')[1].readlines():
        if line.strip() == '#include <...> search starts here:':
            found = True
        elif found:
            if line.strip() == 'End of search list.':
                found = False
            else:
                include = line.strip()
                if include.endswith(' (framework directory)'):
                    include = include[:-len(' (framework directory)')]
                paths.append(include)
    return paths

def main():
    compiler = _parse_args()
    print('compiler: {0}, verbose: {1}'.format(compiler, _is_verbose_output_enabled()))

    try:
        for path in _find_system_include_paths(compiler):
            print(path)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

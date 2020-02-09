#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import sys
import traceback

_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

def _parse_args():
    parser = argparse.ArgumentParser(description='Pretty print environment variables')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-o', '--one-line', action="store_true", help='print variables with multiple values on one line')
    parser.add_argument('-l', '--list-env', action="store_true", help='list environment variables currently defined')
    parser.add_argument('variable', nargs='*', help='specify which variables to print, if none are specified PATH will be printed')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    environment_variables = args.variable
    if not args.list_env and (not environment_variables or len(environment_variables) == 0):
        environment_variables.append('PATH')

    if environment_variables and len(environment_variables) > 0 and args.list_env:
        print('ERROR: specified environment variables to print  and to list all environment variables, will only list variables', file=sys.stderr)
        environment_variables = [] 

    _verbose_print('INFO: args:\n  verbose: {}\n  one line: {}\n  list env: {}\n  variables: {}' \
                   .format(args.verbose, args.one_line, args.list_env, ', '.join(environment_variables)))
    return environment_variables, args.one_line, args.list_env

def main():
    environment_variables, print_one_line, list_env = _parse_args()
    retval = 0
    try:
        if list_env:
            print('Environment Variables:')
            print(''.join(['  {}\n'.format(key) for key in os.environ.keys()]))
        for environment_variable in environment_variables:
            if environment_variable in os.environ:
                value = os.environ[environment_variable]
                if value.find(':') != -1 and not print_one_line:
                    print('{}:'.format(environment_variable))
                    print(''.join(['  {}\n'.format(i) for i in value.split(':')]))
                else:
                    print('{}: {}\n'.format(environment_variable, value))
            else:
                print('ERROR: {} is not defined within the current environment'.format(environment_variable), file=sys.stderr)
                retval = 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        retval = 1
    return retval

if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import sys
import traceback

from verbose import Verbose

# TODO change this into a singleton class within _parse_args and return it to the ccaller
# I define a global variable which the _parse_args sets to true if the -v or the --verbose is set
# Afterwards, clients should use '_verbose_print` unless its an error or expected user output.

def _verbose_print(s):
    verbose = Verbose()
    if verbose.value: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    verbose = Verbose()
    return verbose.value

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

def _output_all_system_environment_variables():
    print('Environment Variables:')
    print(''.join(['  {}\n'.format(key) for key in os.environ.keys()]))

def _output_environment_variable_values(environment_variables, output_one_line, seperators):
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

def _output_values(values, seperators):
    pass

def main():
    values, environment_variables, list_system_environment_variables = _parse_args()
    try:
        if list_system_environment_variables:
            _output_all_system_environment_variables()
        if environment_variables:
            _output_environment_variable_values(environment_variables, output_one_line, seperators)
        if values:
            _output_values(values, seperators)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


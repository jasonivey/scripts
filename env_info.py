#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
import os
import sys
import traceback

from app_settings import app_settings

def _parse_args():
    parser = argparse.ArgumentParser(description='Pretty print environment variables')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-o', '--one-line', action="store_true", help='print variables with multiple values on one line')
    parser.add_argument('-l', '--list-env', action="store_true", help='list environment variables names currently defined')
    parser.add_argument('-s', '--seperator', default=':', metavar='<CHAR>', help='set which character to split multi-value environment variables')
    parser.add_argument('-i', '--identifier', metavar='<VALUE1:VALUE2:VALUE3>', help='out a specified list of identifiers by splitting them to using the <seperator>')
    parser.add_argument('variable', nargs='*', metavar='<ENV-VAR>', help='specify which environment variables should be printed')
    args = parser.parse_args()
    app_settings.verbose = args.verbose

    environment_variables = args.variable
    if not args.list_env and (not environment_variables or len(environment_variables) == 0):
        environment_variables.append('PATH')

    if environment_variables and len(environment_variables) > 0 and args.list_env:
        print('ERROR: specified environment variables to print and to list all environment variables, will only list variables', file=sys.stderr)
        environment_variables = []

    app_settings.print('INFO: args:\n  verbose: {}\n  variables: {}\n  list env: {}\n  ' \
                       'list identifiers: {}\n  one line: {}\n  seperator: {}' \
                       .format(args.verbose, ', '.join(environment_variables), args.list_env,
                               args.identifier, args.one_line, args.seperator))
    return environment_variables, args.list_env, args.identifier, args.one_line, args.seperator

def _output_environment_variables_names():
    print('Environment Variables:')
    print(''.join(['  {}\n'.format(key) for key in os.environ.keys()]))

def _output_environment_variable_values(environment_variables, print_one_line, seperator):
    for environment_variable in environment_variables:
        if environment_variable in os.environ:
            value = os.environ[environment_variable]
            if value.find(seperator) != -1 and not print_one_line:
                print('{}:'.format(environment_variable))
                print(''.join(['  {}\n'.format(i) for i in value.split(seperator)]))
            else:
                print('{}: {}\n'.format(environment_variable, value))
        else:
            print('ERROR: {} is not defined within the current environment'.format(environment_variable), file=sys.stderr)
            retval = 1

def _output_identifiers(values, seperator):
    if seperator in values:
        print(''.join(['{}\n'.format(value) for value in values.split(seperator)]))
    else:
        print(values)

def main():
    environment_variables, list_environment_variables_names, list_identifiers, output_one_line, seperator = _parse_args()
    try:
        if list_environment_variables_names:
            _output_environment_variables_names()
        if environment_variables:
            _output_environment_variable_values(environment_variables, output_one_line, seperator)
        if list_identifiers:
            _output_identifiers(list_identifiers, seperator)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


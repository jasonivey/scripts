#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
import os
from pathlib import Path
import sys
import traceback

from app_settings import app_settings

def _parse_args():
    parser = argparse.ArgumentParser(description='Pretty print environment variables')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-o', '--one-line', action="store_true", help='print variables with multiple values on one line')
    parser.add_argument('-l', '--list-env', action="store_true", help='list environment variables names currently defined')
    parser.add_argument('-s', '--seperator', default=':', metavar='<CHAR>', help='set which character to split multi-value environment variables')
    parser.add_argument('-i', '--identifier', metavar='<VALUE1:VALUE2:VALUE3>', help='out a specified list of identifiers by splitting them to using the <seperator>')
    parser.add_argument('variables', nargs='*', metavar='<ENV-VAR>', help='specify which environment variables should be printed')
    args = parser.parse_args()
    app_settings.set(vars(args))

    environment_variables = app_settings.variables
    if not app_settings.list_env and not app_settings.identifier and (not environment_variables or len(environment_variables) == 0):
        environment_variables.append('PATH')

    if environment_variables and len(environment_variables) > 0 and app_settings.list_env:
        parser.error('attempting to print environment variables and to list all defined environment variables -- choose one!')

    app_settings.variables = environment_variables
    app_settings.print_settings(print_always=False)

def _output_environment_variables_names():
    print('Environment Variables:')
    print(''.join([f'  {key}\n' for key in os.environ.keys()]))

def _get_information_on_value(orig_value):
    value = orig_value
    if value.startswith('-isystem'):
        value = value[len('-isystem'):]
    if value.startswith('-I'):
        value = value[len('-I'):]
    if value.startswith('-L'):
        value = value[len('-L'):]
    path = Path(value)
    if path.is_char_device():
        return f'(char device) {value}'
    elif path.is_block_device():
        return f'(block device) {value}'
    elif path.is_fifo():
        return f'(fifo) {value}'
    elif path.is_socket():
        return f'(socket) {value}'
    elif path.is_mount():
        return f'(mount point) {value}'
    elif path.is_symlink():
        return f'(symbolic link) {value}'
    elif path.is_file():
        return f'(file) {value}'
    elif path.is_dir():
        return f'(directory) {value}'
    elif path.exists():
        return f'(exists) {value}'
    else:
        return orig_value

def _get_information_on_values(values, seperator):
    for value in values.split(seperator):
        yield _get_information_on_value(value)

def _output_environment_variable_values(environment_variables, print_one_line, seperator):
    for environment_variable in environment_variables:
        if environment_variable in os.environ:
            value = os.environ[environment_variable]
            if value.find(seperator) != -1 and not print_one_line:
                count = len(value.split(seperator))
                print(f'{environment_variable} ({count}):')
                output = ''
                for single_value in _get_information_on_values(value, seperator):
                    output += f'  {single_value}\n'
                print(output, end='')
            else:
                print(f'{environment_variable}: {_get_information_on_value(value)}')
        else:
            print(f'ERROR: {environment_variable} is not defined within the current environment', file=sys.stderr)
            retval = 1

def _output_identifiers(values, seperator):
    if seperator in values:
        output = ''
        for single_value in _get_information_on_values(values, seperator):
            output += f'{single_value}\n'
        print(output, end='')
    else:
        print(values)

def main():
    _parse_args()
    try:
        if app_settings.list_env:
            _output_environment_variables_names()
        if app_settings.variables:
            _output_environment_variable_values(app_settings.variables, app_settings.one_line, app_settings.seperator)
        if app_settings.identifier:
            _output_identifiers(app_settings.identifier, app_settings.seperator)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


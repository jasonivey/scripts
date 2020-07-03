#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
import os
from pathlib import Path
import sys
import traceback

from app_settings import app_settings

user_tags = {
    'title'     : parse('<bold><green>'),    # bold green
    'text'      : parse('<bold><white>'),    # bold white
    'alttext'   : parse('<white>'),          # white
    'name'      : parse('<bold><cyan>'),     # bold cyan
    'altname'   : parse('<cyan>'),           # cyan
    'error'     : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

def _error_print(msg):
    am.ansiprint(f'<error>ERROR: {msg}</error>', file=sys.stderr)

def _title_print(title):
    am.ansiprint(f'<title>{title}</title>')

def _is_only_defaults_set():
    return not app_settings.list_env and \
           not app_settings.list_env_values and \
           not app_settings.identifier and \
           (not app_settings.variables or len(app_settings.variables) == 0)

def _parse_args():
    parser = argparse.ArgumentParser(description='Pretty print environment variables')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-r', '--raw', action='store_true', help='print variables how they are found in the environment')
    parser.add_argument('-o', '--one-line', action="store_true", help='print variables with multiple values on one line')
    parser.add_argument('-l', '--list-env', action="store_true", help='list environment variables names currently defined')
    parser.add_argument('-L', '--list-env-values', action="store_true", help='list environment variables names currently defined and values')
    parser.add_argument('-s', '--seperator', default=':', metavar='<CHAR>', help='set which character to split multi-value environment variables')
    parser.add_argument('-i', '--identifier', metavar='<VALUE1:VALUE2:VALUE3>', help='out a specified list of identifiers by splitting them to using the <seperator>')
    parser.add_argument('variables', nargs='*', metavar='<ENV-VAR>', help='specify which environment variables should be printed')
    args = parser.parse_args()
    app_settings.set(vars(args))

    if _is_only_defaults_set():
        app_settings.variables.append('PATH')

    # these should be fixed with a mutually exclusive group
    if app_settings.variables and len(app_settings.variables) > 0 and (app_settings.list_env or app_settings.list_env_values):
        parser.error('attempting to print environment variables and to list all defined environment variables -- choose one!')

    app_settings.print_settings(print_always=False)

def _environment_variable_key(name):
    if name.startswith('__'):
        return name[2:] if name[2:] else ''
    elif name.startswith('_'):
        return name[1:] if name[1:] else ''
    else:
        return name

def _output_environment_variables_names(raw):
    _title_print('Environment Variables')
    names = os.environ.keys() if raw else sorted(os.environ, key=_environment_variable_key)
    for index, name in enumerate(names):
        if index % 2 == 0:
            am.ansiprint(f'  <name>{name}</name>')
        else:
            am.ansiprint(f'  <altname>{name}</altname>')
    return True

def _get_max_name_width():
    return max([len(f'{name}:') for name in sorted(os.environ)])

def _output_environment_variables_names_values(raw):
    MAX_LINE_LEN = 100
    MAX_NAME_WIDTH = _get_max_name_width()
    _title_print('Environment Variables & Values')
    name_values = []
    for index, name in enumerate(sorted(os.environ, key=_environment_variable_key)):
        label_size = len(f'  {name:{MAX_NAME_WIDTH}}:')
        value = os.environ[name]
        updated_value = ''
        if raw:
            updated_value = value
        elif len(value) + label_size > MAX_LINE_LEN and (value.find(':') != -1 or value.find(' ') != -1):
            current_line_len = label_size
            value_parts = value.replace(':', ' ').split()
            value_parts_dups = []
            for value_part in value_parts:
                if value_part not in value_parts_dups and value_parts.count(value_part) > 1:
                    value_parts_dups.append(value_part)
                    #return _error_print(f'environment variable {name} has multiple values of {value_part}')
                if not updated_value:
                    current_line_len += len(value_part)
                    updated_value = value_part
                elif current_line_len + len(value_part) > MAX_LINE_LEN:
                    current_line_len = label_size + len(value_part)
                    updated_value += '\n' + label_size * ' ' + value_part
                else:
                    current_line_len += len(value_part)
                    updated_value += f', {value_part}' if updated_value else value_part
        else:
            value_parts = value.replace(':', ' ').split()
            value_parts_dups = []
            for value_part in value_parts:
                if value_part not in value_parts_dups and value_parts.count(value_part) > 1:
                    value_parts_dups.append(value_part)
                    #return _error_print(f'environment variable {name} has multiple values of {value_part}')
                updated_value += f', {value_part}' if updated_value else value_part
        if index % 2 == 0:
            name_values.append((am.ansistring(f'<name>{name}:</name>'), am.ansistring(f'<text>{updated_value}</text>')))
        else:
            name_values.append((am.ansistring(f'<altname>{name}:</altname>'), am.ansistring(f'<alttext>{updated_value}</alttext>')))
    for (name, value) in name_values:
        print(f'  {name:{MAX_NAME_WIDTH + name.delta}} {value}')
    return True

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

def _output_environment_variable_values(environment_variables, raw, print_one_line, seperator):
    for environment_variable in environment_variables:
        if environment_variable in os.environ:
            value = os.environ[environment_variable]
            if raw:
                am.ansiprint(f'<name>{environment_variable}:</name> <text>{value}</text>')
            elif value.find(seperator) != -1 and not print_one_line:
                count = len(value.split(seperator))
                am.ansiprint(f'<name>{environment_variable} ({count}):<name>')
                output = ''
                for single_value in _get_information_on_values(value, seperator):
                    output += f'  <text>{single_value}</text>\n'
                am.ansiprint(output, end='')
            else:
                am.ansiprint(f'<name>{environment_variable}:</name> <text>{_get_information_on_value(value)}</text>')
        else:
            return _error_print(f'{environment_variable} is not defined within the current environment')
    return True

def _output_identifiers(values, seperator):
    if seperator in values:
        output = ''
        for single_value in _get_information_on_values(values, seperator):
            output += f'<text>{single_value}</text>\n'
        am.ansiprint(output, end='')
    else:
        am.ansiprint(f'<text>{values}</text>')
    return True

def env_info():
    if app_settings.list_env:
        return _output_environment_variables_names(app_settings.raw)
    elif app_settings.list_env_values:
        return _output_environment_variables_names_values(app_settings.raw)
    elif app_settings.variables:
        return _output_environment_variable_values(app_settings.variables, app_settings.raw, app_settings.one_line, app_settings.seperator)
    elif app_settings.identifier:
        return _output_identifiers(app_settings.identifier, app_settings.seperator)
    return True

def main():
    _parse_args()
    try:
        return 0 if env_info() else 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())


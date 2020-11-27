
import argparse
import os
import subprocess
import sys
import traceback

def enum(**enums):
    return type('Enum', (), enums)

Verbosity = enum(ERROR=0, INFO=1, DEBUG=2, TRACE=3)

_VERBOSE_LEVEL = 0

def get_verbosity(verbosity):
    if verbosity == Verbosity.ERROR:
        return 'ERROR'
    if verbosity == Verbosity.INFO:
        return 'INFO'
    if verbosity == Verbosity.DEBUG:
        return 'DEBUG'
    if verbosity == Verbosity.TRACE:
        return 'TRACE'
    return None

def verbose_print(verbosity, msg):
    if verbosity > _VERBOSE_LEVEL:
        return
    print('{0}: {1}'.format(get_verbosity(verbosity), msg))

def _parse_args():
    description = 'Find the system include paths associated with a given compiler'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--compiler', metavar='<compiler>', required=True, help='name of compiler (gcc/g++/clang++)')
    parser.add_argument('-l', '--stdlib', metavar='<stdlib>', help='the standard library to use (libstdc++ or libc++)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('-s', '--single-line', default=False, action='store_true', help='output include paths as a single line')
    args = parser.parse_args()
    global _VERBOSE_LEVEL
    _VERBOSE_LEVEL = args.verbose
    verbose_print(Verbosity.INFO, 'compiler: {0}, standard library: {1} single line: {2}, verbose: {3}'.format(args.compiler, args.stdlib, args.single_line, args.verbose))
    return args.compiler, args.stdlib, args.single_line

def _parse_system_include_path(input_str):
    input_str = input_str.strip()
    verbose_print(Verbosity.INFO, 'parsing: {}'.format(input_str))
    if input_str.startswith('"'):
        index = input_str.find('"', 1)
        path_str = '' if index == -1 else input_str[1:index]
    elif input_str.startswith("'"):
        index = input_str.find("'", 1)
        path_str = '' if index == -1 else input_str[1:index]
    else:
        path_str = ''
        index = 0
        while index != -1:
            index = input_str.find(os.sep)
            if index != -1:
                path_str += input_str[:index + 1]
                verbose_print(Verbosity.DEBUG, 'path_str: {}'.format(path_str))
                input_str = input_str[index + 1:]
                verbose_print(Verbosity.DEBUG, 'input_str: {}'.format(input_str))
                if not os.path.isdir(path_str):
                    verbose_print(Verbosity.DEBUG, 'the path contains an invalid directory {}'.format(path_str))
                    return None
            else:
                space_index = input_str.find(' ')
                if space_index == -1:
                    path_str += input_str
                    verbose_print(Verbosity.DEBUG, 'path_str: {}'.format(path_str))
                else:
                    path_str += input_str[:space_index]
                    verbose_print(Verbosity.DEBUG, 'path_str: {}'.format(path_str))
    if os.path.isdir(path_str):
        verbose_print(Verbosity.INFO, 'returning the path {}'.format(os.path.normpath(path_str)))
        return os.path.normpath(path_str)
    verbose_print(Verbosity.DEBUG, 'the input str {} did not contain a valid path'.format(input_str))
    return None

def _run_external_shell_command(cmd):
    try:
        completed_process = subprocess.run(cmd, shell=True, check=True, encoding='utf-8', capture_output=True)
        return completed_process.stdout
    except subprocess.SubprocessError as err:
        print(f'ERROR: "{cmd}" returned: {err}', file=sys.stderr)
        return None
    except Exception as err:
        print(f'EROR: "{cmd}" returned: {err}', file=sys.stderr)
        return None

def find_system_include_paths(compiler, stdlib=None):
    if stdlib:
        command = '{0} -stdlib={1} -E -x c++ - -v < /dev/null'.format(compiler, stdlib)
    else:
        command = '{0} -E -x c++ - -v < /dev/null'.format(compiler)
    paths = []
    verbose_print(Verbosity.INFO, 'system command: {}'.format(command))
    output = _run_external_shell_command(command)
    for line in output.splitlines():
        include = _parse_system_include_path(line)
        if include:
            paths.append(include)
    return paths

def main():
    compiler, stdlib, single_line = _parse_args()
    try:
        paths = find_system_include_paths(compiler, stdlib)
        if single_line:
            print(os.pathsep.join(paths))
        else:
            for index, path in enumerate(paths):
                print('{0:2}. {1}'.format(index + 1, path))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

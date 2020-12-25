#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

import argparse
import os
from pathlib import Path
import shlex
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
    parser.add_argument('-c', '--compiler', metavar='<compiler>', default='clang++',
                        help='name of compiler (gcc/g++/clang++)')
    parser.add_argument('-l', '--stdlib', metavar='<stdlib>', help='the standard library to use (libstdc++ or libc++)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('-s', '--single-line', default=False, action='store_true',
                        help='output include paths as a single line')
    parser.add_argument('-f', '--find-file', help='using the include paths find the file')
    parser.add_argument('-g', '--grep', help='using the include paths grep for string')
    args = parser.parse_args()
    global _VERBOSE_LEVEL
    _VERBOSE_LEVEL = args.verbose
    verbose_print(Verbosity.INFO, f'compiler: {args.compiler}, standard library: {args.stdlib}, '
                                  f'verbose: {args.verbose}, single line: {args.single_line}, '
                                  f'find file: {args.find_file}, grep: {args.grep}')
    return args.compiler, args.stdlib, args.single_line, args.find_file, args.grep


def _run_external_shell_command(cmd, ignore_error=False):
    process = subprocess.Popen(cmd, shell=True, encoding='utf-8', bufsize=1,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0 and not ignore_error:
        verbose_print(Verbosity.ERROR, f'"{cmd}" returned error code: {process.returncode}')
        return None
    verbose_print(Verbosity.INFO, f'INFO: "{cmd}" returned: {stdoutdata}')
    return stdoutdata


def find_system_include_paths(compiler, stdlib=None):
    if stdlib:
        command = f'{compiler} -stdlib={stdlib} -E -x c++ - -v  < /dev/null'
    else:
        command = f'{compiler} -E -x c++ - -v < /dev/null'
    verbose_print(Verbosity.INFO, f'system command: {command}')
    output = _run_external_shell_command(command)
    verbose_print(Verbosity.INFO, f'command returned:\n{output}')
    if not output:
        return
    started = False
    for line in output.splitlines():
        line = line.strip()
        if line == '#include <...> search starts here:':
            started = True
        elif line == 'End of search list.':
            break
        elif started:
            if line.endswith(' (framework directory)'):
                index = len(line) - len(' (framework directory)')
                line = line[0:index]
            path = Path(line)
            if not path.exists():
                verbose_print(Verbosity.INFO, f'non-existent directory found in system include path: {path}')
            else:
                yield path.resolve()


def find_file_in_path(include_path, file_to_find):
    for path in include_path.rglob(file_to_find):
        yield path.resolve()


def find_str_in_path(include_path, search_str):
    command = f'find -H {include_path} -type f -exec grep "{search_str}" {{}} \+'
    output = _run_external_shell_command(command, ignore_error=True)
    if not output:
        return
    for line in output.splitlines():
        yield line.strip()


def main():
    compiler, stdlib, single_line, file_to_find, grep_str = _parse_args()
    try:
        single_line_str = ''
        for path in find_system_include_paths(compiler, stdlib):
            if single_line:
                single_line_str += f'{path}' if len(single_line_str) == 0 else f'{os.path.pathsep}{path}'
            else:
                print(path)
                if file_to_find:
                    for found_path in find_file_in_path(path, file_to_find):
                        print(f'  [FILE FOUND]: {found_path}')
                if grep_str:
                    for found_path in find_str_in_path(path, grep_str):
                        print(f'  [{grep_str} FOUND]: {found_path}')
        if single_line:
            print(single_line_str)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

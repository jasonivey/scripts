#!/usr/bin/env python
# coding: utf-8
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
import argparse
import os
import subprocess
import sys
import traceback

_VERBOSE_LEVEL = 0
def enum(**enums):
    return type('Enum', (), enums)
Verbosity = enum(ERROR=0, INFO=1, DEBUG=2, TRACE=3)

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

def _verbose_print(verbosity, msg):
    if verbosity > _VERBOSE_LEVEL:
        return
    print('{0}: {1}'.format(get_verbosity(verbosity), msg))

def _is_source_type(path):
    return path.endswith('.cpp') or path.endswith('.h')

def _is_source(path):
    fullpath = os.path.abspath(path)
    if (os.path.isfile(fullpath) and _is_source_type(fullpath)) or os.path.isdir(fullpath):
        return fullpath
    msg = '%s is not a valid source file or directory' % src
    raise argparse.ArgumentTypeError(msg)

def _find_sources(paths, recursive):
    sources = []
    for path in paths:
        if os.path.isfile(path):
            sources.append(path)
        elif recursive:
            for root, dirs, files in os.walk(path):
                for filename in files:
                    fullpath = os.path.abspath(os.path.join(root, filename))
                    if _is_source_type(fullpath):
                        sources.append(fullpath)
        else:
            for filename in os.listdir(path):
                fullpath = os.path.abspath(os.path.join(os.path.dirname(path), filename))
                if _is_source_type(fullpath):
                    sources.append(fullpath)
    return list(set(sources))

def _parse_args():
    parser = argparse.ArgumentParser(description='Run clang format')
    parser.add_argument('source', metavar='N', type=_is_source, nargs='+', help='source file or directory')
    parser.add_argument('-r', '--disable-recursive', default=False, action='store_true', help='do NOT search for sources recursively')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    args = parser.parse_args()
    global _VERBOSE_LEVEL
    _VERBOSE_LEVEL = args.verbose
    sources = _find_sources(args.source, not args.disable_recursive)
    _verbose_print(Verbosity.DEBUG, 'sources: %s' % ', '.join(sources))
    return sources

def _execute_command(command):
    _verbose_print(Verbosity.DEBUG, 'executing command: %s' % command)
    process = subprocess.Popen(command, shell=True, bufsize=1, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        return False, stderrdata.decode('utf-8')
    else:
        return True, stdoutdata.decode('utf-8')

def _find_configuration(filename):
    cur_dir = os.getcwd()
    os.chdir(os.path.dirname(filename))
    retval, path = _execute_command('git rev-parse --show-toplevel')
    os.chdir(cur_dir)
    if retval and os.path.isfile(os.path.join(path.strip(), '.clang-format')):
        return os.path.abspath(os.path.join(path.strip(), '.clang-format'))
    else:
        return os.path.abspath(os.path.join(os.environ['HOME'], 'settings', '.clang-format'))

def run_clang_format(filename):
    config_file = _find_configuration(filename)
    command = 'cat {0} | clang-format-3.7 -assume-filename={1} | tee {0}'.format(filename, config_file)
    retval, output = _execute_command(command)
    if not retval:
        _verbose_print(Verbosity.ERROR, '%s: %s' % (filename, output.strip()))
    else:
        _verbose_print(Verbosity.DEBUG, '%s' % filename)

def main():
    sources = _parse_args()
    try:
        for source in sources:
            run_clang_format(source)
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())

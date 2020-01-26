#!/usr/bin/env python
# coding: utf-8
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
import argparse
import json
import os
import sys
import traceback

def _is_source_type(path):
    return path.endswith('.cpp')

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
    parser = argparse.ArgumentParser(description='Create compile_commands.json from compiler command')
    parser.add_argument('command', metavar='command', type=str, help='compiler command')
    parser.add_argument('-s', '--source', required=True, type=_is_source, action='append', help='source file or directory')
    parser.add_argument('-o', '--output', required=False, default='compile_commands.json', type=argparse.FileType('w'), help='destination for json data')
    parser.add_argument('-d', '--directory', required=False, default=os.getcwd(), type=str, help='destination directory')
    parser.add_argument('-r', '--disable-recursive', default=False, action='store_true', help='do NOT search for sources recursively')
    args = parser.parse_args()
    sources = _find_sources(args.source, not args.disable_recursive)
    return args.command, sources, args.directory, args.output

def _create_command_line(command_line, filename):
    cmds = command_line.split()
    prefix = ' '.join(cmds[:-4])
    middle = ' '.join(cmds[-3:-1])
    return '{} {} {} {}'.format(prefix, filename, middle, '/dev/null')

def create_compile_commands(command_line, directory, sources):
    commands = []
    for source in sources:
        command = {}
        command['directory'] = directory
        command['command'] = _create_command_line(command_line, source)
        command['file'] = source
        commands.append(command)
    return json.dumps(commands, indent=4, separators=(',', ': '), sort_keys=True)

def main():
    command, sources, directory, output = _parse_args()
    try:
        print(('command: %s' % command))
        print('sources:')
        for i in sources:
            print(i)
        print(('sources: %s' % type(sources)))
        output.write(create_compile_commands(command, directory, sources))
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    finally:
        if output:
            output.close()

if __name__ == '__main__':
    sys.exit(main())

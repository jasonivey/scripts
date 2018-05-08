#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import json
import os
import re
import sys
import traceback

def _is_valid_directory(dirname):
    dirname = os.path.expandvars(dirname)
    if not os.path.isdir(dirname):
        msg = '{0} is not a valid directory'.format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return os.path.abspath(dirname)

def _parse_args():
    description = 'Update the CMake generated compile_commands.json to work on the local machine instead of a docker container'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--compiler', type=str, required=False, default='/usr/local/opt/llvm/bin/clang++', help='name and path of compiler to use')
    parser.add_argument('-t', '--omniture', type=_is_valid_directory, required=False, default='$HOME/tools/omniture', help='local directory where omniture is located')
    parser.add_argument('-m', '--mysql', type=_is_valid_directory, required=False, default='$HOME/tools/mysql', help='local directory where mysql is located')
    parser.add_argument('-s', '--openssl', type=_is_valid_directory, required=False, default='/usr/local/opt/openssl/include', help='local directory where openssl is located')
    parser.add_argument('-b', '--boost', type=_is_valid_directory, required=False, default='$HOME/tools/boost_1_41_0', help='local directory where boost_1_41_0 is located')
    args = parser.parse_args()
    print('Compiler: %s' % args.compiler)
    print('Omniture: %s' % args.omniture)
    print('mysql   : %s' % args.mysql)
    print('OpenSSL : %s' % args.openssl)
    print('Boost   : %s' % args.boost)
    return args.compiler, args.omniture, args.mysql, args.openssl, args.boost

def _find_compile_commands_file(dirname):
    filename = os.path.abspath(os.path.join(dirname, 'compile_commands.json'))
    if os.path.isfile(filename):
        return filename
    else:
        new_dir = os.path.dirname(os.path.abspath(os.path.join(dirname, '..')))
        if new_dir == dirname:
            raise ValueError('Unable to find compile_commands.json')
        else:
            return _find_compile_commands_file(new_dir)

def _update_compile_command(command, dirname, compiler_path, omniture_dir, mysql_dir, openssl_dir, boost_dir):
    command = re.sub(r'/source/', dirname, command)

    if compiler_path:
        command = re.sub(r'(?P<compiler_path>.*/)(?P<compiler>clang\+\+|clang|g\+\+|gcc|icc) ', r'%s ' % compiler_path, command)
    else:
        # Default to using g++/clang++/gcc/clang/icc (i.e. strip the path) 
        command = re.sub(r'(?P<compiler_path>.*/)(?P<compiler>clang\+\+|clang|g\+\+|gcc|icc) ', r'\2 ', command)

    if omniture_dir:
        # This points to the container /home/omniture/ various directories
        command = re.sub(r'/home/omniture', omniture_dir.rstrip('/'), command)

    if mysql_dir:
        command = re.sub(r'/usr/include/mysql', mysql_dir.rstrip('/'), command)

    if openssl_dir:
        # OpenSSL has been pre-installed in the container to a standard include area
        command = re.sub(r'\s+-g\s+', r' -g -isystem %s ' % openssl_dir, command)

    if boost_dir:
        # Boost 1.41.0 has been pre-installed in the container to a standard include area
        command = re.sub(r'\s+-g\s+', r' -g -isystem %s ' % boost_dir, command)

    return command

def update_compile_commands(compiler_path, omniture_dir, mysql_dir, openssl_dir, boost_dir):
    compile_commands_filename = _find_compile_commands_file(os.getcwd())
    compile_commands_dirname = os.path.abspath(os.path.dirname(compile_commands_filename))
    if not compile_commands_dirname.endswith(os.path.sep):
        compile_commands_dirname += '/'

    # Read in the compile_commands.json
    with open(compile_commands_filename, 'r') as compile_commands_file:
        compile_commands = json.load(compile_commands_file)

    new_commands = []
    for compile_command in compile_commands:
        new_command = {}
        for key, value in compile_command.iteritems():
            new_value = _update_compile_command(value,
                                                compile_commands_dirname,
                                                compiler_path,
                                                omniture_dir,
                                                mysql_dir,
                                                openssl_dir,
                                                boost_dir)
            new_command[key] = new_value
        new_commands.append(new_command)
            
    # Write out the updated compile_commands.json
    with open(compile_commands_filename, 'w') as compile_commands_file:
        json.dump(new_commands, compile_commands_file, indent=2, separators=(',', ': '), sort_keys=True)
    print('Successfully updated %s' % compile_commands_filename)

def main():
    compiler_path, omniture_dir, mysql_dir, openssl_dir, boost_dir = _parse_args()
    try:
        update_compile_commands(compiler_path, omniture_dir, mysql_dir, openssl_dir, boost_dir)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


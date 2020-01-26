#!/usr/bin/env python

import argparse
import exceptions
import glob
import os
import subprocess
import sys
import shutil

def _find_sandbox_root(start_dir):
    dir = start_dir
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if os.path.isfile(os.path.join(dir, 'sandbox.conf')):
            return dir
        else:
            dir = parent
        parent = os.path.abspath(os.path.join(dir, '..'))
    raise exceptions.RuntimeError('Unable to find the sandbox.conf file within {0}'.format(start_dir))

def _read_suo_files(dir_name):
    suo_files = []
    for suo_file_name in glob.iglob('{0}{1}*.suo'.format(dir_name, os.sep)):
        with file(suo_file_name, 'rb') as suo:
            data = suo.read()
            suo_file = [suo_file_name, data]
            suo_files.append(suo_file)
    return suo_files

def _write_suo_files(suo_files):
    for suo_file in suo_files:
        with file(suo_file[0], 'wb') as suo:
            suo.write(suo_file[1])
    
def parse_command_line():
    return
    
def main():
    sandbox_dir = _find_sandbox_root(os.getcwd())
    sandbox_suo_files = []

    for dir_name in os.listdir(sandbox_dir):
        if not dir_name.startswith('built.'):
            continue
        built_dir = os.path.join(sandbox_dir, dir_name)
        suo_files = _read_suo_files(built_dir)
        if len(suo_files) > 0:
            sandbox_suo_files.append(suo_files)
        shutil.rmtree(built_dir, True)

    process = subprocess.Popen('sb build config', shell=True, bufsize=1, cwd=sandbox_dir)
    retval = process.wait()

    for suo_files in sandbox_suo_files:
        _write_suo_files(suo_files)

    return 0

if __name__ == '__main__':
    sys.exit(main())

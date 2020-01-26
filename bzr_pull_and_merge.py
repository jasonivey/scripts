#!/usr/bin/env python

import argparse
import os
import subprocess
import sys


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

def _contains_sandbox(dir):
    sandbox_root = None
    try:
        sandbox_root = _find_sandbox_root(dir)
    except:
        sandbox_root = None
    return sandbox_root != None

def _valid_sandbox(dir):
    if not os.path.isdir(dir):
        raise argparse.ArgumentTypeError("{0} is not a directory".format(dir))
    if not _contains_sandbox(dir):
        raise argparse.ArgumentTypeError("{0} does not contain a sandbox".format(dir))
    return _find_sandbox_root(dir)

def _parse_command_line():
    parser = argparse.ArgumentParser(description='Perform a bazaar pull and merge')
    parser.add_argument('-s', '--sandbox', dest='sandbox', default=os.getcwd(), required=False, type=_valid_sandbox, help='sandbox directory')
    parser.add_argument('-b', '--branch', dest='branch', default=None, required=False, type=type(''), help='branch to pull and merge from')
    args = parser.parse_args()
    branch = args.branch
    if not branch:
        branch = os.path.basename(args.sandbox)
    return args.sandbox, branch

class SandboxPath(object):
    def __init__(self, dir_path):
        self.dir_path = dir_path
        parts = self.dir_path.rstrip(os.path.sep).split(os.path.sep)
        self.component = parts[-1]
        self.aspect = parts[-2]
        self.branch = parts[-3]
    def __str__(self):
        return 'Path: {0}\n\tComponent: {1}\n\tAspect:    {2}\n\tBranch:    {3}'.format(self.dir_path, self.component, self.aspect, self.branch)

def _execute_bazaar_command(cmd, location, cwd):
    command = 'bzr {0} {1}'.format(cmd, location)
    print(command, end='\n\n')
    process = subprocess.Popen(command, \
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, \
                               shell=True, bufsize=1, cwd=cwd)
    process.wait()
    exitcode = process.returncode
    print('{0}\nExit Code: {1}'.format(process.stdout.read().strip(), exitcode), end='\n\n')
    return exitcode == 0
    
def _pull(sandbox_path, branch):
    location = 'bzr+ssh://bazaar.perfectsearchcorp.com/reporoot/{0}/{1}/{2}'.format(branch, sandbox_path.component, sandbox_path.aspect)
    return _execute_bazaar_command('pull', location, sandbox_path.dir_path)

def _merge(sandbox_path, branch):
    location = 'bzr+ssh://bazaar.perfectsearchcorp.com/reporoot/{0}/{1}/{2}'.format(branch, sandbox_path.component, sandbox_path.aspect)
    return _execute_bazaar_command('merge', location, sandbox_path.dir_path)
    
def _pull_and_merge(dirs, branch):
    for dir_name in dirs:
        sandbox_path = SandboxPath(dir_name)
        if not _pull(sandbox_path, branch):
            _merge(sandbox_path, branch)
            #if not _merge(sandbox_path, branch):
            #    raise RuntimeError('Both pull and merge failed in {0}'.format(dir_name))
    
def _lookup_components(sandbox_dir):
    code_dir = os.path.join(sandbox_dir, 'code')
    code_components = [os.path.join(code_dir, fs_entry) for fs_entry in os.listdir(code_dir) if os.path.isdir(os.path.join(code_dir, fs_entry))]
    test_dir = os.path.join(sandbox_dir, 'test')
    test_components = [os.path.join(test_dir, fs_entry) for fs_entry in os.listdir(test_dir) if os.path.isdir(os.path.join(test_dir, fs_entry))]
    return code_components + test_components

def main():
    sandbox, branch = _parse_command_line()
    print('Sandbox Directory: {0}'.format(sandbox), end='\n\n')
    _pull_and_merge(_lookup_components(sandbox), branch)
    return 0

if __name__ == '__main__':
    sys.exit(main())


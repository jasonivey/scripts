#!/usr/bin/env python

import argparse
import collections
import exceptions
import os
import re
import socket
import subprocess
import sys
import traceback

from custom_utils import find_path_in_directory

_REPOROOT = 'bzr+ssh://bazaar.perfectsearchcorp.com/reporoot'
_SANDBOX_CONF = 'sandbox.conf'
_BAZAAR_ROOT = '.bzr'

def _get_newline():
    return '\r\n' if os.name == 'nt' else '\n'

def find_sandbox_root(start_dir):
    return find_path_in_directory(start_dir, filename=_SANDBOX_CONF)
    
def find_bzr_root(start_dir):
    return find_path_in_directory(start_dir, dirname=_BAZAAR_ROOT)

def _parse_repo_path(path):
    if path.startswith('bzr+ssh://'):
        return path
    elif path.startswith('ssh://'):
        return 'bzr+' + path
    else:
        domain = path.split('/')[0]
        if domain == 'bazaar.perfectsearchcorp.com' or domain == 'bazaar.psearch.local':
            return 'bzr+ssh://' + path.lstrip()
        else:
            return '{0}/{1}'.format(_REPOROOT, path.lstrip('/'))

_BZR_FILE_ADDED = 'added:'
_BZR_FILE_MODIFIED = 'modified:'
_BZR_FILE_REMOVED = 'removed:'
_BZR_FILE_PENDING_MERGE = 'pending merge tips:'
_BZR_FILE_UNKNOWN = 'unknown:'
_BZR_FILE_STATES = [_BZR_FILE_ADDED,
                    _BZR_FILE_MODIFIED,
                    _BZR_FILE_REMOVED,
                    _BZR_FILE_PENDING_MERGE,
                    _BZR_FILE_UNKNOWN]

class _StatState(object):
    def __init__(self):
        self._state = {}
        self.reset_state()

    def reset_state(self):
        self._state = {}
        for state in _BZR_FILE_STATES:
            self._state[state] = False

    def change_state(self, state):
        self.reset_state()
        assert state in _BZR_FILE_STATES, 'Unknown state {0} being set'.format(state)
        self._state[state] = True

    @property
    def state(self):
        for state in _BZR_FILE_STATES:
            if self._state[state]:
                return state
        assert False, 'State has not been set!'
        return _BZR_FILE_UNKNOWN[:-1]

class _BzrStatParser(object):
    def __init__(self, text, path):
        self._text = text
        self._path = path
        self._files = collections.defaultdict(list)

    @property
    def files(self):
        return self._files
    
    def add_file(self, state, filename):
        self._files[state].append(filename)

    def __call__(self):
        stat_state = _StatState()
        for line in self._text.split(_get_newline()):
            line = line.strip()
            if len(line) == 0:
                continue
            if line in _BZR_FILE_STATES:
                stat_state.change_state(line)
            else:
                self.add_file(stat_state.state, os.path.abspath(os.path.join(self._path, line)))

class _SandboxStatParser(object):
    def __init__(self, text, sandbox_root):
        self._text = text
        self._sandbox_root = sandbox_root
        self._files = collections.defaultdict(list)

    @property
    def files(self):
        return self._files
    
    def add_file(self, state, filename):
        self._files[state].append(filename)

    def __call__(self):
        lines = self._text.split(_get_newline())
        if len(lines) == 0 or lines[0].strip() != os.path.basename(self._sandbox_root):
            return
        stat_state = _StatState()
        current_directory = None
        for line in lines[1:]:
            if re.match(r'^  (?:code|test|built|run|report)/.*$', line.rstrip()):
                current_directory = os.path.normpath(os.path.join(self._sandbox_root, line.strip()))
                stat_state.reset_state()
            else:
                found = False
                match = re.match('^    ({0})$'.format('|'.join(_BZR_FILE_STATES)), line.rstrip())
                if match:
                    stat_state.change_state(match.group(1))
                    found = True
                if not found and len(line.strip()) > 0:
                   filename = os.path.normpath(os.path.join(current_directory, line.strip()))
                   self.add_file(stat_state.state, filename)

class BzrSandbox:
    def __init__(self, path, verbose=False):
        self._sandbox_root = find_sandbox_root(path)
        self._verbose = verbose
        if self.sandbox_root is None:
            raise exceptions.RuntimeError('Unable to create bazaar sandbox without a sandbox root')

    @property
    def sandbox_root(self):
        return self._sandbox_root
    @sandbox_root.setter
    def sandbox_root(self, value):
        self._sandbox_root = value

    def stat(self):
        process = subprocess.Popen('bzr sb stat', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.sandbox_root)
        stdoutdata, stderrdata = process.communicate()
        process.wait()
        if self._verbose:
            print(stdoutdata)
        parser = _SandboxStatParser(stdoutdata, self.sandbox_root)
        parser()
        return parser.files

    def update(self):
        process = subprocess.Popen('bzr sb up', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.sandbox_root)
        stdoutdata, stderrdata = process.communicate()
        process.wait()
        if self._verbose:
            print(stdoutdata)
        if process.returncode == 0:
            revnos = {}
            for match in re.finditer('Updating (?P<name>[^/]+/[^/]+/[^ ]+) in [^{0}]*?{0}Now on revision (?P<revno>\d+)'.format(_get_newline()), stdoutdata):
                revnos[match.group('name')] = match.group('revno')
            return True
        else:
            raise exceptions.RuntimeError('Error updating sandbox directory: {0}'.format(stderrdata))

    def merge(self, from_location):
        process = subprocess.Popen('bzr sb merge --from {0}'.format(from_location), shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.sandbox_root)
        stdoutdata, stderrdata = process.communicate()
        process.wait()
        if self._verbose:
            print(stdoutdata)
        return process.returncode == 0
    
    def checkin(self, message):
        process = subprocess.Popen('bzr sb ci -m "{0}"'.format(message), shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.sandbox_root)
        stdoutdata, stderrdata = process.communicate()
        process.wait()
        if self._verbose:
            print(stdoutdata)
        return process.returncode == 0

    def push(self):
        process = subprocess.Popen('bzr sb push', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.sandbox_root)
        stdoutdata, stderrdata = process.communicate()
        process.wait()
        if self._verbose:
            print(stdoutdata)
        if process.returncode == 0:
            return True
        else:
            raise exceptions.RuntimeError('Error pushing sandbox directory: {0}'.format(stderrdata))

def cat(self, file_name, verbose=False):
    full_path = _parse_repo_path(file_name)
    process = subprocess.Popen('bzr cat {0}'.format(full_path), shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    return None if process.returncode != 0 else stdoutdata

def stat(self, path, verbose=False):
    bzr_root = find_bzr_root(path)
    if bzr_root is None:
        raise exceptions.RuntimeError('Unable to stat a non-bzr directory')
    process = subprocess.Popen('bzr stat', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=bzr_root)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    if verbose:
        print(stdoutdata)
    parser = _BzrStatParser(stdoutdata, bzr_root)
    parser()
    return parser.files

def update(self, path, verbose=False):
    bzr_root = find_bzr_root(path)
    if bzr_root is None:
        raise exceptions.RuntimeError('Unable to update a non-bzr directory')
    process = subprocess.Popen('bzr up', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=bzr_root)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    if verbose:
        print(stdoutdata)
    if process.returncode == 0:
        match = re.search('Tree is up to date at revision (?P<revno>\d+) of branch ', stdoutdata)
        return int(match.group('revno'))
    else:
        raise exceptions.RuntimeError('Error updating bzr directory: {0}'.format(stderrdata))

def _parse_args():
    parser = argparse.ArgumentParser(description='The script description is here...')

    # The are all optional parameters or flags
    parser.add_argument('-c', '--cat', metavar='PATH', dest='cat_path', required=False, help='cat a bazaar file')
    parser.add_argument('-s', '--stat', metavar='PATH', dest='stat_path', required=False, help='stat a bazaar directory')
    parser.add_argument('-ss', '--stat_sandbox', metavar='PATH', dest='stat_sandbox_path', required=False, help='stat a bazaar sandbox')
    parser.add_argument('-u', '--update', metavar='PATH', dest='update_path', required=False, help='update a bazaar directory')
    parser.add_argument('-us', '--update_sandbox', metavar='PATH', dest='update_sandbox_path', required=False, help='update a bazaar sandbox')
    #parser.add_argument('-ss', '--destination', metavar='DIRECTORY', dest='destination', required=False, help='destination directory')
    #parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show extra output')
    #parser.add_argument('-vv', '--extra-verbose', default=False, action='store_true', help='show extra extra output')
    #parser.add_argument('--simulated', default=False, action='store_true', help='do not actually execute the actions')

    args = parser.parse_args()
    cat_path = None if args.cat_path is None else args.cat_path.replace('\\', '/')
    stat_path = None if args.stat_path is None else os.path.abspath(args.stat_path)
    stat_sandbox_path = None if args.stat_sandbox_path is None else os.path.abspath(args.stat_sandbox_path)
    update_path = None if args.update_path is None else os.path.abspath(args.update_path)
    update_sandbox_path = None if args.update_sandbox_path is None else os.path.abspath(args.update_sandbox_path)

    return cat_path, stat_path, stat_sandbox_path, update_path, update_sandbox_path

def main():
    cat_path, stat_path, stat_sandbox_path, update_path, update_sandbox_path = _parse_args()
    try:
        if cat_path:
            print(cat(cat_path))
        if stat_path:
            for key, values in stat(stat_path).items():
                print(key)
                for value in values:
                    print('  {0}'.format(value))
        if stat_sandbox_path:
            bzr_sandbox = BzrSandbox(stat_sandbox_path)
            for key, values in bzr_sandbox.stat().items():
                print(key)
                for value in values:
                    print('  {0}'.format(value))
        if update_path:
            print(update(update_path))
        if update_sandbox_path:
            bzr_sandbox = BzrSandbox(update_sandbox_path)
            print(bzr_sandbox.update())
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
	sys.exit(main())

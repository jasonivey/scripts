#!/usr/bin/env python

import argparse
import collections
import exceptions
import os
import re
import shutil
import sys
import subprocess
import warnings

import bzr_vcs

_PATCH_EXTENSION = '.patch'
_SANDBOX_CONF = 'sandbox.conf'
_SANDBOX_PATCH = 'sandbox.patch'
_SANDBOX_FILE_ADDED = 'added'
_SANDBOX_FILE_MODIFIED = 'modified'
_SANDBOX_FILE_REMOVED = 'removed'
_SANDBOX_FILE_UNKNOWN = 'unknown'

_VERBOSE_OUTPUT = False
_EXTRA_VERBOSE_OUTPUT = False
_SIMULATED_ACTION = False

def _get_relative_path(filename, root_dir):
    dirname = os.path.dirname(filename)
    while len(dirname) >= len(root_dir):
        if os.path.normcase(dirname) == os.path.normcase(root_dir):
            return filename[len(dirname) + 1:]
        dirname = os.path.dirname(dirname)
    raise AssertionError('Unable to find {0} within this file path {1}'.format(root_dir, filename))

def _find_file_in_dir_hierarchy(start_dir, filename):
    dir = start_dir
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if os.path.isfile(os.path.join(dir, filename)):
            return dir
        else:
            dir = parent
        parent = os.path.abspath(os.path.join(dir, '..'))
    return None

def _find_sandbox_root(start_dir):
    return _find_file_in_dir_hierarchy(start_dir, _SANDBOX_CONF)
    
def _find_patch_root(start_dir):
    return _find_file_in_dir_hierarchy(start_dir, _SANDBOX_PATCH)

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _is_extra_verbose_output_enabled():
    return _EXTRA_VERBOSE_OUTPUT

def _is_operation_simulated():
    return _SIMULATED_ACTION

def _parse_args():
    parser = argparse.ArgumentParser(description='Create or restore diff files for a directory')
    action_group = parser.add_mutually_exclusive_group(required=True)
    
    action_group.add_argument('-c', '--create', default=False, action='store_true', help='create patch files from modified files')
    action_group.add_argument('-r', '--restore', default=False, action='store_true', help='restore patch files to directory')
    
    parser.add_argument('-s', '--source', metavar='DIRECTORY', dest='source', required=True, help='source directory')
    parser.add_argument('-d', '--destination', metavar='DIRECTORY', dest='destination', required=False, help='destination directory')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show extra output')
    parser.add_argument('-vv', '--extra-verbose', default=False, action='store_true', help='show extra extra output')
    parser.add_argument('--simulated', default=False, action='store_true', help='do not actually execute the actions')
    
    args = parser.parse_args()
    
    global _VERBOSE_OUTPUT
    global _EXTRA_VERBOSE_OUTPUT
    global _SIMULATED_ACTION
    
    _VERBOSE_OUTPUT = args.verbose
    _EXTRA_VERBOSE_OUTPUT = args.extra_verbose
    _SIMULATED_ACTION = args.simulated
    
    source = os.path.abspath(args.source)
    if args.create:
        exception_message = '--source argument must specify a valid sandbox or a sub-directory of a sandbox'
        if not source:
            raise argparse.ArgumentTypeError(exception_message)
        sandbox_root = _find_sandbox_root(source)
        if not sandbox_root:
            raise argparse.ArgumentTypeError(exception_message)
        destination = os.path.abspath(args.destination) if args.destination else os.getcwd()
        if not os.path.isdir(destination):
            if _is_verbose_output_enabled():
                print('Creating directory {0}'.format(destination))
            #if not _is_operation_simulated():
            #The code relies on this directory -- can't find the directory without it -- refactor!
            os.makedirs(destination)
        if not os.path.isfile(os.path.join(destination, _SANDBOX_PATCH)):
            print('Creating {0} in {1}'.format(_SANDBOX_PATCH, destination))
            #if not _is_operation_simulated():
            #The code relies on this file being present -- can't find the directory without it -- refactor!
            if not os.path.isdir(destination):
                os.makedirs(destination)
            with open(os.path.join(destination, _SANDBOX_PATCH), 'a'):
                pass
        else:
            print('Appending to an existing {0} in {1}'.format(_SANDBOX_PATCH, destination))
        destination = os.path.normpath(destination + source[len(sandbox_root):])
        if not _is_operation_simulated() and not os.path.isdir(destination):
            os.makedirs(destination)
    else:
        if not source or not os.path.isdir(source):
            raise argparse.ArgumentTypeError('--source argument must specify a valid directory')
        destination = _find_sandbox_root(os.path.abspath(args.destination) if args.destination else os.getcwd())
        if not destination:
            raise argparse.ArgumentTypeError('--destination argument must specify a valid sandbox or a sub-directory of a sandbox')
        sandbox_root = destination

    return args.create, args.restore, sandbox_root, source, destination

def _get_eol():
    if os.name == 'nt':
        return '\r\n'
    elif sys.platform == 'darwin':
        return '\r'

def _is_file_in_directory(file_name, directory):
    if not os.path.isfile(file_name) or not os.path.isdir(directory):
        return False
    file_dir = os.path.dirname(file_name)
    while len(file_dir) >= len(directory):
        if os.path.normcase(file_dir) == os.path.normcase(directory):
            return True
        file_dir = os.path.dirname(file_dir)
    return False

def _get_diff_program():
    if os.name == 'nt':
        return r'd:\tools\gow\bin\diff'
    else:
        return 'diff'

def _create_patch_file_impl(orig_src_file, src_file, dst_file):
    cat_process = subprocess.Popen('bzr cat {0} > {1}'.format(os.path.basename(src_file), orig_src_file),
                                   shell=True,
                                   bufsize=1,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=os.path.dirname(src_file))
    cat_process.wait()
    if cat_process.returncode != 0:
        return False

    command = '{0} -u {1} {2} > {3}'.format(_get_diff_program(), orig_src_file, src_file, dst_file + _PATCH_EXTENSION)
    patch_process = subprocess.Popen(command,
                                     shell=True,
                                     bufsize=1,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     cwd=os.path.dirname(src_file))
    patch_process.wait()
    return patch_process.returncode == 0

def _create_patch_file(src_file, dst_file):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', exceptions.RuntimeWarning)
            orig_src_file = os.tempnam()
            _create_patch_file_impl(orig_src_file, src_file, dst_file)
    finally:
        if os.path.isfile(orig_src_file):
            os.remove(orig_src_file)

def _create_directory_tree(dir_name):
    if not os.path.isdir(dir_name):
        if _is_verbose_output_enabled():
            print('Creating directory {0}'.format(dir_name))
        if not _is_operation_simulated():
            os.makedirs(dir_name)

def _output_sandbox_patch(patch_file, file_type, relative_path):
    relative_path = relative_path if os.name != 'nt' else relative_path.replace('\\', '/')
    print('{0}, {1}'.format(file_type, relative_path), file=patch_file)

def create_patch_files(sandbox_root, src_dir, dst_dir):
    patch_root = _find_patch_root(dst_dir)
    sandbox_vcs = bzr_vcs.BzrSandbox(sandbox_root, _is_verbose_output_enabled())
    with open(os.path.join(patch_root, _SANDBOX_PATCH), 'a') as patch_file:
        for file_state, path_names in sandbox_vcs.stat().items():
            file_state = file_state.rstrip(':')
            for path_name in path_names:
                if _is_file_in_directory(path_name, src_dir):
                    relative_path = _get_relative_path(path_name, sandbox_root)
                    assert relative_path
                    dst_file = os.path.join(patch_root, relative_path)
                    _output_sandbox_patch(patch_file, file_state, relative_path)
        
                    if file_state == 'added':
                        print('Adding file {0}'.format(relative_path))
                        if os.path.isfile(dst_file):
                            if _is_verbose_output_enabled():
                                print('Removing the existing file already located in the sandbox patch {0}'.format(relative_path))
                            if not _is_operation_simulated():
                                os.remove(dst_file)
                        _create_directory_tree(os.path.dirname(dst_file))
                        if not _is_operation_simulated():
                            shutil.copy2(path_name, dst_file)
                    elif file_state == 'modified':
                        print('Creating a patch file for {0}'.format(relative_path))
                        if os.path.isfile(dst_file):
                            if _is_verbose_output_enabled():
                                print('Removing the existing file already located in the sandbox patch {0}'.format(relative_path))
                            if not _is_operation_simulated():
                                os.remove(dst_file)
                        _create_directory_tree(os.path.dirname(dst_file))
                        if not _is_operation_simulated():
                            _create_patch_file(path_name, dst_file)
                    elif file_state == 'removed':
                        print('Creating a removal entry in the sandbox patch file for {0}'.format(relative_path))
                        if os.path.isfile(dst_file):
                            if _is_verbose_output_enabled():
                                print('Removing the existing file already located in the sandbox patch {0}'.format(relative_path))
                            if not _is_operation_simulated():
                                os.remove(dst_file)
                        pass
                    elif file_state == 'unknown':
                        # Nothing to do other than ask the user whether they forgot to add something to bazaar!
                        print('The file {0} is marked as unknown'.format(relative_path))

def restore_patch_files(sandbox_root, src_dir):
    patch_root = _find_patch_root(src_dir)
    if not patch_root:
        raise AssertionError('This directory is not a valid formed patch directory using this script.')

    sandbox_files = collections.defaultdict(list)
    with open(os.path.join(patch_root, _SANDBOX_PATCH)) as patch_file:
        for line in patch_file.readlines():
            parts = line.split(',')
            assert len(parts) == 2
            file_type, filename = parts[0].strip(), os.path.normpath(os.path.join(patch_root, parts[1].strip()))
            sandbox_files[file_type].append(filename)

    for file_state, path_names in sandbox_files.items():
        for path_name in path_names:
            relative_path = _get_relative_path(path_name, patch_root)
            dst_file = os.path.join(sandbox_root, relative_path)
    
            if file_state == 'added':
                print('Adding file {0}, (don not forget to bzr add)'.format(relative_path))
                if not os.path.isfile(sandbox_file.filename):
                    print('ERROR: Unable to add {0} since it is missing in the patch'.format(relative_path))
                if os.path.isfile(dst_file):
                    if _is_verbose_output_enabled():
                        print('Removing the existing file already located in the sandbox {0}'.format(relative_path))
                    if not _is_operation_simulated():
                        os.remove(dst_file)
                _create_directory_tree(os.path.dirname(dst_file))
                if not _is_operation_simulated():
                    shutil.copy2(sandbox_file.filename, dst_file)
            elif file_state == 'modified':
                print('Patching file {0}'.format(relative_path))
                if not os.path.isfile(sandbox_file.filename + _PATCH_EXTENSION):
                    print('ERROR: Unable to apply patch {0} since it is missing'.format(relative_path + _PATCH_EXTENSION))
                if not os.path.isfile(dst_file):
                    print('ERROR: Unable to apply patch since destination file is missing {0}'.format(dst_file))
                if not _is_operation_simulated():
                    subprocess.check_call(['patch', '-i', sandbox_file.filename + _PATCH_EXTENSION, dst_file])
            elif file_state == 'removed':
                print('Removing file {0}'.format(relative_path))
                if not os.path.isfile(dst_file):
                    print('ERROR: Unable to remove destination file since it is missing {0}'.format(dst_file))
                if not _is_operation_simulated():
                    os.remove(dst_file)
            elif file_state == 'unknown':
                # How in the world did this get in there!
                pass

def main():
    create, restore, sandbox_root, source, destination = _parse_args()
    if _is_verbose_output_enabled():
        print('Args:')
        print('  Creating:       {0}'.format(create))
        print('  Restoring:      {0}'.format(restore))
        print('  Sandbox Root:   {0}'.format(sandbox_root))
        print('  Source:         {0}'.format(source))
        print('  Destination:    {0}'.format(destination))
        print('  Verbose Mode:   {0}'.format(_is_verbose_output_enabled()))
        print('  Simulated Mode: {0}'.format(_is_operation_simulated()))

    if create:
        create_patch_files(sandbox_root, source, destination)
    elif restore:
        restore_patch_files(sandbox_root, source)
    return 0

if __name__ == '__main__':
	sys.exit(main())

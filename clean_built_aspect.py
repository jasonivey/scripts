#!/usr/bin/env python
from __future__ import print_function
import argparse
import ConfigParser
import os
import pep8
import re
import shutil
import sys
import traceback

import custom_utils

_SANDBOX_CONF = 'sandbox.conf'
_SANDBOX_CONF_SETTINGS_SECTION = 'settings'
_SANDBOX_CONF_TARGETED_PLATFORM = 'targeted platform'
_BAZAAR_ROOT = '.bzr'

_VERBOSE_OUTPUT = False
_SIMULATED_MODE = False

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _simulated_mode_is_enabled():
    return _SIMULATED_MODE

def _parse_args():
    parser = argparse.ArgumentParser(description='Clean sandbox built aspect')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show extra output')
    parser.add_argument('-s', '--simulated', default=False, action='store_true', help='do not actually execute the actions')
    parser.add_argument('sandbox_dir', metavar='<DIR>', help='sandbox directory or sub-directory of sandbox')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    global _SIMULATED_MODE
    _VERBOSE_OUTPUT = args.verbose
    _SIMULATED_MODE = args.simulated
    return os.path.abspath(args.sandbox_dir)

def _delete_directory_entry(path_name):
    if os.path.isfile(path_name):
        if _is_verbose_output_enabled():
            print('Deleting file {0}'.format(path_name))
        if not _simulated_mode_is_enabled():
            os.remove(path_name)
    if os.path.isdir(path_name):
        if os.path.isdir(os.path.join(path_name, _BAZAAR_ROOT)):
            if _is_verbose_output_enabled():
                print('Not deleting bazaar repository {0}'.format(path_name))
        else:
            if _is_verbose_output_enabled():
                print('Deleting directory {0}'.format(path_name))
            if not _simulated_mode_is_enabled():
                shutil.rmtree(path_name, True)
    
def _get_targeted_platform(sandbox_root):
    config = ConfigParser.SafeConfigParser()
    with open(os.path.join(sandbox_root, _SANDBOX_CONF)) as conf_file:
        config.readfp(conf_file)
        for name, value in config.items(_SANDBOX_CONF_SETTINGS_SECTION):
            if name.lower().strip() == _SANDBOX_CONF_TARGETED_PLATFORM:
                return value.lower().strip()
    return custom_utils.get_platform_id()

def _find_built_aspect(start_dir):
    sandbox_root = custom_utils.find_path_in_directory(start_dir, filename=_SANDBOX_CONF)
    if sandbox_root is None:
        raise exceptions.RuntimeError('Unable to find sandbox root within {0}'.format(start_dir))

    built_dir = os.path.join(sandbox_root, 'built.{0}'.format(_get_targeted_platform(sandbox_root)))
    if os.path.isdir(built_dir):
        return built_dir

    existing_built_dirs = []
    for platform in custom_utils.get_supported_platforms():
        built_dir = os.path.join(sandbox_root, 'built.{0}'.format(platform))
        if os.path.isdir(built_dir):
            return built_dir

    raise exceptions.RuntimeError('Unable to find a built directory within {0}'.format(start_dir))

def clean(start_dir):
    built_dir = _find_built_aspect(start_dir)
    for path_entry in os.listdir(built_dir):
        path_name = os.path.join(built_dir, path_entry)
        _delete_directory_entry(path_name)

def main():
    sandbox_dir = _parse_args()
    try:
        clean(sandbox_dir)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
	sys.exit(main())

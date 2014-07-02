#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import shutil
import string
import subprocess
import sys
import tempfile

if os.name != 'nt':
    print('ERROR: Script is only valid on Windows NT platforms!')
    sys.exit(1)

from _winreg import *
from win32con import HWND_BROADCAST
from win32con import WM_SETTINGCHANGE
from win32con import SMTO_ABORTIFHUNG
from win32gui import SendMessageTimeout

SYSTEM_ENVIRONMENT_VARIABLE = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
USER_ENVIRONMENT_VARIABLE = r'Environment'
REGISTRY_HIVES = {'system' : HKEY_LOCAL_MACHINE, 'user' : HKEY_CURRENT_USER}
REGISTRY_HIVES_STRS = {'HKEY_LOCAL_MACHINE' : HKEY_LOCAL_MACHINE, 'HKEY_CURRENT_USER' : HKEY_CURRENT_USER}
REGISTRY_STRS_HIVES = {HKEY_LOCAL_MACHINE : 'HKEY_LOCAL_MACHINE', HKEY_CURRENT_USER : 'HKEY_CURRENT_USER'}

def _inform_os_environment_changed():
    SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 100)

class TempDir:
    '''
    A temporary directory that is created at the top of Python's "with" statement
    and deleted at the end of the block.
    '''
    def __init__(self, path=None):
        if path is not None:
            path = os.path.abspath(path)
        self.path = path
    def __enter__(self):
        if self.path:
            assert(not os.path.isdir(self.path))
            os.makedirs(self.path)
        else:
            self.path = tempfile.mkdtemp()
        return self
    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.path)


class RegistryKey(object):
    def __init__(self, registry_var, key_name_str, key_name, subkey_name, values=None):
        self._registry_var = registry_var
        self._key_name_str = key_name_str
        self._key_name = key_name
        self._subkey_name = subkey_name
        self._values = [] if values == None else values.split(';')
        if values == None:
            self._type = None
        else:
            self._type = REG_EXPAND_SZ if '%' in values else REG_SZ
        self._dirty = False
    
    @property
    def KeyName(self):
        return self._key_name
    
    @property
    def IsDirty(self):
        return self._dirty
    
    def read(self):
        values, self._type = RegistryKey.get_registry_type_value(self._key_name, \
                                                                 self._subkey_name, \
                                                                 self._registry_var)
        self._values = [] if values == None else values.split(';')

    def write(self):
        if not self._dirty:
            return
        RegistryKey.set_registry_value(self._key_name, \
                                       self._subkey_name, \
                                       self._registry_var, \
                                       ';'.join(self._values), \
                                       self._type)

    @staticmethod
    def get_normalized_path(filepath):
        if '%' in filepath:
            filepath = ExpandEnvironmentStrings(filepath)
        return os.path.normcase(os.path.normpath(filepath))

    def add_path(self, filepath):
        self._values.append(os.path.normcase(os.path.normpath(filepath)))
        self._dirty = True
    
    def remove_path(self, filepath):
        new_values = []
        for value in self._values:
            if RegistryKey.get_normalized_path(value) != RegistryKey.get_normalized_path(filepath):
                new_values.append(value)
        self._values = new_values
        self._dirty = True

    def __contains__(self, filepath):
        for value in self._values:
            if RegistryKey.get_normalized_path(value) == RegistryKey.get_normalized_path(filepath):
                return True
        return False

    def equal(self, other):
        other_values = map(string.lower, other._values)
        these_values = map(string.lower, self._values)

        these_not_equal = [value for value in these_values if value not in other_values]
        other_not_equal = [value for value in other_values if value not in these_values]
        
        return len(these_not_equal) == 0 and len(other_not_equal) == 0

    def __eq__(self, other):
        equal = self.equal(other)
        self._dirty, other._dirty = equal, equal
        return equal

    def __ne__(self, other):
        not_equal = not self.equal(other)
        self._dirty, other._dirty = not_equal, not_equal
        return not_equal

    def __str__(self):
        return '\n'.join(self._values)

    @staticmethod
    def get_registry_type_value(key, subkey, varname):
        value, type = None, None
        with OpenKey(key, subkey, 0, KEY_READ) as reg:
            try:
                value, type = QueryValueEx(reg, varname)
            except WindowsError as error:
                # OK: The system cannot find the file specified
                if error.args[0] != 2:
                    raise error
        return value, type

    @staticmethod
    def set_registry_value(key, subkey, varname, value, type):
        with OpenKey(key, subkey, 0, KEY_SET_VALUE) as reg:
            SetValueEx(reg, varname, None, type, value)
        _inform_os_environment_changed()

class EnvironmentVariable(object):
    def __init__(self, registry_hives, env_var, value=None):
        self._env_var_name = env_var
        self._registry_keys = []
        
        values = EnvironmentVariable._parse_environment_variable(value)

        for hive in registry_hives:
            assert(hive in REGISTRY_STRS_HIVES)
            if value != None:
                value = ';'.join(values[hive]) if hive in values else ''
            if hive == HKEY_LOCAL_MACHINE:
                regkey = RegistryKey(self._env_var_name, hive, HKEY_LOCAL_MACHINE, SYSTEM_ENVIRONMENT_VARIABLE, value)
            else:
                regkey = RegistryKey(self._env_var_name, hive, HKEY_CURRENT_USER, USER_ENVIRONMENT_VARIABLE, value)
            self._registry_keys.append(regkey)

        self._registry_keys.sort(key=lambda x: x.KeyName, reverse=True)

    @staticmethod
    def _parse_environment_variable(value):
        if not value:
            return {}
        values = {}
        selected_hive = None
        for val in value.split(';'):
            if not val:
                continue
            if val in REGISTRY_HIVES_STRS:
                selected_hive = REGISTRY_HIVES_STRS[val]
            else:
                if selected_hive in values:
                    values[selected_hive].append(val)
                else:
                    values[selected_hive] = [val]
        return values

    def add_path(self, filepath, force):
        assert(len(self._registry_keys) == 1)
        orig_filepath = filepath
        if filepath in self._registry_keys[0]:
            print('The path {0} is already set in the environment variable'.format(filepath))
            return
        if not os.path.isdir(filepath) and not force:
            print('ERROR: The path {0} does not exist on the system.  Override error using --force.'.format(filepath))
            return
        
        self._registry_keys[0].add_path(orig_filepath)
        self._registry_keys[0].write()

    def remove_path(self, filepath, force):
        assert(len(self._registry_keys) == 1)
        if filepath not in self._registry_keys[0]:
            print('The path {0} is not in the environment variable'.format(filepath))
            return
        if not os.path.isdir(filepath) and not force:
            print('ERROR: The path {0} does not exist on the system.  Override error using --force.'.format(filepath))
            return

        self._registry_keys[0].remove_path(filepath)
        self._registry_keys[0].write()

    def synch_to_system(self):
        [regkey.write() for regkey in self._registry_keys if regkey.IsDirty]

    def __enter__(self):
        [regkey.read() for regkey in self._registry_keys]
        return self

    def __exit__(self, type, value, traceback):
        pass
    
    def __eq__(self, other):
        if len(self._registry_keys) != len(other._registry_keys):
            return False
        equal = True
        for self_regkey, other_regkey in zip(self._registry_keys, other._registry_keys):
            assert(self_regkey.KeyName == other_regkey.KeyName)
            if self_regkey != other_regkey:
                equal = False
        return equal

    def __str__(self):
        strs = []
        for regkey in self._registry_keys:
            strs.append('%s\n%s\n\n' % (REGISTRY_STRS_HIVES[regkey.KeyName], regkey))
        return ''.join(strs).strip()

def _get_default_text_editor():
    text_editor_name, type = RegistryKey.get_registry_type_value(HKEY_CLASSES_ROOT, '.txt', '')
    registry_text_editor_name = r'%s\shell\open\command' % text_editor_name

    editor_path, type = RegistryKey.get_registry_type_value(HKEY_CLASSES_ROOT, registry_text_editor_name, '')
    if type == REG_EXPAND_SZ:
        editor_path = ExpandEnvironmentStrings(editor_path)

    if not editor_path:
        return RegistryKey.get_normalized_path(os.path.join('%windir%', 'notepad.exe'))
    else:
        return editor_path.replace(' "%1"', '').replace(' %1', '').strip('"')

def _edit_file(file_name):
    text_editor = _get_default_text_editor()
    
    process = subprocess.Popen('%s "%s"' % (os.path.basename(text_editor), file_name),
                               shell=True, bufsize=1, cwd=os.path.dirname(text_editor))
    retval = process.wait()
    
    return retval

def edit_environment_variable(registry_hive_ids, variable):
    new_environment_variable = None
    with TempDir() as tmpdir:
        with EnvironmentVariable(registry_hive_ids, variable) as environment_variable:
            env_vars_path = os.path.join(tmpdir.path, 'env-vars.txt')
            with open(env_vars_path, 'w') as env_file:
                env_file.write(str(environment_variable))
    
            _edit_file(env_vars_path)
    
            with open(env_vars_path) as env_file:
                new_env_vars = ';'.join(map(string.strip, env_file.readlines()))
                new_environment_variable = EnvironmentVariable(registry_hive_ids, variable, new_env_vars)
            
            if new_environment_variable == environment_variable:
                print('Environment variables have not been modified.')
                return 0

    try:
        answer = raw_input('Environment variables have changed. Update system [y]: ')
    except SyntaxError, EOFError:
        answer = 'n'
    if len(answer) == 0:
        answer = 'y'
    elif answer.lower().startswith('y'):
        answer = 'y'
    else:
        answer = 'n'
    
    if answer == 'n':
        print('Not updating environment variables.')
    else:
        print('Updating environment variables NOW!')
        new_environment_variable.synch_to_system()

def show_environment_variable(registry_hive_ids, variable):
    with EnvironmentVariable(registry_hive_ids, variable) as environment_variable:
        print(environment_variable)

def add_environment_variable(registry_hive_ids, variable, filepath, force):
    with EnvironmentVariable(registry_hive_ids, variable) as environment_variable:
        environment_variable.add_path(filepath, force)

def remove_environment_variable(registry_hive_ids, variable, filepath, force):
    with EnvironmentVariable(registry_hive_ids, variable) as environment_variable:
        environment_variable.remove_path(filepath, force)

def parse_command_line():
    parser = argparse.ArgumentParser(description='Edit environment variable')
    action_group = parser.add_mutually_exclusive_group(required=True)

    action_group.add_argument('-e', '--edit', default=False, action='store_true', help='edit the environment variable in a notepad')
    action_group.add_argument('-s', '--show', default=False, action='store_true', help='show the environment variable')
    action_group.add_argument('-u', '--update', default=False, action='store_true', help='inform the system that the environment has changed')
    action_group.add_argument('-a', '--add', metavar='<path>', help='add a new directory to the environment variable')
    action_group.add_argument('-r', '--remove', metavar='<path>', help='remove a directory from the environment variable')

    #parser.add_argument('--expand-strings', default=False, action='store_true', help='expand environment strings (windir) when showing')
    parser.add_argument('-f', '--force', default=False, action='store_true', help='forces add or remove to complete if dir does/does\'t exist')
    parser.add_argument('-v', '--variable', metavar='<env var>', default='PATH', help='specifies the environment variable to use -- defaults to PATH')
    
    registry_choices = [hive for hive in REGISTRY_HIVES.keys()]
    registry_choices.append('|'.join(REGISTRY_HIVES.keys()))
        
    parser.add_argument('--registry', choices=registry_choices, default=registry_choices[-1], help='specifies which registry hive to use')
    
    args = parser.parse_args()
    registry_hive_ids = []
    for registry_hive in args.registry.split('|'):
        registry_hive_ids.append(REGISTRY_HIVES[registry_hive])

    if (args.add or args.remove) and len(registry_hive_ids) > 1:
        print('ERROR: When adding or removing directories only one registry hive must be specified.')
        sys.exit(2)

    return args.show, args.edit, args.update, args.add, args.remove, args.force, registry_hive_ids, args.variable

def main():
    show, edit, update, add, remove, force, registry_hive_ids, variable = parse_command_line()

    if edit:
        edit_environment_variable(registry_hive_ids, variable)
    if show:
        show_environment_variable(registry_hive_ids, variable)
    if update:
        print('Informing the system that the environment has been modified')
        _inform_os_environment_changed()
    if add:
        add_environment_variable(registry_hive_ids, variable, add, force)
    if remove:
        remove_environment_variable(registry_hive_ids, variable, remove, force)
    
if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python
from __future__ import print_function
import argparse
import datetime
import exceptions
import os
import pep8
import platform
import re
import subprocess
import sys
import time
import traceback

class ScopedTimer(object):
    TIMER_TIME_OF_DAY = 1
    TIMER_ELAPSED = 2
    ALL_TIMERS = [TIMER_TIME_OF_DAY, TIMER_ELAPSED]
    
    ELAPSED_PROMPT_KEY = 'ELAPSED_PROMPT'
    TIME_OF_DAY_PROMPT_KEY = 'TIME_OF_DAY_PROMPT'
    STATUS_PROMPTS_DICT = {ELAPSED_PROMPT_KEY:'{0}', TIME_OF_DAY_PROMPT_KEY:'{0}'}

    def __init__(self, file=None, flags=ALL_TIMERS, prompts=STATUS_PROMPTS_DICT):
        self._file = file if file is not None else sys.stdout
        self._flags = flags if flags is not None else ALL_TIMERS
        self._prompts = prompts if prompts is not None else ScopedTimer.STATUS_PROMPTS_DICT
        for flag in self._flags:
            if flag == ScopedTimer.TIMER_TIME_OF_DAY:
                assert ScopedTimer.TIME_OF_DAY_PROMPT_KEY in self._prompts
            if flag == ScopedTimer.TIMER_ELAPSED:
                assert ScopedTimer.ELAPSED_PROMPT_KEY in self._prompts
        self._start = None
    def __enter__(self):
        self._start = datetime.datetime.now()
        if ScopedTimer.TIMER_TIME_OF_DAY in self._flags:
            print(self._prompts[ScopedTimer.TIME_OF_DAY_PROMPT_KEY].format(self._start.strftime('%I:%M:%S %p')), file=self._file)
        return self
    def __exit__(self, type, value, traceback):
        self._get_status()
    @property
    def status(self):
        self._get_status()
    def _get_status(self):
        end_time = datetime.datetime.now()
        if ScopedTimer.TIMER_TIME_OF_DAY in self._flags:
            print(self._prompts[ScopedTimer.TIME_OF_DAY_PROMPT_KEY].format(end_time.strftime('%I:%M:%S %p')), file=self._file)
        if ScopedTimer.TIMER_ELAPSED in self._flags:
            elapsed_time = end_time - self._start
            hours = int(elapsed_time.seconds / 3600)
            minutes = int((elapsed_time.seconds % 3600) / 60)
            seconds = int((elapsed_time.seconds % 3600) % 60)
            milli_seconds = int(elapsed_time.microseconds / 1000)
            str = '{0:02}:{1:02}:{2:02}.{3:03}'.format(hours, minutes, seconds, milli_seconds)
            print(self._prompts[ScopedTimer.ELAPSED_PROMPT_KEY].format(str), file=self._file)

def get_supported_platforms():
    return ['win_x64', 'win_32', 'linux_x86-64', 'linux_i686', 'osx_universal']

def get_platform_id():
    _u = platform.uname()
    uname = [_u[0], _u[1], _u[2], _u[3], _u[4], _u[5]]
    bitness = '64' if uname[4].find('64') != -1 or uname[5].find('64') != -1 else '32'

    if os.name == 'nt':
        return 'win_x64' if bitness == '64' else 'win_32'
    elif uname[0].startswith('Darwin'):
        return 'osx_universal'
    elif uname[0] == 'Linux':
        return 'linux_x86-64' if bitness == '64' else 'linux_i686'
    else:
        raise exceptions.RuntimeError('Unknown platform encountered: "{0}"'.format(uname[0]))

def find_path_in_directory(start_dir, filename=None, dirname=None):
    dir = start_dir
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if dirname is not None and os.path.isdir(os.path.join(dir, dirname)):
            return dir
        elif filename is not None and os.path.isfile(os.path.join(dir, filename)):
            return dir
        else:
            dir = parent
        parent = os.path.abspath(os.path.join(dir, '..'))
    return None

def prepare_filename_for_shell(file_name):
    return '"{0}"'.format(file_name.replace('\\', '\\\\').replace('"', '\"').replace('$', '\$').replace('`', '\`'))    

def is_binary_in_path(file_name):
    command = '{0} {1}'.format('where' if os.name == 'nt' else 'which', prepare_filename_for_shell(file_name))
    process = subprocess.Popen(command, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return process.wait() == 0

def get_files_in_directory_old(start_dir, predicate=None, sort=False, recurse=True):
    paths = []
    if not recurse:
        for file_name in os.listdir(start_dir):
            if os.path.isfile(os.path.join(start_dir, file_name)):
                if predicate is not None and predicate(os.path.join(start_dir, file_name)):
                    paths.append(os.path.join(start_dir, file_name))
    else:
        for root, dirs, files in os.walk(start_dir):
            for file_name in files:
                if predicate is not None and predicate(os.path.join(root, file_name)):
                    paths.append(os.path.join(root, file_name))
    if sort:
        paths.sort(key=string.lower if os.name == 'nt' else None)
    return paths

def get_files_in_directory(start_dir, predicate=None, sort=False, recurse=True):
    paths = []
    if not recurse:
        for file_name in os.listdir(start_dir):
            if os.path.isfile(os.path.join(start_dir, file_name)):
                if predicate is None or predicate(os.path.join(start_dir, file_name)):
                    if not sort:
                        yield os.path.join(start_dir, file_name)
                    else:
                        paths.append(os.path.join(start_dir, file_name))
    else:
        for root, dirs, files in os.walk(start_dir):
            for file_name in files:
                if predicate is None or predicate(os.path.join(root, file_name)):
                    if not sort:
                        yield os.path.join(root, file_name)
                    else:
                        paths.append(os.path.join(root, file_name))
    if sort:
        paths.sort(key=string.lower if os.name == 'nt' else None)
        for path_name in paths:
            yield path_name

def _process():
    time.sleep(1)
    print('{0} is in path: {1}'.format(sys.argv[1], is_binary_in_path(sys.argv[1])))

def _main():
    try:
        with ScopedTimer(flags=[ScopedTimer.TIMER_TIME_OF_DAY], prompts={ScopedTimer.TIME_OF_DAY_PROMPT_KEY:'Begin/End {0}'}) as timer:
        #with ScopedTimer(flags=[ScopedTimer.TIMER_ELAPSED], prompts={ScopedTimer.ELAPSED_PROMPT_KEY:'Total time to execute {0} sec'}) as timer:
            _process()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
	sys.exit(_main())

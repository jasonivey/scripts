#!/usr/bin/env python

import argparse
import os
import shutil
import sys
import subprocess
import tempfile
import time
import traceback

_VERBOSE_OUTPUT = False
_EXTRA_VERBOSE_OUTPUT = False
_SIMULATED_MODE = False

if os.geteuid() != 0:
    print('ERROR: Script needs to be run as either sudo or root')
    sys.exit(1)

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _is_extra_verbose_output_enabled():
    return _EXTRA_VERBOSE_OUTPUT

def _simulated_mode_is_enabled():
    return _SIMULATED_MODE

def kill_running_processes():
    PROCESSES = [('SearchServer', 'SearchServer'),
                 ('feeder', 'bin/feeder.jar'),
                 ('nginx', 'nginx'),
                 ('paster', '/usr/bin/paster'),
                 ('slapd', 'conf/slapd-development.conf')]
    process = subprocess.Popen('ps -aux', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    if _is_extra_verbose_output_enabled():
        print('ps -aux output:\n{0}'.format(stdoutdata.strip()))
    pids = []
    for line in stdoutdata.split('\n'):
        for process in PROCESSES:
            if process[1] in line:
                pid = line.split()[1]
                pids.append((pid, process[1]))
                break
    if len(pids) == 0 and _is_verbose_output_enabled():
        print('No running processes to kill')
    for pid in pids:
        if _is_verbose_output_enabled():
            print('Killing {0} : {1}'.format(pid[0], pid[1]))
        if not _simulated_mode_is_enabled():
            subprocess.check_call(['kill', pid[0]])

def _get_open_handles():
    process = subprocess.Popen('lsof', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    lines = stdoutdata.split('\n')
    # lsof prints a header on the first line and we can use that as information
    headers = [header for header in lines[0].split(' ') if len(header) > 0]
    handle_names = []
    for line in lines[1:]:
        if _is_extra_verbose_output_enabled():
            print(line.strip())
        parts = [parts for parts in line.split(' ') if len(parts) > 0]
        if len(parts) == len(headers):
            handle_name = parts[-1].strip()
            if handle_name not in handle_names and (os.path.isdir(handle_name) or os.path.isfile(handle_name)):
                if _is_verbose_output_enabled():
                    print('Open handle {0}'.format(handle_name))
                handle_names.append(handle_name)
    return handle_names

_PATH_TOO_OLD = 60 * 60 * 2 # 2 Hours
def _is_path_too_old(path_name):
    last_modified = os.path.getctime(path_name)
    now = time.time()
    return now > last_modified + _PATH_TOO_OLD

def _get_files_to_delete(dir_name):
    filenames = []
    for filename in os.listdir(dir_name):
        file_path = os.path.join(dir_name, filename)
        modified_time = time.gmtime(os.path.getctime(file_path))
        modified_time_str = time.strftime('%b %d, %Y - %I:%M:%S %p %Z', modified_time)
        if _is_path_too_old(file_path):
            if _is_extra_verbose_output_enabled():
                print('OLD {0}: {1}'.format(modified_time_str, file_path))
            filenames.append(file_path)
        else:
            if _is_extra_verbose_output_enabled():
                print('NEW {0}: {1}'.format(modified_time_str, file_path))
    return filenames
                  
def clean_temporary_directory():
    temp_path = tempfile.mkdtemp()
    temp_directory = os.path.dirname(temp_path)
    shutil.rmtree(temp_path, True)
    open_files = _get_open_handles()

    for path_name in _get_files_to_delete(temp_directory):
        if path_name in open_files:
            if _is_verbose_output_enabled():
                print('Unable to delete {0} since it is in use'.format(path_name))
        elif os.path.islink(path_name):
            if _is_verbose_output_enabled():
                print('Unable to delete {0} since it is a link'.format(path_name))
        elif os.path.ismount(path_name):
            if _is_verbose_output_enabled():
                print('Unable to delete {0} since it is a mount point'.format(path_name))
        elif os.path.isdir(path_name) :
            if _is_verbose_output_enabled():
                print('Deleting directory {0}'.format(path_name))
            if not _simulated_mode_is_enabled():
                subprocess.check_call(['rm', '-rf', path_name])
                if os.path.isdir(path_name):
                    print('ERROR: unable to delete {0}'.format(path_name))
        elif os.path.isfile(path_name):
            if _is_verbose_output_enabled():
                print('Deleting file {0}'.format(path_name))
            if not _simulated_mode_is_enabled:
                subprocess.check_call(['rm', '-rf', path_name])
                if os.path.isfile(path_name):
                    print('ERROR: unable to delete {0}'.format(path_name))

def _parse_args():
    parser = argparse.ArgumentParser(description='Clean the testing environment')
    parser.add_argument('-c', '--clean-tempdir', default=False, action='store_true', help='clean the temporary directory')
    parser.add_argument('-k', '--kill-processes', default=False, action='store_true', help='kill the running processes')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show verbose output')
    parser.add_argument('-vv', '--extra-verbose', default=False, action='store_true', help='show extra verbose output')
    parser.add_argument('-s', '--simulated', default=False, action='store_true', help='run in simulation mode')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    global _EXTRA_VERBOSE_OUTPUT
    global _SIMULATED_MODE
    _VERBOSE_OUTPUT = args.verbose
    _EXTRA_VERBOSE_OUTPUT = args.extra_verbose
    _SIMULATED_MODE = args.simulated
    return args.clean_tempdir, args.kill_processes

def main():
    _clean_tempdir, _kill_processes = _parse_args()
    try:
        if _clean_tempdir:
            clean_temporary_directory()
        if _kill_processes:
            kill_running_processes()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
	sys.exit(main())

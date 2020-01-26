#!/usr/bin/env python

import argparse
import glob
import os
import pep8
import re
import sys
import subprocess
import traceback

_VERBOSE_OUTPUT = False
_SIMULATED_MODE = False

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _simulated_mode_is_enabled():
    return _SIMULATED_MODE

def _parse_args():
    parser = argparse.ArgumentParser(description='Call HandBrakeCLI and convert media files')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show extra output')
    parser.add_argument('-s', '--simulated', default=False, action='store_true', help='do not actually execute the actions')
    parser.add_argument('destination', metavar='<DIR>', help='destination directory')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    global _SIMULATED_MODE
    _VERBOSE_OUTPUT = args.verbose
    _SIMULATED_MODE = args.simulated
    return args.destination

def is_media_file(file_name):
    extension = os.path.splitext(file_name)[1].lower()
    if _is_verbose_output_enabled():
        print('Extension: {0}'.format(extension))
    return extension in ['.avi', '.mkv']

def convert_media(output_dir):
    #output_dir = '/Volumes/MyBook/movies/ipod/Fringe/'
    for full_path in glob.glob('{0}/*.avi'.format(os.getcwd())):
        if _is_verbose_output_enabled():
            print('File name: {0}'.format(full_path))
        if not is_media_file(full_path):
            continue

        output_path = os.path.join(output_dir, os.path.splitext(full_path)[0] + '.m4v')
        if _is_verbose_output_enabled():
            print('New file name: {0}'.format(output_path))

        #match = re.match(r'Fringe\.S02E(?P<number>\d\d)\.(?P<title>.*)\.avi', os.path.basename(full_path))
        #assert match, full_path
        #if not os.path.isfile(full_path) or not is_media_file(full_path):
        #    continue
        #new_name = '2{0} - Fringe - {1}.m4v'.format(match.group('number'), match.group('title'))
        #output_path = os.path.join(output_dir, new_name)

        command = ['HandBrakeCLI', 
                   '--preset', '"AppleTV 2"', 
                   '--input', 
                   '"{0}"'.format(full_path) if ' ' in full_path else full_path,
                   '--output', 
                   '"{0}"'.format(output_path) if ' ' in output_path else output_path,
                   '--decomb']
        print('Converting {0}...'.format(os.path.basename(full_path)))
        if _is_verbose_output_enabled():
            print(command)
        if not _simulated_mode_is_enabled():
            process = subprocess.Popen(' '.join(command), shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.getcwd())
            stdoutdata, stderrdata = process.communicate()
            if process.wait() != 0:
                print('Failed to convert {0}, saving logs...'.format(os.path.basename(full_path)))
                with open(os.path.splitext(full_path)[0] + '.log', 'w') as log:
                    if stdoutdata is not None:
                        log.write('LOG Info:\n')
                        log.writelines(stdoutdata)
                    if stderrdata is not None:
                        log.write('ERROR Info:\n')
                        log.writelines(stderrdata)
            #subprocess.check_call(command)
    
def main():
    output_dir = _parse_args()
    try:
        convert_media(output_dir)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

if __name__ == '__main__':
    sys.exit(main())


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
    extension = os.path.splitext(file_name)[1]
    if _is_verbose_output_enabled():
        print('Extension: {0}'.format(extension))
    return extension.endswith('avi')

def convert_media(output_dir):
    input_files = [r"G:\movies\avi\Bee Movie.avi",
                   r"G:\movies\avi\Big Trouble.avi",
                   r"G:\movies\avi\Bourne Identity, The.avi",
                   r"G:\movies\avi\Bourne Supremacy, The.avi",
                   r"G:\movies\avi\Chronicles of Riddick, The.avi",
                   r"G:\movies\avi\Cloudy With A Chance Of Meat Balls.avi",
                   r"G:\movies\avi\Constantine.avi",
                   r"G:\movies\avi\Count of Monte Cristo, The.avi",
                   r"G:\movies\avi\Harry Connick Jr. - Harry for the Holidays.avi",
                   r"G:\movies\avi\Harry Connick, Jr - Only You.avi",
                   r"G:\movies\avi\Into The Wild.avi",
                   r"G:\movies\avi\Juno.avi",
                   r"G:\movies\avi\Last Samurai, The.avi",
                   r"G:\movies\avi\Led Zeppelin - Disc 1.avi",
                   r"G:\movies\avi\Led Zeppelin - Disc 2.avi",
                   r"G:\movies\avi\Man on Fire.avi",
                   r"G:\movies\avi\Metallica - Some Kind of Monster.avi",
                   r"G:\movies\avi\Nim's Island.avi",
                   r"G:\movies\avi\Ocean's Eleven.avi",
                   r"G:\movies\avi\Ocean's Twelve.avi",
                   r"G:\movies\avi\Open Range.avi",
                   r"G:\movies\avi\Pitch Black.avi",
                   r"G:\movies\avi\Rundown.avi",
                   r"G:\movies\avi\Super Rhino.avi"]

        #for full_path in glob.glob('{0}/*.avi'.format(os.getcwd())):
    for full_path in input_files:
        if _is_verbose_output_enabled():
            print('File name: {0}'.format(full_path))
        #match = re.match(r'Fringe\.S02E(?P<number>\d\d)\.(?P<title>.*)\.avi', os.path.basename(full_path))
        #assert match, full_path
        if not os.path.isfile(full_path) or not is_media_file(full_path):
            if _is_verbose_output_enabled():
                print('Skipping')
            continue
        #new_name = '2{0} - Fringe - {1}.m4v'.format(match.group('number'), match.group('title'))
        new_name = '{0} - iPad.m4v'.format(os.path.splitext(os.path.basename(full_path))[0])
        output_path = os.path.join(output_dir, new_name)
        assert not os.path.isfile(output_path), 'Destination already exists {0}'.format(output_path)
        command = ['HandBrakeCLI', 
                   #'--preset', '"AppleTV 2"', 
                   '--preset', '"iPad"', 
                   '--input', 
                   '"{0}"'.format(full_path) if ' ' in full_path else full_path,
                   '--output', 
                   '"{0}"'.format(output_path) if ' ' in output_path else output_path,
                   '--decomb']
        print('Converting {0}...'.format(new_name))
        if _is_verbose_output_enabled():
            print(command)
        if not _simulated_mode_is_enabled():
            process = subprocess.Popen(' '.join(command), shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.getcwd())
            stdoutdata, stderrdata = process.communicate()
            if process.wait() != 0:
                'Failed to convert {0}, saving logs...'.format(new_name)
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


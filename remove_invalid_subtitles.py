#!/usr/bin/env python3
# vim: aw:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

import argparse
import os
import re
import shlex
import subprocess
import sys
import traceback

from app_settings import app_settings

def _is_valid_directory(dir_name):
    if os.path.isdir(dir_name):
        return os.path.abspath(dir_name)
    raise argparse.ArgumentTypeError('The path "{}" is not a valid directory'.format(dir_name))

def _parse_args():
    parser = argparse.ArgumentParser(description='Find all of the subtitle files which are invalid')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-l', '--live-run', action="store_true", help='remove all of the invalid subtitle')
    parser.add_argument('directories', metavar='PATH', type=_is_valid_directory, nargs='+', help='one or more directories to search for invalid subtitles')
    args = parser.parse_args()
    app_settings.update(vars(args))
    app_settings.print_settings(print_always=False)

def _get_subtitle_filenames(dir_name):
    for root, dirs, files in os.walk(dir_name):
        for file_name in files:
            _, ext = os.path.splitext(file_name)
            if ext == '.srt':
                yield os.path.abspath(os.path.join(root, file_name))

def _get_subtitle_line_count(filename):
    args = shlex.split('wc -l "{}"'.format(filename))
    process = subprocess.Popen(args, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.wait() != 0:
        app_settings.error(f'{error} while getting line count on {filename}')
    match = re.match(r'^(?P<count>\d+)\s+.*$', output.strip())
    line_count = int(match.group('count')) if match else 0
    return line_count

def _get_invalid_subtitle_filenames(dir_name):
    for filename in _get_subtitle_filenames(dir_name):
        app_settings.debug(f'File: {filename}')
        line_count = _get_subtitle_line_count(filename)
        app_settings.debug(f'File: {filename}\n    : {line_count} lines')
        if line_count < 1000:
            app_settings.info(f'{line_count} - {filename} INVALID')
            yield filename

def remove_invalid_subtitles(dir_name):
    for filename in _get_invalid_subtitle_filenames(dir_name):
        if app_settings.live_run:
            try:
                app_settings.info(f'{filename} live run -- deleting')
                os.remove(path)
                app_settings.info(f'{filename} live run -- deleted')
            except OSError as e:
                app_settings.error(f'{e.code} - {e.stderr} file: {filename}')
        else:
            app_settings.info(f'{filename} dry run -- doing nothing')

def main():
    _parse_args()
    try:
        for dir_name in app_settings.directories:
            remove_invalid_subtitles(dir_name)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

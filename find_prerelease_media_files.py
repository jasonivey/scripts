#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import json
import os
import sys
import re
import traceback

gVerbose = 0

def enum(**enums):
    return type('Enum', (), enums)

LogSeverity = enum(ERROR=0, WARNING=1, INFO=2, DEBUG=3)

def _get_log_severity_str(severity):
    severity_str = None 
    if severity == LogSeverity.ERROR:
        severity_str = 'ERROR'
    elif severity == LogSeverity.WARNING:
        severity_str = 'WARNING'
    elif severity == LogSeverity.INFO:
        severity_str = 'INFO'
    elif severity == LogSeverity.DEBUG:
        severity_str = 'DEBUG'
    assert severity_str
    return severity_str

def log(severity, message, *args):
    if gVerbose < severity:
        return
    print(('%s: ' % _get_log_severity_str(severity)) + (message % args))

def _validate_log_severity(value):
    if value < LogSeverity.ERROR or value > LogSeverity.DEBUG:
        raise argparse.ArgumentTypeError('argument must be a valid log severity')
    return value

def _is_directory(value):
    if os.path.isdir(value):
        return os.path.normpath(os.path.abspath(value))
    raise argparse.ArgumentTypeError('argument must be a valid directory')

def _parse_args():
    description = 'Parse pre release media files such as HDRip or DVDScr'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('-d', '--media_dir', metavar='<dir>', default=os.getcwd(), type=_is_directory, help='directory where media files exist')
    parser.add_argument('-r', '--recurse', default=False, action='store_true', help='Switch whether it traverses sub directories')
    args = parser.parse_args()
    global gVerbose
    gVerbose = args.verbose
    _validate_log_severity(gVerbose)
    log(LogSeverity.INFO, 'Arguments:\n verbose: %d\n media directory: %s\n recurse: %s', gVerbose, args.media_dir, args.recurse)
    return args.media_dir, args.recurse

def _is_valid_media_file(filename):
    OS_FILES = ['.DS_Store', '._.DS_Store']
    if filename in OS_FILES or filename.startswith('._'):
        return False
    SUBTITLE_EXTENSIONS = ['.srt', '.idx', '.sub', '.smi', 'sbv']
    basename, ext = os.path.splitext(filename)
    return ext not in SUBTITLE_EXTENSIONS 

def _get_media_files(media_dir, recurse):
    media_files = []
    if recurse:
        for root, dirs, files in os.walk(media_dir):
            for filename in files:
                if not _is_valid_media_file(filename):
                    continue
                #media_files.append(os.path.join(root, filename))
                media_files.append(filename)
    else:
        for filename in os.listdir(media_dir):
            if not _is_valid_media_file(filename):
                continue
            #media_files.append(os.path.join(media_dir, filename))
            media_files.append(filename)

    media_files.sort()
    return media_files

def _is_prerelease_media_file(filename):
    basename, ext = os.path.splitext(filename)
    return basename[-1] != ')'

def _parse_media_filename(filename):
    index = filename.find(')')
    assert index != -1
    name = filename[:index + 1] + filename[filename.rfind('.'):]
    media_type = filename[index + 1 : filename.rfind('.')].strip(' -')
    return name, media_type

def _print_prerelease_media_files(filenames):
    media_type_length = 0
    for filename in filenames:
        name, media_type = _parse_media_filename(filename)
        media_type_length = max(media_type_length, len(media_type))

    fmt_str = '{:<' + str(media_type_length) + '} | {}'
    log(LogSeverity.DEBUG, fmt_str)

    for filename in filenames:
        name, media_type = _parse_media_filename(filename)
        print(fmt_str.format(media_type, name))

def main():
    media_dir, recurse = _parse_args()
    try:
        prerelease_media_files = []
        for filename in _get_media_files(media_dir, recurse):
            if _is_prerelease_media_file(filename):
                prerelease_media_files.append(filename)
        _print_prerelease_media_files(prerelease_media_files)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


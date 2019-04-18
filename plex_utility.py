#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import json
import os
import sys
import re
import tempfile
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

def _get_log_severity():
    return gVerbose

def log(severity, message, *args):
    if gVerbose < severity:
        return
    print(('%s: ' % _get_log_severity_str(severity)) + (message % args))

def _validate_log_severity(value):
    if value < LogSeverity.ERROR or value > LogSeverity.DEBUG:
        raise argparse.ArgumentTypeError('argument must be a valid log severity')
    return value

def sizeof_fmt(num):
    for unit in ['b','Kb','Mb','Gb','Tb','Pb','Eb','Zb']:
        if abs(num) < 1024.0:
            return '%3.1f%s' % (num, unit)
        num /= 1024.0
    return '%.1f%s' % (num, 'Yb')

def _is_directory(value):
    if os.path.isdir(value):
        return os.path.normpath(os.path.abspath(value))
    raise argparse.ArgumentTypeError('argument must be a valid directory')

def _parse_args():
    description = 'Plex Utility'
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

def IsDsStore(filename):
    with open(filename, 'r+b') as store:
        store.seek(0x54, os.SEEK_SET)
        signature = bytearray(store.read(4))
        #print(signature.decode("utf-8"))
        #print(len(signature.decode("utf-8")))
        ret = signature.decode("utf-8") == 'ATTR'
        if not ret:
            log(LogSeverity.ERROR, 'The name is correct but it doesn\'t have ATTR in data ({})'.format(filename))
        return ret

def IsDataStore(filename):
    with open(filename, 'r+b') as store:
        store.seek(0x04, os.SEEK_CUR)
        signature = bytearray(store.read(4))
        #print(signature.decode("utf-8"))
        #print(len(signature).decode("utf-8"))
        ret = signature.decode("utf-8") == 'Bud1'
        if not ret:
            log(LogSeverity.ERROR, 'The name is correct but it doesn\'t have Bud1 in data ({})'.format(filename))
        return ret

def _is_os_meta_file(filename):
    if os.path.basename(filename).startswith('.DS_Store'):
        return IsDataStore(filename)
    elif os.path.basename(filename).startswith('._') or os.path.basename(filename).startswith('._.DS_Store'):
        return IsDsStore(filename)

def _is_media_file(filename):
    return (filename.endswith('.mkv') or filename.endswith('.mp4') or filename.endswith('.m4v') or
            filename.endswith('.avi') or filename.endswith('.srt') or filename.endswith('.idx') or
            filename.endswith('.sub') or filename.endswith('.smi')) and not _is_os_meta_file(filename)

def _dump_lists_to_file(media_files1, non_media_files1, media_files2, non_media_files2):
    with tempfile.NamedTemporaryFile(mode='w+t', suffix='.txt', delete=True) as debug_file:
        log(LogSeverity.INFO, 'Creating a temporary file %s with the input data' % debug_file.name)
        debug_file.writelines(['MEDIA_FILES1', '\n'])
        filenames = [filename + '\n' for filename in media_files1]
        debug_file.writelines(filenames)
        debug_file.writelines(['\n', '\n', 'MEDIA_FILES2', '\n'])
        filenames = [filename + '\n' for filename in media_files2]
        debug_file.writelines(filenames)
        debug_file.writelines(['\n', '\n', 'NON_MEDIA_FILES1', '\n'])
        filenames = [filename + '\n' for filename in non_media_files1]
        debug_file.writelines(filenames)
        debug_file.writelines(['\n', '\n', 'NON_MEDIA_FILES2', '\n'])
        filenames = [filename + '\n' for filename in non_media_files2]
        debug_file.writelines(filenames)

def _validate_os_meta_file_finder(media_files1, non_media_files1, media_files2, non_media_files2):
    if _get_log_severity() >= LogSeverity.DEBUG:
        _dump_lists_to_file(media_files1, non_media_files1, media_files2, non_media_files2)

    media_files1_count, media_files2_count = len(media_files1), len(media_files2)
    count = max(media_files1_count, media_files2_count)
    for i in range(count):
        if i >= media_files1_count:
            raise RuntimeError('Iterated directory and found more media files (%d, %d)' % (media_files1_count, media_files2_count))
        if i >= media_files2_count:
            raise RuntimeError('generated media files found more media files (%d, %d)' % (media_files1_count, media_files2_count))

        media_file1, media_file2 = media_files1[i], media_files2[i]
        if media_file1 != media_file2:
            raise RuntimeError('media file at index %d are not equal (%s, %s)' % (i, media_file1, media_file2))

    log(LogSeverity.INFO, 'the media files are what we expect')

    non_media_files1_count, non_media_files2_count = len(non_media_files1), len(non_media_files2)
    count = max(non_media_files1_count, non_media_files2_count)
    for i in range(count):
        if i >= non_media_files1_count:
            raise RuntimeError('Iterated directory and found more meta files (%d, %d)' % (non_media_files1_count, non_media_files2_count))
        if i >= non_media_files2_count:
            raise RuntimeError('generated meta files found more meta files (%d, %d)' % (non_media_files1_count, non_media_files2_count))

        non_media_file1, non_media_file2 = non_media_files1[i], non_media_files2[i]
        if non_media_file1 != non_media_file2:
            raise RuntimeError('meta file at index %d are not equal (%s, %s)' % (i, non_media_file1, non_media_file2))
    
    log(LogSeverity.INFO, 'the meta files are what we expect')


def _get_valid_media_files(media_dir, recurse):
    media_files = []
    non_media_files = []
    if recurse:
        for root, dirs, files in os.walk(media_dir):
            for filename in files:
                if _is_media_file(os.path.join(root, filename)):
                    media_files.append(os.path.join(root, filename))
                else:
                    non_media_files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(media_dir):
            if _is_media_file(os.path.join(media_dir, filename)):
                media_files.append(os.path.join(media_dir, filename))
            else:
                non_media_files.append(os.path.join(media_dir, filename))
    media_files.sort()
    non_media_files.sort()
    return media_files, non_media_files


def _get_media_files(media_dir, recurse):
    media_files = []
    non_media_files = []
    if recurse:
        for root, dirs, files in os.walk(media_dir):
            for filename in files:
                if _is_os_meta_file(os.path.join(root, filename)):
                    non_media_files.append(os.path.join(root, filename))
                else:
                    media_files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(media_dir):
            if _is_os_meta_file(os.path.join(media_dir, filename)):
                non_media_files.append(os.path.join(media_dir, filename))
            else:
                media_files.append(os.path.join(media_dir, filename))

    media_files.sort()
    non_media_files.sort()

    media_files_check, non_media_files_check = _get_valid_media_files(media_dir, recurse)

    _validate_os_meta_file_finder(media_files, non_media_files, media_files_check, non_media_files_check)

    return media_files, non_media_files

def main():
    media_dir, recurse = _parse_args()
    try:
        media_files, non_media_files = _get_media_files(media_dir, True)
        print('\nMedia Files:')
        for filename in media_files:
            print(filename)
        print('\nNON Media Files:')
        for filename in non_media_files:
            print('{} - {}'.format(filename, sizeof_fmt(os.stat(filename).st_size)))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())



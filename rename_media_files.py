#!/usr/bin/python

import argparse
import json
import os
from pydub.utils import mediainfo
import shutil
import sys
import traceback

def _is_directory(directory):
    if not os.path.isdir(directory):
        msg = "{0} is not a valid directory".format(directory)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(directory))

def _parse_args():
    parser = argparse.ArgumentParser('rename media files')
    parser.add_argument('directory', metavar='<DIRECTORY>', type=_is_directory, help='directory to scan for media')
    parser.add_argument('-s', '--simulated', default=False, action='store_true', help='dry run the rename operation on the directory hierarchy')
    args = parser.parse_args()
    print('directory: {0}, simulated: {1}'.format(args.directory, args.simulated))
    return args.directory, args.simulated

def _find_media_files(directory):
    all_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.mp3'):
                all_files.append(os.path.join(root, filename))
    all_files.sort()
    return all_files

def _get_track_number(track_num):
    if not track_num.isdigit():
        track = ''
        for i in track_num:
            if i.isdigit(): 
                track += i
            else: 
                return int(track)
    else:
        return int(track_num)

def rename_media_file(filename, simulated):
    info = mediainfo(filename)
    track = _get_track_number(info['track'])
    artist = info['artist']
    title = info['title']
    name = '{0:02d} - {1} - {2}.mp3'.format(track, artist, title)
    new_filename = os.path.join(os.path.dirname(filename), name)
    if filename != new_filename:
        print('mv "{0}" "{1}"'.format(os.path.basename(filename), name))
        if not simulated:
            shutil.move(filename, new_filename)
    else:
        print('no need to mv "{0}"'.format(os.path.basename(filename)))

def main():
    directory, simulated = _parse_args()
    try:
        for filename in _find_media_files(directory):
            rename_media_file(filename, simulated)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

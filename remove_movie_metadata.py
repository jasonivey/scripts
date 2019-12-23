#!/usr/bin/env python
import argparse
import os
import hashlib
from pymediainfo import MediaInfo
import sqlite3
import shutil
import subprocess
import sys
import traceback

_VERBOSE = False
_EXTENSIONS = ['.webm', '.mpg', '.mp2', '.mpeg',
               '.mpe', '.mpv', '.ogg', '.mp4', 
               '.m4p', '.m4v', '.avi', '.wmv', 
               '.mov', '.qt', '.flv', '.swf', 
               '.avchd']

def _verbose_print(s):
    if _VERBOSE: print(s)

def _is_video_file(file_name):
    extension = os.path.splitext(file_name)[1]
    return extension in _EXTENSIONS

def _find_files(input_dir):
    paths = []
    for root, dirs, files in os.walk(input_dir):
        for file_name in files:
            if _is_video_file(file_name):
                paths.append(os.path.abspath(os.path.join(root, file_name)))
    return paths

def _parse_args():
    parser = argparse.ArgumentParser(description='Given a directory or list of files it will remove the metadata in various video files')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-d', '--dir', default=None, help='specify which directory to find files to remove metadata from')
    parser.add_argument('files', nargs='*', help='specify which files to remove metadata from')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    input_files = []
    if len(args.files) > 0:
        for filename in args.files:
            if not os.path.isfile(filename):
                parser.error('the files specified for metadata removal must exist')
            elif not _is_video_file(filename):
                raise parser.error('the files specified for metadata removal must be a video type file')
            else:
                input_files.append(os.path.abspath(filename))
    
    input_dir = args.dir
    if len(input_files) == 0:
        if not input_dir:
            input_dir = os.getcwd()
        if not os.path.isdir(input_dir):
            raise parser.error('the diriectory specified for searching for files for metadata removal must exist')
        input_files += _find_files(input_dir)

    return input_files

def _get_mediainfo_track(file_name):
    media_info = MediaInfo.parse(file_name)
    for track in media_info.tracks:
        if track.track_type == 'General':
            return track.to_data()
    return None

def _has_metadata(file_name):
    track = _get_mediainfo_track(file_name)
    if not track:
        return False 

    if 'title' in track and len(track['title']) > 0:
        return 'title - {}'.format(track['title']) if _VERBOSE else True
    elif 'movie_name' in track and len(track['movie_name']) > 0:
        return 'movie_name - {}'.format(track['movie_name']) if _VERBOSE else True
    elif 'Season' in track and len(track['Season']) > 0:
        return 'Season - {}'.format(track['Season']) if _VERBOSE else True
    elif 'Part' in track and len(track['Part']) > 0:
        return 'Part - {}'.format(track['Part']) if _VERBOSE else True
    elif 'Performer' in track and len(track['Performer']) > 0:
        return 'Performer - {}'.format(track['Performer']) if _VERBOSE else True
    elif 'Composer' in track and len(track['Composer']) > 0:
        return 'Composer - {}'.format(track['Composer']) if _VERBOSE else True
    elif 'Genre' in track and len(track['Genre']) > 0:
        return 'Genre - {}'.format(track['Genre']) if _VERBOSE else True
    elif 'ContentType' in track and len(track['ContentType']) > 0:
        return 'ContentType - {}'.format(track['ContentType']) if _VERBOSE else True
    elif 'Description' in track and len(track['Description']) > 0:
        return 'Description - {}'.format(track['Description']) if _VERBOSE else True
    elif 'Comment' in track and len(track['Comment']) > 0:
        return 'Comment {}'.format(track['Comment']) if _VERBOSE else True
    else:
        False

def _get_files_with_metadata(file_names):
    files_with_metadata = []
    for i, file_name in enumerate(file_names, start=1):
        _verbose_print("%d: %s" % (i, file_name))
        metadata = _has_metadata(file_name)
        if metadata:
            files_with_metadata.append((file_name, metadata))
    if len(files_with_metadata) > 0:
        _verbose_print('')
    for count, i in enumerate(files_with_metadata, start=1):
        _verbose_print("%d: %s" % (count, i[0]))
        _verbose_print("  %s" % i[1])

    print(files_with_metadata)
    # return just a list of the paths to the files
    return [i[0] for i in files_with_metadata]

def _create_temp_name(file_name):
    basename, ext = os.path.splitext(file_name)
    return '{}.new{}'.format(basename, ext)

def _remove_metadata_from_file(file_name):
    _verbose_print('removing metadata: %s' % file_name)
    new_file_name = _create_temp_name(file_name)
    _verbose_print('metadata free file: %s' % new_file_name)
    command = 'ffmpeg -i "{}" -map_chapters -1 -map_metadata -1 -c:v copy -c:a copy "{}"'.format(file_name, new_file_name)
    _verbose_print('command: %s' % command)
    process = subprocess.Popen(command, shell=True, bufsize=1, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        print('ERROR: while running command %s' % command)
        print('DETAILS:\n%s' % stderrdata.decode('utf-8'))
        return False
    _verbose_print('removed metadata: %s' % new_file_name)
    shutil.move(new_file_name, file_name)
    _verbose_print('moved %s over top of %s' % (new_file_name, file_name))
    return True

def _remove_metadata_from_files(file_names):
    print(file_names)
    for file_name in file_names:
        if not _remove_metadata_from_file(file_name):
            return False
    return True

def main():
    input_files = _parse_args()
    try:
        files_with_metadata = _get_files_with_metadata(input_files)
        return 0  if _remove_metadata_from_files(files_with_metadata) else 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())


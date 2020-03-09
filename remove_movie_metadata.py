#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import hashlib
from itertools import takewhile
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
               '.avchd', '.mkv']

def _verbose_print(s):
    if _VERBOSE: print(s, file=sys.stdout)

def _is_verbose_mode_on():
    return _VERBOSE

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
    parser.add_argument('-r', '--dry-run', action="store_true", help='only perform a dry run to see which files will be affected')
    parser.add_argument('-f', '--force', action="store_true", help='force all the files specified to have metadata removed')
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

    return input_files, args.dry_run, args.force

class MediaMetadataParser:
    def __init__(self, file_name, force):
        self._file_name = file_name
        self._force = force
        self._media_info = MediaInfo.parse(self._file_name)
        self._metadata = None

    def has_metadata(self):
        if not self._media_info:
            print('ERROR: MediaInfo library was unable to parse \'{}\''.format(self._file_name), file=sys.stderr)
            return False

        if self._force:
            _verbose_print('INFO: forcing has_metadata to return \'True\' via --force flag')
            return True

        for track_name in ['General', 'Video', 'Audio']:
            for track in self._media_info.tracks:
                if track.track_type == track_name:
                    track_data = track.to_data()
                    if not track_data:
                        print('ERROR: unable to convert {} properties to a dictionary in media {}'.format(track_name, self._file_name), file=sys.stderr)
                        continue
                    if self._get_metadata(track_data, track_name):
                        return True
        return False

    def _get_metadata(self, track, track_name):
        _verbose_print('INFO: checking \'{}\' track for extraneous metadata'.format(track_name))
        strippable_metadata_keys = set({'title', 'title_name', 'movie', 'movie_name', 'season', 'part', 'performer', \
                                    'composer', 'genre', 'contenttype', 'description', 'comment'})

        track_keys = set(track.keys())
        strippable_metadata_in_track = strippable_metadata_keys & track_keys
        if len(strippable_metadata_in_track) == 0:
            _verbose_print('INFO: did not find any extraneous metadata in the \'{}\' track'.format(track_name))
            return False

        track_key = strippable_metadata_in_track.pop()
        self._metadata = '{}: {}'.format(track_key, track[track_key])
        _verbose_print('INFO: extraneous metadata was found in the \'{}\' track'.format(track_name))
        return True

    @property
    def metadata(self):
        return self._metadata if self._metadata else ''

def _get_files_with_metadata(file_names, force):
    file_names_with_metadata = []
    for i, file_name in enumerate(file_names, start=1):
        _verbose_print('INFO: {:3}: checking for custom metadata {}'.format(i, file_name))
        media_metadata_parser = MediaMetadataParser(file_name, force)
        if media_metadata_parser.has_metadata():
            file_names_with_metadata.append((file_name, media_metadata_parser.metadata))
    if len(file_names_with_metadata) > 0:
        _verbose_print('')
    for i, file_name_with_metadata in enumerate(file_names_with_metadata, start=1):
        file_name = file_name_with_metadata[0]
        metadata = file_name_with_metadata[1]
        _verbose_print('INFO: {:3}: custom metadata found {}'.format(i, file_name))
        _verbose_print('  {}'.format(metadata))

    # return just a list of the paths to the files
    return [file_name_with_metadata[0] for file_name_with_metadata in file_names_with_metadata]

def _create_temp_name(file_name):
    basename, ext = os.path.splitext(file_name)
    return '{}.new{}'.format(basename, ext)

def _clean_up_on_error(file_name):
    _verbose_print('INFO: cleaning up by deleting the destination file if it exists here {}'.format(file_name))
    if not os.path.isfile(file_name):
        _verbose_print('INFO: the destination file was never created so no need to delete {}'.format(file_name))
        return

    _verbose_print('INFO: the destination file exists -- attempting to delete {}'.format(file_name))
    try:
        os.remove(file_name)
        _verbose_print('INFO: successfully deleted the file {}'.format(file_name))
    except OSError as err:
        print('ERROR: OSError exception thrown -- {}'.format(err), file=sys.stderr)
        _verbose_print('ERROR: unable to remove the destination file {}'.format(file_name))

def _remove_metadata_from_file(file_name):
    _verbose_print('INFO: removing metadata from: {}'.format(file_name))
    new_file_name = _create_temp_name(file_name)
    _verbose_print('INFO: destination metadata free file: {}'.format(new_file_name))
    command = 'ffmpeg -i "{}" -map_chapters -1 -map_metadata -1 -c:v copy -c:a copy "{}"'.format(file_name, new_file_name)
    _verbose_print('INFO: command \'{}\''.format(command))
    process = subprocess.Popen(command, shell=True, bufsize=1, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        print('ERROR: while running command \'{}\''.format(command), file=sys.stderr)
        print('DETAILS:', file=sys.stderr)
        print(stderrdata.decode('utf-8'), file=sys.stderr)
        _clean_up_on_error(new_file_name)
        return False
    _verbose_print('INFO: created identical file and removed the metadata: {}'.format(new_file_name))
    shutil.move(new_file_name, file_name)
    _verbose_print('INFO: moved new {} over top of old {}'.format(new_file_name, file_name))
    return True

def _remove_metadata_from_files(file_names, dry_run):
    _verbose_print('INFO: there are {} file(s) which need to have extraneous metadata removed'.format(len(file_names)))
    if dry_run and len(file_names) > 0:
        _verbose_print('INFO: dry run enabled -- NO METADATA BEING REMOVED')
        return True

    file_names_updated = list(takewhile(_remove_metadata_from_file, file_names))
    return len(file_names_updated) == len(file_names)

def main():
    input_files, dry_run, force = _parse_args()
    _verbose_print('args:\n  input files: {}\n  verbose: {}\n  dry run: {}\n  force: {}' \
                   .format('\n               '.join(input_files), _is_verbose_mode_on(), dry_run, force))

    retval = 0
    try:
        file_names = _get_files_with_metadata(input_files, force)
        retval = 0 if _remove_metadata_from_files(file_names, dry_run) else 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        retval = 1
    return retval

if __name__ == '__main__':
    sys.exit(main())


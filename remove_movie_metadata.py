#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120:ft=python

from ansimarkup import AnsiMarkup, parse
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

user_tags = {
    'info'     : parse('<bold><green>'),    # bold green
    'text'      : parse('<bold><white>'),    # bold white
    #'alttext'   : parse('<white>'),          # white
    #'name'      : parse('<bold><cyan>'),     # bold cyan
    #'altname'   : parse('<cyan>'),           # cyan
    'error'     : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

_COUNTER_WIDTH = 2
_VERBOSE = False
_EXTENSIONS = ['.webm', '.mpg', '.mp2', '.mpeg',
               '.mpe', '.mpv', '.ogg', '.mp4',
               '.m4p', '.m4v', '.avi', '.wmv',
               '.mov', '.qt', '.flv', '.swf',
               '.avchd', '.mkv']


def _verbose_print(msg):
    if _VERBOSE: 
        am.ansiprint(f'<info>INFO:</info> <text>{msg}</text>', file=sys.stdout)

def _error_print(msgp, prefix=True):
    if prefix:
        am.ansiprint(f'<error>ERROR: {msg}</error>', file=sys.stderr)
    else:
        am.ansiprint(f'<error>{msg}</error>', file=sys.stderr)

def _title_print(title):
    am.ansiprint(f'<title>{title}</title>')

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

def _get_index_width(input_file_count):
    if input_file_count >= 100:
        # Once it gets to 100 convert the number to a str and then get the length of that
        #  I.E if the number of input files is 5980 this wil give an len('5980') or width
        #  of 4.  This allows output of the indexes from 1-5980 in a fixed column width.
        return len(str(input_file_count))
    # Default to a minimum width of 2
    return 2

class MediaMetadataParser:
    def __init__(self, file_name, force):
        self._file_name = file_name
        self._force = force
        self._media_info = MediaInfo.parse(self._file_name)
        self._metadata = None

    def has_metadata(self):
        if not self._media_info:
            _error_print(f'MediaInfo library was unable to parse \'{self._file_name}\'')
            return False

        TRACK_NAMES = {'General', 'Video', 'Audio'}
        available_tracks = available_tracks = set([track.track_type for track in  self._media_info.tracks])
        missing_tracks = TRACK_NAMES - available_tracks
        if len(missing_tracks) > 0:
            _error_print(f'File \'{self._file_name}\' is missing {", ".join(missing_tracks)} track(s)')
            return False

        if self._force:
            self._metadata = 'Unknown: use of --force flag'
            _verbose_print('forcing has_metadata to return \'True\' via --force flag')
            return True

        for track in self._media_info.tracks:
            if track.track_type not in TRACK_NAMES:
                _verbose_print(f'ignoring track {track.track_type} in {self._file_name}')
                continue
            track_data = track.to_data()
            if not track_data:
                _error_print(f'unable to convert {track_name} properties to a dictionary in media {self._file_name}')
                continue
            if self._get_metadata(track_data, track.track_type):
                return True
        return False

    def _get_metadata(self, track, track_name):
        _verbose_print(f'checking \'{track_name}\' track for extraneous metadata')
        if track_name == 'General':
            strippable_metadata_keys = {'title', 'title_name', 'movie', 'movie_name', 'season', 'part', 'performer', \
                                        'composer', 'genre', 'contenttype', 'description', 'comment'}
        else:
            # Video & Audio Tracks will often have a title or title_name metadata field. This will indicate they type
            #  of video (Sterio, AAC, etc.) or the language of the audio (en, es, de, etc.) both are rather helpful
            strippable_metadata_keys = {'movie', 'movie_name', 'season', 'part', 'performer', \
                                        'composer', 'genre', 'contenttype', 'description', 'comment'}
        track_keys = set(track.keys())
        strippable_metadata_in_track = strippable_metadata_keys & track_keys
        if len(strippable_metadata_in_track) == 0:
            _verbose_print(f'did not find any extraneous metadata in the \'{track_name}\' track')
            return False

        track_key = strippable_metadata_in_track.pop()
        self._metadata = f'{track_key}: {track[track_key]}'
        _verbose_print(f'extraneous metadata was found in the \'{track_name}\' track')
        return True

    @property
    def metadata(self):
        return self._metadata if self._metadata else ''

def get_files_with_metadata(file_names, force):
    index_width = _get_index_width(len(file_names))
    for i, file_name in enumerate(file_names, start=1):
        _verbose_print(f'{i:{index_width}}: checking for custom metadata {file_name}')
        media_metadata_parser = MediaMetadataParser(file_name, force)
        if media_metadata_parser.has_metadata():
            _verbose_print(f'{i:{index_width}}: custom metadata found {file_name}')
            _verbose_print(f'  metadata: {media_metadata_parser.metadata}')
            yield file_name

def _create_temp_name(file_name):
    basename, ext = os.path.splitext(file_name)
    return f'{basename}.new{ext}'

def _clean_up_on_error(file_name):
    _verbose_print(f'cleaning up by deleting the destination file if it exists here {file_name}')
    if not os.path.isfile(file_name):
        _verbose_print(f'the destination file was never created so no need to delete {file_name}')
        return

    _verbose_print(f'the destination file exists -- attempting to delete {file_name}')
    try:
        os.remove(file_name)
        _verbose_print(f'successfully deleted the file {file_name}')
    except OSError as err:
        _error_print(f'OSError exception thrown -- {err}')
        _error_print(f'  unable to remove the destination file {file_name}', prefix=False)

def _remove_metadata_from_file(file_name):
    _verbose_print(f'removing metadata from {file_name}')
    new_file_name = _create_temp_name(file_name)
    _verbose_print(f'temporary metadata free file will be named {new_file_name}')
    command = 'ffmpeg -i "{}" -map_chapters -1 -map_metadata -1 -c:v copy -c:a copy "{}"'.format(file_name, new_file_name)
    _verbose_print(f'command \'{command}\'')
    process = subprocess.Popen(command, shell=True, bufsize=1, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        _error_print(f'while running command \'{command}\'')
        _error_print('DETAILS:', prefix=False)
        _error_print(stderrdata.decode('utf-8'), prefix=False)
        _clean_up_on_error(new_file_name)
        return False
    _verbose_print(f'created {new_file_name} and removed the metadata')
    shutil.move(new_file_name, file_name)
    _verbose_print(f'moved {new_file_name} over top of {file_name}')
    return True

def remove_metadata_from_file(file_name, dry_run):
    if dry_run:
        _verbose_print('dry run enabled -- NO METADATA BEING REMOVED')
        return True
    return _remove_metadata_from_file(file_name)

def main():
    input_files, dry_run, force = _parse_args()
    _verbose_print(f'args:\n' \
                   f'  input files: {", ".join(input_files)}\n' \
                   f'  verbose: {_is_verbose_mode_on()}\n'
                   f'  dry run: {dry_run}\n' \
                   f'  force: {force}')

    retval = 0
    try:
        first = True
        for file_name in get_files_with_metadata(input_files, force):
            if first: first = False
            else: print('')
            if not remove_metadata_from_file(file_name, dry_run):
                retval = 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        retval = 1
    return retval

if __name__ == '__main__':
    sys.exit(main())


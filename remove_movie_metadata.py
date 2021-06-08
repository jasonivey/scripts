#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120:ft=python

from ansimarkup import AnsiMarkup, parse
import argparse
import json
import os
from pymediainfo import MediaInfo
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import traceback

user_tags = {
    'info'   : parse('<bold><cyan>'),
    'text'   : parse('<bold><white>'),
    'error'  : parse('<bold><red>'),
    'status' : parse('<bold><green>'),
}

am = AnsiMarkup(tags=user_tags)

_COUNTER_WIDTH = 2
_VERBOSE = False
_EXTENSIONS = ['.webm', '.mpg', '.mp2', '.mpeg',
               '.mpe', '.mpv', '.ogg', '.mp4',
               '.m4p', '.m4v', '.avi', '.wmv',
               '.mov', '.qt', '.flv', '.swf',
               '.avchd', '.mkv']

def _status_print(msg, newline=False):
    newline_str = '\n' if newline else ''
    am.ansiprint(f'{newline_str}<status>STATUS:</status> <text>{msg}</text>', file=sys.stdout)

def _verbose_print(msg, newline=False):
    newline_str = '\n' if newline else ''
    if _VERBOSE:
        am.ansiprint(f'{newline_str}<info>INFO:</info> <text>{msg}</text>', file=sys.stdout)

def _error_print(msg, prefix=True):
    if prefix:
        am.ansiprint(f'<error>ERROR:</error> <text>{msg}</text>', file=sys.stderr)
    else:
        am.ansiprint(f'<error>{msg}</error>', file=sys.stderr)

def _title_print(title):
    am.ansiprint(f'<title>{title}</title>')

def _is_verbose_mode_on():
    return _VERBOSE

def _call_external_process(command, dry_run):
    args = shlex.split(command)
    try:
        if dry_run:
            _status_print(f'dry-run skipping: \'{command}\'')
        else:
            _verbose_print(f'executing \'{command}\'')
            subprocess.run(args, check=True, encoding='utf-8', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.SubprocessError as err:
        _error_print(f'error executing \'{command}\', {err}')
        return False
    except Exception as err:
        _error_print(f'error executing \'{command}\', {err}')
        return False

def _is_video_file(file_path):
    return file_path.suffix in _EXTENSIONS

def _find_video_files(input_dir):
    if not input_dir or not input_dir.is_dir(): return None
    for child in input_dir.rglob('*'):
        if _is_video_file(child):
            yield child

def _is_valid_directory(dir):
    dir_path = Path(dir)
    if not dir_path.is_dir():
        raise argparse.ArgumentTypeError(f'{dir} is not an existing directory')
    else:
        return dir_path.resolve()

def _is_valid_filename(filename):
    file_path = Path(filename)
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f'{filename} is not an existing file')
    elif not _is_video_file(file_path):
        raise argparse.ArgumentTypeError(f'{filename} is not a video file')
    else:
        return file_path.resolve()

def _parse_args():
    parser = argparse.ArgumentParser(description='Given a directory or list of files it will remove the metadata in various video files')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s 0.0.16')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')

    subparsers = parser.add_subparsers(metavar="{action}", dest='subcommand', required=True, help='commands to show/remove movie metadata')

    show_mediainfo_description = 'this command will use pymetadata to display the movie files stream metadata'
    subparsers.add_parser('show', description=show_mediainfo_description, help='show movie metadata')

    remove_metadata_description = 'this command will create/overwrite movie files using ffmpeg to copy existing streams wihtout existing metadata'
    remove_metadata_parser = subparsers.add_parser('remove', description=remove_metadata_description, help='remove movie metadata')
    remove_metadata_parser.add_argument('-s', '--simulated-run', dest='dry_run', action="store_true", help='identify extraneous metadata but DO NOT remove it')
    remove_metadata_parser.add_argument('-F', '--force', dest='force', action="store_true", help='force all files to be re-written using ffmpeg')

    sources_group = parser.add_mutually_exclusive_group(required=True)
    sources_group.add_argument('-d', '--dir', dest='dirs', type=_is_valid_directory, action='append', help='source directory to locate movie files')
    sources_group.add_argument('-f', '--filename', dest='files', type=_is_valid_filename, action='append', help='explicit paths to movie files')

    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    file_paths = args.files if args.files else []
    if args.dirs:
        for dir in args.dirs:
            file_paths += [file_path for file_path in _find_video_files(dir)]
    dry_run = False if args.subcommand == 'show' else args.dry_run
    force = False if args.subcommand == 'show' else args.force

    return args.subcommand, file_paths, dry_run, force

class MediaMetadataParser:
    # Video & Audio Tracks will often have a title or title_name metadata field. This will indicate the type
    #  of video (Sterio, AAC, etc.) or the language of the audio (en, es, de, etc.) both are rather helpful.
    # For this reason the NonGeneralMetadataFields does not include 'title' or 'title_name' fields where as
    #  the General track does.  Within the General track 'title' or 'title_name' fields there is often
    #  found very whacky information that is best to be stripped.
    GeneralMetadataFields = {'title', 'title_name', 'movie', 'movie_name', 'season', 'part', 'performer', 'composer', 'genre', 'contenttype', 'description', 'comment'}
    NonGeneralMetadataFields = {'movie', 'movie_name', 'season', 'part', 'performer', 'composer', 'genre', 'contenttype', 'description', 'comment'}
    TrackNames = ['General', 'Video', 'Audio']

    def __init__(self, file_path):
        self._file_path = file_path
        self._media_info = None
        self._metadata = {}
        self._json_metadata = None

    def has_metadata(self):
        return self.find_first_of_any_extraneous_metadata()

    def find_all_metadata(self):
        if not self._parse():
            return False
        for track in self._media_info.tracks:
            if not self._is_known_track_type(track.track_type):
                continue
            if track.track_type not in self._metadata:
                self._metadata[track.track_type] = {}
            self._metadata[track.track_type] = track.to_data()
        self._json_metadata = json.dumps(self._metadata, indent=2, sort_keys=True)
        return True

    def find_first_of_any_extraneous_metadata(self):
        if not self._parse():
            return False
        if not self._are_all_expected_tracks_available():
            return False
        for track in self._media_info.tracks:
            if not self._is_known_track_type(track.track_type):
                continue
            track_data = track.to_data()
            if not track_data:
                _error_print(f'unable to convert "{track.track_type}" properties to a dictionary in "{self._file_path}"')
                continue
            if self._get_extraneous_metadata_in_track(track_data, track.track_type):
                return True
        return False

    def _parse(self):
        try:
            self._media_info = MediaInfo.parse(self._file_path)
            return True
        except Exception as ex:
            _error_print('MediaInfo parse raised exception {ex}')
            return False

    def _are_all_expected_tracks_available(self):
        available_tracks = set([track.track_type for track in  self._media_info.tracks])
        missing_tracks = set(MediaMetadataParser.TrackNames) - available_tracks
        if len(missing_tracks) > 0:
            _error_print(f'some of the tracks are not present ({", ".join(missing_tracks)}) in "{self._file_path}"')
        return len(missing_tracks) == 0

    def _is_known_track_type(self, track_type):
        if track_type not in MediaMetadataParser.TrackNames:
            _verbose_print(f'ignoring track \'{track_type}\' in "{self._file_path}"')
        return track_type in MediaMetadataParser.TrackNames

    def _get_fields_in_track_which_contain_metadata(self, track, track_name):
        fields_containing_metadata = set(MediaMetadataParser.GeneralMetadataFields) if track_name == 'General' else MediaMetadataParser.NonGeneralMetadataFields
        track_fields = set(track.keys())
        metadata_fields = fields_containing_metadata & track_fields
        if len(metadata_fields) == 0:
            _verbose_print(f'did not find any metadata in the \'{track_name}\' track')
            return None
        # return the first field (may be many) which is both a member of the set 'fields_containing_metadata' and 'track_fields'
        return metadata_fields.pop()

    def _get_extraneous_metadata_in_track(self, track, track_name):
        _verbose_print(f'checking the \'{track_name}\' track for metadata')
        metadata_field = self._get_fields_in_track_which_contain_metadata(track, track_name)
        if not metadata_field:
            return False
        if track_name not in self._metadata:
            self._metadata[track_name] = {}
        self._metadata[track_name][metadata_field] = track[metadata_field]
        _verbose_print(f'metadata was found in the \'{track_name}\' track')
        return True

    @property
    def metadata(self):
        return self._metadata

    def _get_single_item_metadata(self):
        assert len(self._metadata) == 1
        outter_key_name = list(self._metadata.keys())[0]
        assert isinstance(self._metadata[outter_key_name], dict)
        assert len(self._metadata[outter_key_name]) == 1
        key = list(self._metadata[outter_key_name].keys())[0]
        value = list(self._metadata[outter_key_name].values())[0]
        return f'{outter_key_name}:{key} = {value}'

    def _is_single_item_metadata(self):
        if len(self._metadata) != 1:
            return False
        outter_key_name = list(self._metadata.keys())[0]
        return isinstance(self._metadata[outter_key_name], dict) and len(self._metadata[outter_key_name]) == 1

    def __str__(self):
        if self._is_single_item_metadata():
            return self._get_single_item_metadata()
        else:
            return self._json_metadata if self._json_metadata else ''

def get_files_with_metadata(file_paths, force):
    for file_path in file_paths:
        _status_print(f'checking: "{file_path}"', True)
        if force:
            _status_print(f'forced: "{file_path}"')
            yield file_path
        else:
            media_metadata_parser = MediaMetadataParser(file_path)
            if not media_metadata_parser.has_metadata():
                _status_print(f'NO extra metadata: "{file_path}"')
                continue
            _status_print(f'HAS extra metadata: "{file_path}"')
            _verbose_print(f'  metadata: {media_metadata_parser}')
            yield file_path

def _create_temp_path(file_path):
    updated_extension = f'.new{file_path.suffix}'
    return file_path.with_suffix(updated_extension)

def _clean_up_on_error(file_path):
    _verbose_print(f'cleaning up by deleting "{file_path}"')
    if not os.path.isfile(file_path):
        _verbose_print(f'destination file was not created, "{file_path}"')
        return
    _verbose_print(f'deleting "{file_path}"')
    try:
        os.remove(file_path)
        _verbose_print(f'successfully deleted "{file_path}"')
    except OSError as err:
        _error_print(f'OSError exception thrown -- {err}')
        _error_print(f'  unable to remove "{file_path}"', prefix=False)

def _remove_metadata_from_file(file_path, dry_run):
    _verbose_print(f'removing metadata: "{file_path}"')
    new_file_path = _create_temp_path(file_path)
    _verbose_print(f'temporary file: "{new_file_path}"')
    command = f'ffmpeg -i "{file_path}" -map_chapters -1 -map_metadata -1 -c:v copy -c:a copy "{new_file_path}"'
    if not _call_external_process(command, dry_run):
        _clean_up_on_error(new_file_path)
        return False
    _verbose_print(f'created "{new_file_path}" and removed the metadata')
    if not dry_run:
        shutil.move(new_file_path, file_path)
    _verbose_print(f'moved "{new_file_path}" over top of "{file_path}"')
    _status_print(f'removed metadata: "{file_path}"')
    return True

def show_metadata_from_files(file_paths):
    for file_path in file_paths:
        _verbose_print(f'gathing metadata: "{file_path}"')
        media_metadata_parser = MediaMetadataParser(file_path)
        if not media_metadata_parser.find_all_metadata():
            continue
        metadata_str = str(media_metadata_parser).replace('\n', '\n' + ' ' * 7)
        _status_print(f'metadata: "{file_path}"')
        _status_print(f'\n{" ":{7}}{metadata_str}')

def remove_metadata_from_files(file_paths, force, dry_run):
    retval = True
    first = True
    for file_path in get_files_with_metadata(file_paths, force):
        if first: first = False
        if not _remove_metadata_from_file(file_path, dry_run):
            retval = False
    return retval

def main():
    command_name, file_paths, dry_run, force = _parse_args()
    movie_files_str = ('\n' + ' ' * 15).join(map(str, file_paths))
    _verbose_print(f'args:\n' \
                   f'  sub-command: {command_name}\n'
                   f'  movie files: {movie_files_str}\n' \
                   f'  verbose: {_is_verbose_mode_on()}\n'
                   f'  dry run: {dry_run}\n' \
                   f'  force: {force}')
    retval = 0
    try:
        if command_name == 'show':
            if not show_metadata_from_files(file_paths):
                retval = 1
        elif command_name == 'remove':
            if not remove_metadata_from_files(file_paths, force, dry_run):
               retval = 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        retval = 1
    return retval

if __name__ == '__main__':
    sys.exit(main())


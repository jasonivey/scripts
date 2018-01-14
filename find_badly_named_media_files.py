#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import os
import sys
import re
import traceback

def is_directory(value):
    if os.path.isdir(value):
        return os.path.normpath(value)
    raise argparse.ArgumentTypeError('argument must be a valid directory')

def handle_all_destinations(audio_dir, movies_dir, tv_dir):
    if not audio_dir and not movies_dir and not tv_dir:
        msg = '%s: error: argument \'-a\', \'--audio\', \'-m\', \'--movies\', or \'-t\', \'--television\' must be specified' % sys.argv[0]
        print(msg)
        sys.exit(1)

def _parse_args():
    description = 'Parse Plex media files to ensure correct naming'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('-a', '--audio', metavar='<dir>', type=is_directory, help='directory where audio files are stored')
    parser.add_argument('-m', '--movies', metavar='<dir>', type=is_directory, help='directory where movies files are stored')
    parser.add_argument('-t', '--television', metavar='<dir>', type=is_directory, help='directory where television files are stored')
    parser.add_argument('-f', '--find-prerelease', default=False, action='store_true', help='Find files which are pre-release (i.e. screeners, cams, etc.)')
    args = parser.parse_args()
    if args.verbose > 0:
        print('Arguments:\n  verbose: {}\n  audio: {}\n  movies: {}\n  television: {}\n  find pre-release: {}'.format(
             args.verbose, args.audio, args.movies, args.television, args.find_prerelease))
    handle_all_destinations(args.audio, args.movies, args.television)
    return args.verbose, args.audio, args.movies, args.television, args.find_prerelease

def _walk_directory(directory):
    entries = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            entries.append(os.path.join(root, filename))
    return entries

def _split_file_extensions(filename):
    index = filename.rfind('.')
    if index == -1:
        return filename, '.'
    return filename[:index], filename[index:]

VALID_MEDIA_EXTENSIONS = ['.mkv', '.mp4', '.m4v', '.avi', '.mp3', '.srt', '.idx', '.sub', '.smi']
# todo: why?
MEDIA_EXTENSIONS = ['.mkv', '.mp4', '.m4v', '.avi', '.mp3']
INVALID_OS_FILES = ['.DS_Store', '._.DS_Store']
INVALID_AUDIO_FILES = ['.directory', '.folder.png', 'folder.jpg']

def _is_system_file(filename, audio_dir=False):
    name = os.path.split(filename)[1]
    if name in INVALID_OS_FILES:
        return True
    if audio_dir and name in INVALID_AUDIO_FILES:
        return True
    if name.startswith('._'):
        return True
    return False

def _scan_television_directory(directory, verbose):
    REGEX = r'(?:(?P<name>.*)\s-\s)?s(?P<season>\d{2})e(?P<episode>\d{2})(?:\s-\s(?P<subname>.*))?'
    errors_found = 0
    bad_extensions = []
    for fullname in _walk_directory(directory):
        basename, ext = _split_file_extensions(fullname)
        if _is_system_file(fullname):
            if verbose > 1:
                print('Found invalid name: %s' % fullname)
        elif ext not in VALID_MEDIA_EXTENSIONS and ext not in bad_extensions:
            bad_extensions.append(ext)
            print('Found unknown extension: %s (%s)' % (ext, fullname))
            errors_found += 1
        elif not os.path.isdir(fullname):
            match = re.match(REGEX, os.path.split(basename)[1])
            if not match:
                print('Found unknown file naming convention: %s' % fullname) 
                errors_found += 1
            else:
                # Create JSON here
                #episodes[
    return errors_found

def _scan_movie_directory(directory, find_prerelease, verbose):
    REGEX = r'(?P<name>[^)]+)\((?P<year>\d{4})\)(?:\s-\s(?P<type>.*))?' 
    errors_found = 0
    bad_extensions = []
    for fullname in _walk_directory(directory):
        basename, ext = _split_file_extensions(fullname)
        if _is_system_file(fullname):
            if verbose > 1:
                print('Found invalid name: %s' % fullname)
        elif ext not in VALID_MEDIA_EXTENSIONS and ext not in bad_extensions:
            bad_extensions.append(ext)
            print('Found unknown extension: %s (%s)' % (ext, fullname))
            errors_found += 1
        elif not os.path.isdir(fullname):
            match = re.match(REGEX, os.path.split(basename)[1])
            if not match:
                print('Found unknown file naming convention: %s' % fullname) 
                errors_found += 1
            elif match.group('type') and find_prerelease:
                print('Pre release: %s' % fullname)
    return errors_found

def _scan_music_directory(directory, verbose):
    REGEX = r'(?P<artist>[^/]+)/(?P<album>[^/]+)/(?P<name>.*)'
    

def _print_results(error_count, name):
    print('%s scan errors: %d' % (name, error_count))

def main():
    verbose, audio_dir, movies_dir, tv_dir, find_prerelease = _parse_args()

    try:
        if tv_dir:
            _print_results(_scan_television_directory(tv_dir, verbose), 'TV')
        if movies_dir:
            _print_results(_scan_movie_directory(movies_dir, find_prerelease, verbose), 'movie')
        if audio_dir:
            _print_results(_scan_movie_directory(audio_dir, verbose), 'music')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

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
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='display extra debugging information')
    parser.add_argument('-a', '--audio', metavar='<dir>', type=is_directory, help='directory where audio files are stored')
    parser.add_argument('-m', '--movies', metavar='<dir>', type=is_directory, help='directory where movies files are stored')
    parser.add_argument('-t', '--television', metavar='<dir>', type=is_directory, help='directory where television files are stored')
    parser.add_argument('-f', '--find-prerelease', default=False, action='store_true', help='Find files which are pre-release (i.e. screeners, cams, etc.)')
    args = parser.parse_args()
    print('verbose: {}\naudio: {}\nmovies: {}, television: {}\nfind pre-release: {}'.format(
        args.verbose, args.audio, args.movies, args.television, args.find_prerelease))
    handle_all_destinations(args.audio, args.movies, args.television)
    return args.verbose, args.audio, args.movies, args.television, args.find_prerelease

def _split_file_extensions(filename):
    index = filename.rfind('.')
    if index == -1:
        return filename
    return filename[:index - 1], filename[index:]

VALID_MEDIA_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.srt']
INVALID_OS_FILES = ['.DS_Store', '._.DS_Store']

def _scan_television_directory(tv_dir, find_prerelease, verbose):
    bad_extensions = []
    for root, dirs, files in os.walk(tv_dir):
        for filename in files:
            if filename in INVALID_OS_FILES or (filename.startswith('._') and filename[2:] in files):
                continue
            basename, ext = _split_file_extensions(filename)
            if ext not in VALID_MEDIA_EXTENSIONS and ext not in bad_extensions:
                bad_extensions.append(ext)
                print('Found unknown extension: %s' % ext)
            match = re.match(r'(?P<name>.*)\s-\ss(?P<season>\d+)e(?P<episode>\d+)', basename)
            if not match:
                print('basename: %s' % basename)
                print('Found unknown file naming convention: %s' % os.path.join(root, filename))
            else:
                # Keep track of the season numbering, episode numbering and the gaps
                pass

def _find_media_files(verbose, audio_dir, movies_dir, tv_dir, find_prerelease):
    return None

def main():
    verbose, audio_dir, movies_dir, tv_dir, find_prerelease = _parse_args()

    try:
        if tv_dir:
            _scan_television_directory(tv_dir, find_prerelease, verbose)
        _find_media_files(verbose, audio_dir, movies_dir, tv_dir, find_prerelease)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

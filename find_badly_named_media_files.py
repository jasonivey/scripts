#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import json
import os
import sys
import re
import traceback

def enum(**enums):
    return type('Enum', (), enums)

MediaType = enum(MOVIES=0, TV=1, AUDIO=2)

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

class Subtitle(object):
    def __init__(self, path, name, year, release_type):
        _path = path
        _name = name
        _year = year
        _release_type = release_type

class Movie(object):
    def __init__(self, path, name, year, release_type):
        self.__path = path
        self.__name = name
        self.__year = year
        self.__release_type = release_type
        self.__subtitles = []

    def AddSubtitle(self, subtitle):
        self.__subtitles.append(subtitle)


class TelevisionShow(object):
    def __init__(self, path, name):
        self.__path = path
        self.__name = name
        self.__seasons = {}

    @property
    def seasons(self):
        return self.__seasons

    def add_season(self, path, name):
        if name not in self.__seasons:
            self.__seasons[name] = TelevisionSeason(path, name)
        else:
            ass

class TelevisionSeason(object):
    def __init__(self, path, name):
        self.__path = path
        self.__name = name
        self.__episodes = {}

class TelevisionEpisode(object):
    def __init__(self, path, name, season, episode, subname):
        self.__path = path
        self.__name = name
        self.__season = season
        self.__episode = episode
        self.__subname = subname

class AudioArtist(object):
    def __init__(self, path, name):
        self.__path = path
        self.__name = name

class AudioAlbum(object):
    def __init__(self, path, name):
        self.__path = path
        self.__name = name

class AudioSong(object):
    def __init__(self, path, name):
        self.__path = path
        self.__name = name


def _walk_directory(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            yield os.path.join(root, filename)

def _split_file_extension(filename):
    index = filename.rfind('.')
    if index == -1:
        return filename, '.'
    return filename[:index], filename[index:]

VALID_VIDEO_EXTENSIONS = ['.mkv', '.mp4', '.m4v', '.avi', '.srt', '.idx', '.sub', '.smi']
VALID_SUBTITLE_EXTENSIONS = ['.srt', '.idx', '.sub', '.smi']
VALID_AUDIO_EXTENSIONS = ['.mp3', '.wma', '.ogg', '.m4a', '.m4b']
INVALID_OS_FILES = ['.DS_Store', '._.DS_Store']
INVALID_AUDIO_FILES = ['.directory', '.folder.png', 'folder.jpg', 'Folder.jpg']

def _is_system_file(filename):
    name = os.path.split(filename)[1]
    if name in INVALID_OS_FILES:
        return True
    if name.startswith('._'):
        return True
    return False

def _is_audio_meta_file(filename):
    name = os.path.split(filename)[1]
    basename, ext = _split_file_extension(name)
    return name in INVALID_AUDIO_FILES

def _parse_tv_data(match, filename, tv_data, shows):
    #regex = r'(?P<show>[^/]+)/(?P<season>[^/]+|Specials)/(?:(?P<name>.*)\s-\s)?s(?P<season_num>\d{2})e(?P<episode_num>\d{2})(?:\s-\s(?P<subname>.*))?'
    show = match.group('show')
    season = match.group('season')
    name = match.group('name')
    season_num = int(match.group('season_num'))
    episode_num = int(match.group('episode_num'))
    subname = '' if not match.group('subname') else match.group('subname')
    data = {}
    data['name'] = name
    data['season'] = season_num
    data['episode'] = episode_num
    data['subname'] = subname
    data['path'] = filename
    if show not in shows:
        shows[show] = TelevisionShow(filename)
    if season not in shows[show].seasons:
        pass
    if show not in tv_data:
        tv_data[show] = {}
    if season not in tv_data[show]:
        tv_data[show][season] = []
    tv_data[show][season].append(data)
    return tv_data

def _parse_movie_data(match, filename):
    #regex = r'(?P<name>[^)]+)\((?P<year>\d{4})\)(?:\s-\s(?P<type>.*))?'
    name = match.group('name')
    year = int(match.group('year'))
    release_type = '' if not match.group('type') else match.group('type')
    data = {}
    data['name'] = name
    data['year'] = year
    data['release_type'] = release_type
    return filename, data

def _parse_audio_data(match, filename):
    data = {}
    data['artist'] = match.group('artist')
    data['album'] = match.group('album')
    data['name'] = match.group('name')
    data['type'] = match.group('ext')
    return filename, data

def _is_valid_file_type(filename, media_type):
    if _is_system_file(filename):
        return False
    _, ext = _split_file_extension(filename)
    if media_type == MediaType.AUDIO:
        if _is_audio_meta_file(filename):
            return False
        if ext not in VALID_AUDIO_EXTENSIONS:
            return False
    else:
        if ext not in VALID_VIDEO_EXTENSIONS and ext not in VALID_SUBTITLE_EXTENSIONS:
            return False

    return True

# TODO: TV and Music both need consolidation.  No entry for each file at the highest level
# TODO: subtitle files should be a property of the MOVIE/TV
def _scan_media_directory_impl(directory, regex, media_type, verbose, find_prerelease=False):
    shows = {}
    json_data = {}
    errors_found = 0
    bad_extensions = []
    for fullname in _walk_directory(directory):
        if not _is_valid_file_type(fullname, media_type):
            if verbose > 1:
                print('Found invalid name: %s' % fullname)
            continue

        if os.path.isdir(fullname):
            continue

        relative_name = fullname[len(directory) + 1:]
        match = re.match(regex, relative_name)
        if not match:
            print('Found unknown file naming convention: %s' % fullname)
            errors_found += 1
            continue

        if media_type == MediaType.TV:
            _parse_tv_data(match, relative_name, json_data, shows)
        elif media_type == MediaType.MOVIES:
            key, value = _parse_movie_data(match, relative_name)
            if key in json_data:
                print('ERROR: already processed %s' % key)
                errors_found += 1
                continue
            json_data[key] = value
        else:
            assert media_type == MediaType.AUDIO
            key, value = _parse_audio_data(match, relative_name)
            if key in json_data:
                print('ERROR: already processed %s' % key)
                errors_found += 1
                continue
            json_data[key] = value

    return errors_found, json_data, shows

def _scan_media_directory(directory, media_type, verbose, find_prerelease=False):
    if media_type == MediaType.TV:
        regex = r'(?P<show>[^/]+)/(?P<season>[^/]+|Specials)/(?:(?P<name>.*)\s-\s)?s(?P<season_num>\d{2})e(?P<episode_num>\d{2})(?:\s-\s(?P<subname>.*))?'
        #regex = r'(?:(?P<name>.*)\s-\s)?s(?P<season>\d{2})e(?P<episode>\d{2})(?:\s-\s(?P<subname>.*))?'
        return _scan_media_directory_impl(directory, regex, media_type, verbose, find_prerelease)
    elif media_type == MediaType.MOVIES:
        regex = r'(?P<name>[^)]+)\((?P<year>\d{4})\)(?:\s-\s(?P<type>.*))?'
        return _scan_media_directory_impl(directory, regex, media_type, verbose, find_prerelease)
    else:
        assert media_type == MediaType.AUDIO
        regex = r'(?P<artist>[^/]+)/(?P<album>[^/]+)/(?P<name>[^.]+)\.(?P<ext>.*)'
        return _scan_media_directory_impl(directory, regex, media_type, verbose, find_prerelease)

def _print_results(error_count, name):
    print('%s scan errors: %d' % (name, error_count))

def main():
    verbose, audio_dir, movies_dir, tv_dir, find_prerelease = _parse_args()

    try:
        media = {}
        if tv_dir:
            errors, tv, shows = _scan_media_directory(tv_dir, MediaType.TV, verbose)
            _print_results(errors, 'TV')
            media['television'] = tv
        if movies_dir:
            errors, movies, _ = _scan_media_directory(movies_dir, MediaType.MOVIES, verbose, find_prerelease)
            _print_results(errors, 'movie')
            media['movies'] = movies
        if audio_dir:
            errors, audio, _ = _scan_media_directory(audio_dir, MediaType.AUDIO, verbose)
            _print_results(errors, 'audio')
            media['audio'] = audio
        with open('/tmp/media.json', 'w') as media_file:
            json.dump(media, media_file, indent=2, separators=(',', ': '), sort_keys=True)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

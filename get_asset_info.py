#!/usr/bin/env python

import json
import urllib.request, urllib.error, urllib.parse
import os
import sys
import argparse
import traceback

def _parse_command_line():
    parser = argparse.ArgumentParser(description='Retrieves all the information about an asset')
    parser.add_argument('asset_id', metavar='<asset id>', help='asset id to retrieve information')
    args = parser.parse_args()
    return args.asset_id

def _parse_asset_id(asset_id):
    input_str = urllib.request.urlopen('http://bbtv.qa.movetv.com/cms/publish3/asset/info/{0}.json'.format(asset_id)).read()
    values = json.loads(input_str)
    if 'title' in values:
        print('title: {0}'.format(values['title']))
    if 'metadata' in values:
        metadata = values['metadata']
        if 'description' in metadata:
            print('description: {0}'.format(metadata['description']))
        if 'episode_title' in metadata:
            print('episode: {0}'.format(metadata['episode_title']))
        if 'episode_season' in metadata:
            print('season: {0}'.format(metadata['episode_season']))
        if 'episode_number' in metadata:
            print('number: {0}'.format(metadata['episode_number']))
        if 'tv_rating' in metadata:
            print('rating: {0}'.format(metadata['tv_rating']))
        if 'cast' in metadata:
            cast_str = ''
            for cast in metadata['cast']:
                cast_str += cast + ', '
            print('cast: {0}'.format(cast_str.rstrip(', ')))
        if 'genre' in metadata:
            genre_str = ''
            for genre in metadata['genre']:
                genre_str += genre + ', '
            print('genre: {0}'.format(genre_str.rstrip(', ')))

def main():
    asset_id = _parse_command_line()

    try:
        _parse_asset_id(asset_id)
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
from __future__ import print_function
import json
import urllib2
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
    input_str = urllib2.urlopen('http://bbtv.qa.movetv.com/cms/publish3/asset/info/{0}.json'.format(asset_id)).read()
    values = json.loads(input_str)
    if values.has_key('title'):
        print('title: {0}'.format(values['title']))
    if values.has_key('metadata'):
        metadata = values['metadata']
        if metadata.has_key('description'):
            print('description: {0}'.format(metadata['description']))
        if metadata.has_key('episode_title'):
            print('episode: {0}'.format(metadata['episode_title']))
        if metadata.has_key('episode_season'):
            print('season: {0}'.format(metadata['episode_season']))
        if metadata.has_key('episode_number'):
            print('number: {0}'.format(metadata['episode_number']))
        if metadata.has_key('tv_rating'):
            print('rating: {0}'.format(metadata['tv_rating']))
        if metadata.has_key('cast'):
            cast_str = ''
            for cast in metadata['cast']:
                cast_str += cast + ', '
            print('cast: {0}'.format(cast_str.rstrip(', ')))
        if metadata.has_key('genre'):
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

#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120:ft=python

import argparse
import os
from pymediainfo import MediaInfo
from pathlib import Path
import sys
import traceback


def _parse_args():
    parser = argparse.ArgumentParser(description='Parse input video files for resolution')
    parser.add_argument('paths', metavar='PATH', type=Path, nargs='+', help='file names for video files')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    args = parser.parse_args()
    print(args)
    return args.verbose, args.paths


def get_video_resolution(path, verbose):
    if not path.is_file():
        print(f'ERROR: the path is not a regular file or symlink pointing to a file "{path}"')
        return None
    path = path.resolve(strict=True)
    media_info = MediaInfo.parse(str(path))
    for track in media_info.tracks:
        if track.track_type == 'Video':
            return (track.width, track.height)
    print(f'ERROR: unable to find "video" track in "{path}"')
    return None


def main():
    verbose, video_paths = _parse_args()
    paths_str = ", ".join([str(path) for path in video_paths])
    print(f'args: verbose: {verbose}, video files: [{paths_str}]')
    try:
        for path in video_paths:
            resolution = get_video_resolution(path, verbose)
            if resolution:
                print(f'{path}: {resolution[0]}x{resolution[1]}')
            else:
                print(f'{path}: <resolution unknown>')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())


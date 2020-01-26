#!/usr/bin/env python

import argparse
import os
import shutil
import sys


def IsAnAudioFile(fullpath):
    audio_extensions = \
    ['.aa', '.aa3', '.acd', '.acd-zip', '.acm', '.afc', '.aif', '.als', '.amr',
     '.amxd', '.at3', '.caf', '.cda', '.cpr', '.dcf', '.dmsa', '.dmse', '.dss',
     '.emp', '.emx', '.flac', '.gpx', '.iff', '.kpl', '.m3u', '.m3u8', '.m4a',
     '.m4b', '.m4r', '.mid', '.midi', '.mod', '.mp3', '.mpa', '.nra', '.ogg',
     '.omf', '.pcast', '.pls', '.ptf', '.ra', '.ram', '.rns', '.rx2', '.seq',
     '.sib', '.snd', '.vpm', '.wav', '.wma', ]
    
    basename, extension = os.path.splitext(fullpath)
    return extension and len(extension) > 0 and extension in audio_extensions


def IsValidDestinationDirectory(dir):
    if not os.path.isdir(dir):
        if os.path.isdir(os.path.dirname(dir)):
            return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
        else:
            raise argparse.ArgumentTypeError('%s does not exist, nor does its parent' % dir)
    else:
        if len(os.listdir(dir)) == 0:
            return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
        else:
            raise argparse.ArgumentTypeError('%s exists but is not empty' % dir)


def IsValidSourceDirectory(dir):
    if os.path.isdir(dir):
        return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
    else:
        raise argparse.ArgumentTypeError('%s does not exist' % dir)


def ParseArgs():
    desc = 'Copy an entire directory heirarchy using 0 KB files'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('source_directory', metavar='<source directory>', type=IsValidSourceDirectory, default=os.getcwd(), nargs='?')
    parser.add_argument('destination_directory', metavar='<destination directory>', type=IsValidDestinationDirectory)
    args = parser.parse_args()
    return args.source_directory, args.destination_directory


if __name__ == '__main__':
    src_dir, dst_dir = ParseArgs()
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            source = os.path.join(root, file)
            destination = os.path.join(dst_dir, source[len(src_dir) + 1:])
            if not os.path.isdir(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            if IsAnAudioFile(destination):
                with open(destination, 'w') as file:
                    pass                    # Create a 0 KB file
            else:
                shutil.copy2(source, destination)
            print(destination)

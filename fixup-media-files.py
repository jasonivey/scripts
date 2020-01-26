import argparse
import json
import os
from pydub.utils import mediainfo
import sys
import traceback

def _is_directory(directory):
    if not os.path.isdir(directory):
        msg = "{0} is not a valid directory".format(directory)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(directory))

def _parse_args():
    description = 'scan and analyze media files'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--directory', metavar='<DIRECTORY>', required=True, type=_is_directory, help='directory to scan for media')
    parser.add_argument('-f', '--filename', metavar='<FILENAME>', required=True, type=str, help='file to backup file names into')
    sub_parsers = parser.add_subparsers(help='commands', dest='command')
    unknown_files = sub_parsers.add_parser('find-unknown-files', help='identify all unknown files within the repository')

    args = parser.parse_args()
    find_unknown_files = args.command == 'find-unknown-files'
    return args.directory, args.filename, find_unknown_files

def _is_media_file(filename):
    return filename.endswith('.mp3') or \
           filename.endswith('.wav') or \
           filename.endswith('.ogg') or \
           filename.endswith('.wma') or \
           filename.endswith('.m4b') or \
           filename.endswith('.m4a')

def _is_ignorable_file(filename):
    return filename.endswith('.DS_Store') or \
           filename.endswith('.directory') or \
           filename.endswith('.folder.png') or \
           filename.endswith('.folder.jpg') or \
           filename.lower().endswith('folder.jpg')

_BIT_RATES = {}
def _process_directory(root, files):
    media_found = False
    for filename in files:
        #if media_found: break
        if _is_media_file(filename):
            media_found = True
            pathname = os.path.join(root, filename)
            info = mediainfo(pathname)
            bit_rate = int(float(info['bit_rate']) / 1000)
            global _BIT_RATES
            if root in _BIT_RATES:
                if _BIT_RATES[root] != bit_rate:
                    print(('ERROR: %s has two different bitrates %d and %d' % (root, _BIT_RATES[root], bit_rate)))
            else:
                _BIT_RATES[root] = bit_rate
                print(('%s bitrate: %d kbps' % (root, bit_rate)))
        elif not _is_ignorable_file(filename):
            print(('unknown: %s' % os.path.join(root, filename)))

def _find_unknown_files(files):
    for filename in files:
        if not _is_media_file(filename):
            print(('  Unknown file: %s' % filename))

def _find_all_files_impl(directory):
    all_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not _is_ignorable_file(filename):
                all_files.append(os.path.join(root, filename))
    all_files.sort()
    return all_files

def _find_all_files(directory, filename):
    all_files = []
    if os.path.isfile(filename):
        print(('INFO: reading file names from %s' % filename))
        with open(filename, 'r') as file:
            data = json.loads(file.read())
            for name in data['files']:
                all_files.append(name)
    else:
        print(('INFO: reading file names from parsing directory %s' % directory))
        all_files = _find_all_files_impl(directory)
        with open(filename, 'w') as file:
            data = {'files': all_files}
            file.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    return all_files

def _main():
    directory, filename, find_unknown_files = _parse_args()
    try:
        files = _find_all_files(directory, filename)
        if find_unknown_files:
            _find_unknown_files(files)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(_main())

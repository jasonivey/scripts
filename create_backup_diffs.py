#!/usr/bin/env python

import os
import sys
import argparse
import subprocess
import time
import traceback

import dump_dir

def _parse_command_line():
    parser = argparse.ArgumentParser(description='Enumerates all files in a directory (with MD5\'s).')
    chksum_group = parser.add_mutually_exclusive_group(required=False)
    chksum_group.add_argument('-c', '--crc32', dest='chksum', action='store_true', help='enables md5 chksum')
    chksum_group.add_argument('-m', '--md5', dest='md5', action='store_true', help='enables md5 chksum')
    parser.add_argument('-n', '--no-timestamp', dest='no_timestamp', action='store_true', help='disable timestamp output')
    parser.add_argument('-d', '--destination-volume', dest='destination', required=True, type=_directory_exists, help='destination volume')
    parser.add_argument('-s', '--source-volume', dest='source', required=True, type=_directory_exists, help='source volume')
    parser.add_argument('output_dir', type=_directory_exists, metavar='<output dir>', help='directory to output results')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='enable verbose output')
    args = parser.parse_args()

    crc32 = args.crc32
    md5 = args.md5
    timestamp = not args.no_timestamp
    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.destination)
    output_directory = args.output_dir
    
    return crc32, md5, timestamp, source, destination, output_directory, args.verbose

def main():
    crc32, md5, timestamp, source, destination, output_directory, verbose = _parse_command_line()

    try:
        start = time.time()
        for entry_name in os.listdir(source):
            if entry_name.lower() in ['downloads', 'music', 'movies']:
                with open(os.path.join(output_directory, 'source-{1}.txt'.format(entry_name)), 'w') as logfile:
                    dump_dir.dump_dir(cur_dir, logfile, crc32=crc32, md5=md5, timestamp=timestamp, verbose=verbose)
        for entry_name in os.listdir(destination):
            if entry_name.lower() in ['downloads', 'music', 'movies']:
                with open(os.path.join(output_directory, 'destination-{1}.txt'.format(entry_name)), 'w') as logfile:
                    dump_dir.dump_dir(cur_dir, logfile, crc32=crc32, md5=md5, timestamp=timestamp, verbose=verbose)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    finally:
        print("Elapsed Time: {0}".format(time.time() - start))
        return 0

if __name__ == '__main__':
    sys.exit(main())


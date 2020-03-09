#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import hashlib
import os
import stat
import sys
import traceback
from functools import reduce


def _sum_sha1_file(fobj, size):
    hashobj = hashlib.sha1()
    while True:
        data = fobj.read(size)
        if not data:
            break
        hashobj.update(data)
    return hashobj.hexdigest()

def get_sha1_hash(filename):
    size = min(os.stat(filename)[stat.ST_SIZE], 16 * 1048576)
    with open(filename, 'rb') as fobj:
        return _sum_sha1_file(fobj, size)

def _find_duplicates_impl(path, verbose):
    hashes = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            try:
                full_path = os.path.realpath(full_path)
                sha1sum = get_sha1_hash(full_path)
            except OSError as err:
                print('OS ERROR: {0}'.format(err), file=sys.stderr)
                continue

            if sha1sum in hashes:
                hashes[sha1sum].append(full_path)
            else:
                hashes[sha1sum] = []
                hashes[sha1sum].append(full_path)

    # this one seems to work??? except it adds one???
    # duplicates = reduce(lambda x, y: x + y[1:], hashes.values())

    duplicates = []
    for filenames in hashes.values():
        assert filenames 
        for filename in filenames[1:]:
            duplicates.append(filename)
    return duplicates

def _parse_args():
    parser = argparse.ArgumentParser(description='Remove all duplicate files from a directory or directory tree')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-d', '--dry-run', action="store_true", help='run the script without deleting anything')
    parser.add_argument('dirs', nargs='+', action='append', help='specifiy the directories to query')
    args = parser.parse_args()

    dirs = reduce(lambda x, y: x + y, args.dirs)
    print('INFO: args:\n  verbose: {}\n  dry run: {}\n  dirs: {}'.format(args.verbose, args.dry_run, dirs))
    return args.verbose, args.dry_run, dirs 

def main():
    verbose, dry_run, dirs = _parse_args()
    try:
        for dir in dirs:
            print('Duplicates in {}:'.format(dir))
            duplicates = _find_duplicates_impl(dir, verbose)
            for i, duplicate in enumerate(duplicates, 1):
                print('{}  {}'.format(i, duplicate))
            print('')
            if not dry_run:
                print('Deleting duplicates in {}:'.format(dir))
                for duplicate in duplicates:
                    #os.remove(duplicate)
                    print('  deleted {}'.format(duplicate))
                print('')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())

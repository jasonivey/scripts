#!/usr/bin/env python

import argparse
import binascii
from collections import defaultdict
import os
import sys

import hash_utils

print( sys.version)

def _display_progress(i):
    print('.', end='' if 0 <= i < 80 else '\n')
    return 0 if i > 0 and (i % 80) == 0 else i + 1
    
def _clear_progress(newline=True):
    print('', end='\n' if newline else '')
    return 0

#class FileHasher(object):
#    def __init__(self, filename):
#        self.filename = filename
#        self.hash = _hashsum(filename, True)
#    
#    def __str__(self):
#        return '{0} - {1}'.format(self.filename, self.hash)
#
#    def __cmp__(self, other):
#        return cmp(self.hash, other.hash)
#
#    def __eq__(self, other):
#        return self.hash == other.hash

class DuplicateFinder(object):
    def __init__(self, match, unique, src_dir, dst_dir):
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.src_files = defaultdict(list)
        self.dst_files = defaultdict(list) if dst_dir else None
        self.matches = defaultdict(list) if match else None
        self.uniques = [] if unique else None

    def hash_files(self):
        i = _clear_progress(False)
        print('Collecting source files in {0}...'.format(self.src_dir))
        for root, dirs, files in os.walk(self.src_dir):
            for filename in files:
                hash = hash_utils.md5sum_shell(os.path.join(root, filename))
                self.src_files[hash].append(os.path.join(root, filename))
                i = _display_progress(i)

        if self.dst_dir == None:
            return
        
        i = _clear_progress()
        print('Collecting destination files in {0}...'.format(self.dst_dir))
        for root, dirs, files in os.walk(self.dst_dir):
            for filename in files:
                hash = hash_utils.md5sum_shell(os.path.join(root, filename))
                self.dst_files[hash].append(os.path.join(root, filename))
                i = _display_progress(i)

        _clear_progress()

    @staticmethod
    def _find_matches_template(src_files, dst_files):
        matches = defaultdict(list)
        for src_hash, src_filenames in src_files.items():
            duplicate_files = src_filenames
            if dst_files and src_hash in dst_files:
                duplicate_files += dst_files[src_hash]
            for filename in duplicate_files:
                if filename not in matches[src_hash]:
                    matches[src_hash].append(filename)
        return matches

    def _find_matches(self):
        print('Finding duplicate files...')
        
        # Check for duplicates in the source directory against the destination directory
        matches1 = DuplicateFinder._find_matches_template(self.src_files, self.dst_files)

        # Only check for duplicates if the user selected two directories
        if self.dst_files != None:
            matches2 = DuplicateFinder._find_matches_template(self.dst_files, self.src_files)
            for hash, filenames in matches2.items():
                for filename in filenames:
                    if filename not in matches1[hash]:
                        matches1[hash].append(filename)

        # Only publish the matches which have more than one file name associated with them
        for hash, filenames in matches1.items():
            if len(filenames) > 1:
                self.matches[hash] = filenames

    @staticmethod
    def _find_uniques_template(src_files, dst_files):
        uniques = []
        for hash in src_files.keys():
            unique = None
            if dst_files == None:
                if len(src_files[hash]) == 1:
                    unique = src_files[hash]
            else:
                if hash not in dst_files:
                    unique = ', '.join(src_files[hash])
            if unique != None:
                uniques.append(unique)
        return uniques

    def _find_uniques(self):
        print('Finding files unique to {0}...'.format(self.src_dir))
        uniques1 = DuplicateFinder._find_uniques_template(self.src_files, self.dst_files)
        
        if self.dst_files != None:
            print('Finding files unique to {0}...'.format(self.dst_dir))
            uniques2 = DuplicateFinder._find_uniques_template(self.dst_files, self.src_files)
            self.uniques = uniques1 + uniques2
        else:
            self.uniques = uniques1

    def process_files(self):
        if self.matches != None:
            self._find_matches()
        elif self.uniques != None:
            self._find_uniques()
        
    def __str__(self):
        output = []
        if self.matches != None:
            output.append('The following are duplicate files:\n')
            for hash, filenames in self.matches.items():
                output.append('unique id: {0}'.format(hash))
                for filename in filenames:
                    output.append('\t{0}'.format(filename))
                output.append('\n')
        elif self.uniques != None:
            output.append('The following are unique files:\n')
            for filename in self.uniques:
                output.append('{0}'.format(filename))
            output.append('\n')
        return '\n'.join(output)

def _directory_exists(dir):
    if not os.path.isdir(dir):
        msg = "{0} is not a valid directory".format(dir)
        raise argparse.ArgumentTypeError(msg)
    return os.path.abspath(dir)

def parse_command_line():
    description = 'Find duplicates either within only the <source> dir or comparing ' \
                  'the contents of the <source> dir to the contents of the ' \
                  '<destination> dir.'
    parser = argparse.ArgumentParser(description=description)
    operation_group = parser.add_mutually_exclusive_group(required=True)
    operation_group.add_argument('-m', '--match', default=False, action='store_true', help='find files which match')
    operation_group.add_argument('-u', '--unique', default=False, action='store_true', help='find files which are unique')
    parser.add_argument('-s', '--source', metavar='<directory>', required=True, type=_directory_exists, help='source directory')
    parser.add_argument('-d', '--destination', metavar='<directory>', required=False, type=_directory_exists, help='destination directory')
    parser.add_argument('-o', '--output', metavar='<output>', default=sys.stdout, required=False, type=argparse.FileType('w'), help='file to output results')
    args = parser.parse_args()
    
    source = args.source
    destination = args.destination if args.destination != args.source else None
    return args.match, args.unique, source, destination, args.output

def main():
    match, unique, src_dir, dst_dir, output = parse_command_line()
    
    finder = DuplicateFinder(match, unique, src_dir, dst_dir)
    finder.hash_files()
    finder.process_files()
    print(finder, file=output)
    return 0
    
if __name__ == '__main__':
    sys.exit(main())

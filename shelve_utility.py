#!/usr/bin/env python
import argparse
import os
import re
import shutil
import sys

import Subversion

def CreateFullPath(dir):
    dirs = dir.split(os.path.sep)
    if sys.platform == 'win32' and dirs[0].endswith(':'):
        dirs[0] += os.path.sep
        
    new_dir = ''
    for dir_part in dirs:
        new_dir = os.path.join(new_dir, dir_part)
        if not os.path.isdir(new_dir):
            os.mkdir(new_dir)


def ShelveFiles(shelve_location, repository):
    svn = Subversion.Subversion()
    added, removed, modified, conflicts, unversioned = svn.GetOpenedFiles(repository)
    
    if len(removed):
        print 'WARNING: %d files have been removed. These files will not be shelved.' % len(removed)
    if len(conflicts):
        print 'ERROR: %d files have conflicts. Please fix them before continuing.' % len(conflicts)
        sys.exit(1)
    if len(unversioned):
        print 'ERROR: %d unversioned files. Please add or remove them before continuing.' % len(unversioned)
        sys.exit(1)
        
    if not os.path.isdir(shelve_location):
        os.mkdir(shelve_location)
    
    repository_parent = os.path.dirname(repository)
    
    for source in modified:
        destination = os.path.join(shelve_location, source[len(repository_parent) + 1:])
        CreateFullPath(os.path.dirname(destination))
        shutil.copy2(source, destination)
        print source


def UnshelveFiles(unshelve_location, repository):
    svn = Subversion.Subversion()
    repository_parent = os.path.dirname(repository)
    for root, dirs, files in os.walk(unshelve_location):
        for file in files:
            source = os.path.join(root, file)
            destination = os.path.join(repository_parent, source[len(unshelve_location) + 1:])

            if not os.path.isfile(destination) or not svn.IsFileInRepository(destination):
                print 'ERROR: %s doesn\'t exist in the file system or in the repository. (ADD)' % destination
                continue

            #if os.path.getmtime(destination) > os.path.getmtime(source):
            #    print 'ERROR: %s file is more recent in the repository than the shelve. (manual diff)'

            shutil.copy2(source, destination)
            print destination


def FindFileInHeirarchy(dir, filename):
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if os.path.exists(os.path.join(dir, filename)):
            return os.path.abspath(dir)
        else:
            dir = parent
            parent = os.path.abspath(os.path.join(dir, '..' ))
    return None


def IsValidShelveDirectory(dir):
    if not os.path.isdir(dir):
        if os.path.isdir(os.path.dirname(dir)):
            return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
        else:
            raise argparse.ArgumentTypeError('%s is not a valid shelve directory!' % dir)
    else:
        if len(os.listdir(dir)) == 0:
            return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
        else:
            raise argparse.ArgumentTypeError('%s is not a valid shelve directory' % dir)


def IsValidUnshelveDirectory(dir):
    if os.path.isdir(dir) and os.path.isdir(os.path.join(dir, 'code')):
        return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
    else:
        raise argparse.ArgumentTypeError('%s is not a valid unshelve directory' % dir)


def IsValidRepositoryDirectory(dir):
    if not os.path.isdir(dir):
        raise argparse.ArgumentTypeError('%s is not a valid repository directory' % dir)
        
    externals_txt_dir = FindFileInHeirarchy(dir, 'externals.txt')
    if not externals_txt_dir:
        raise argparse.ArgumentTypeError('%s is not a valid repository directory' % dir)
        
    with open(os.path.join(externals_txt_dir, 'externals.txt')) as externals_txt:
        data = externals_txt.read()
    if re.search('svn propset svn:externals -F externals\.txt \.', data):
        return os.path.normcase(os.path.normpath(os.path.abspath(dir)))
    else:
        raise argparse.ArgumentTypeError('%s is not a valid repository directory' % dir)
    

def ParseArgs():
    desc = 'Shelve and unshelve a set of repository changes'

    parser = argparse.ArgumentParser(description=desc)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-s', '--shelve', metavar='<location>', type=IsValidShelveDirectory)
    action_group.add_argument('-u', '--unshelve', metavar='<location>', type=IsValidUnshelveDirectory)
    parser.add_argument('repository_directory', type=IsValidRepositoryDirectory)
    parser.add_argument('--revert', default=False, action='store_true')

    args = parser.parse_args()
    return args.repository_directory, args.shelve, args.unshelve, args.revert
    
    
if __name__ == '__main__':
    repository, shelve_location, unshelve_location, revert = ParseArgs()

    if shelve_location:
        ShelveFiles(shelve_location, repository)
    elif unshelve_location:
        UnshelveFiles(unshelve_location, repository)

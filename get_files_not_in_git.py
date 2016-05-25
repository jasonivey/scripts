#!/usr/bin/python
# coding: utf-8
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
from __future__ import print_function
import argparse
import datetime
import git
import hashlib
import logging
import logging.handlers
import os
import sys
import traceback

def _update_logger(verbosity):
    if verbosity == 0:
        _log.setLevel(logging.ERROR)
    elif verbosity == 1:
        _log.setLevel(logging.INFO)
    elif verbosity >= 2:
        _log.setLevel(logging.DEBUG)

def _initialize_logger():
    logger = logging.getLogger(__name__)
    logging.captureWarnings(True)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    #handler = logging.handlers.TimedRotatingFileHandler(config_file.log_file,
    #                                                    when="midnight",
    #                                                    interval=1,
    #                                                    backupCount=7)
    #handler.setFormatter(formatter)
    #logger.addHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

_log = _initialize_logger()

def _is_directory(directory):
    if not os.path.isdir(directory):
        msg = "{0} is not a valid directory".format(directory)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(directory))

def _parse_args():
    parser = argparse.ArgumentParser(description='Get all the files that are not in the git repository')
    parser.add_argument('directory', default=os.getcwd(), type=_is_directory,
                        help='directory which contains the .git directory')
    parser.add_argument('-p', '--pretty-print', default=False, action='store_true',
                        help='output results in pretty print fashion')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='output verbose debugging information')
    args = parser.parse_args()
    _update_logger(args.verbose)
    directory = os.path.abspath(args.directory)
    _log.info('verbose: %d, pretty print: %s, directory: %s', args.verbose, args.pretty_print, directory)
    return args.pretty_print, directory

def _gethash(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()

def _get_repository_files(directory):
    _log.info('getting all files within the repository')
    repo = git.Git(directory)
    files = {}
    for filename in repo.ls_files().split():
        fullname = os.path.join(directory, filename)
        files[_gethash(fullname)] = fullname
    return files

def _get_all_files(directory):
    _log.info('getting all files within %s' % directory)
    all_files = {}
    for root, dirs, files in os.walk(directory):
        if root.startswith(os.path.abspath(os.path.join(directory, '.git'))):
            continue
        dir_entry = {}
        for filename in files:
            if not filename.endswith('.swp'):
                fullname = os.path.join(root, filename)
                dir_entry[_gethash(fullname)] = fullname
        all_files[root] = dir_entry
    return all_files

def _collapse_directories(filenames):
    files = filenames[:]
    files.sort(key=len)
    for i in files:
        for j in files:
            if i != j and j.startswith(i):
                files.remove(j)
    files.sort()
    return files 

def get_files_not_in_repo(directory):
    files = []
    repo_files = _get_repository_files(directory)
    filesystem_files = _get_all_files(directory)
    for dirname in filesystem_files.keys():
        dir_entries = filesystem_files[dirname]
        new_files = []
        for filehash, filename in dir_entries.iteritems():
            if filehash not in repo_files.keys():
                new_files.append(filename)
        if len(new_files) != len(dir_entries):
            files += new_files
        else:
            files.append(dirname)
    return _collapse_directories(files)

def main():
    pretty_print, directory = _parse_args()

    try:
        if pretty_print:
            print('\n'.join(get_files_not_in_repo(directory)))
        else:
            print(' '.join(get_files_not_in_repo(directory)))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

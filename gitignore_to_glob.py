#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
import os
from pathlib import Path
import sys
import traceback

from app_settings import app_settings

user_tags = {
    'title'     : parse('<bold><green>'),    # bold green
    'text'      : parse('<bold><white>'),    # bold white
    'alttext'   : parse('<white>'),          # white
    'name'      : parse('<bold><cyan>'),     # bold cyan
    'altname'   : parse('<cyan>'),           # cyan
    'error'     : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

def _title_print(title):
    am.ansiprint(f'<title>{title}</title>')

def file_exists(filename):
    path = Path(filename)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f'{filename} does not exist')
    return path

def _parse_args():
    parser = argparse.ArgumentParser(description='Convert .gitignore patterns to glob patterns')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-g', '--no-git', action="store_true", help='do not add .git and .github into the returned patterns')
    parser.add_argument('-s', '--seperator', default='|', help='string to seperate output globs')
    parser.add_argument('-w', '--wrapper', default='', help='string to specify, what if any, text to wrap the individual output')
    parser.add_argument('filenames', nargs='+', metavar='<.gitignore>', type=file_exists, help=\
                        'specify which gitignore files to convert')
    args = parser.parse_args()
    app_settings.update(vars(args))
    app_settings.print_settings(print_always=False)

def _parse_ignore_data(data):
    for line_number, pattern in enumerate(data.splitlines(), 1):
        pattern = pattern.strip()
        if not pattern:
            app_settings.info(f'{line_number:2}: empty, skipping')
            continue

        if pattern.startswith('#'):
            app_settings.info(f'{line_number:2}: comment, skipping -- {pattern}')
            continue

        app_settings.info(f'{line_number:2}: adding -- {pattern}')

        # the only modification needed is to strip the trailing '/' which is sometimes added to directories
        yield pattern.rstrip('/')

def git_ignore_to_glob(filenames, add_git):
    if add_git:
        yield '.git'
        yield '.github'
    for file_path in filenames:
        ignore_data = file_path.read_text()
        for pattern in _parse_ignore_data(ignore_data):
            yield pattern

def git_ignore_to_glob_str(filenames, add_git, seperator, wrapper):
    glob = ''
    for pattern in git_ignore_to_glob(filenames, add_git):
        glob += f'{wrapper}{pattern}{wrapper}{seperator}'
    return glob.strip(seperator)

def main():
    _parse_args()
    try:
        print(git_ignore_to_glob_str(app_settings.filenames, \
                                     (not app_settings.no_git), \
                                     app_settings.seperator, \
                                     app_settings.wrapper))
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())

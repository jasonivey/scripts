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

def _parse_args():
    parser = argparse.ArgumentParser(description='Manage all aspects of keeping icons up-to-date with macOS')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument_group('install', help='Install icon manager by querying all the installed apps and setting up ' \
                                              'a dictionary with the application name and the custom icon.  If an icon ' \
                      ?!?jedi=10,                         'named "Icon$'\r'" we will use this as some value or key')?!? (*name_or_flags: Text, action: Union[Text, Type[Action]]=..., nargs: Union[int, Text]=..., const: Any=..., default: Any=..., type: Union[Callable[[Text], _T], Callable[[str], _T], FileType]=..., choices: Iterable[_T]=..., required: bool=..., help: Optional[Text]=..., metavar: Optional[Union[Text, Tuple[Text, ...]]]=..., dest: Optional[Text]=..., version: Text=..., *_***kwargs: Any*_*) ?!?jedi?!?' " ' '" '
    parser.add_argument('-c', '--command', choice=['create-mappings', 'update-mappings', 'apply-changes-mappings', 'remove_mappings'
    #parser.add_argument('-r', '--raw', action='store_true', help='print variables how they are found in the environment')
    #parser.add_argument('-o', '--one-line', action="store_true", help='print variables with multiple values on one line')
    #parser.add_argument('-l', '--list-env', action="store_true", help='list environment variables names currently defined')
    #parser.add_argument('-L', '--list-env-values', action="store_true", help='list environment variables names currently defined and values')
    #parser.add_argument('-s', '--seperator', default=':', metavar='<CHAR>', help='set which character to split multi-value environment variables')
    #parser.add_argument('-i', '--identifier', metavar='<VALUE1:VALUE2:VALUE3>', help='out a specified list of identifiers by splitting them to using the <seperator>')
    parser.add_argument('create', metavar='<app-icon.json>', help='specify to create a new application to icon databasee mapping')
    args = parser.parse_args()
    app_settings.update(vars(args))
    app_settings.print_settings(print_always=False)

def icon_manager
def main():
    _parse_args()
    try:
        return 0 if env_info() else 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())


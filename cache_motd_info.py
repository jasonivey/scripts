#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from ansimarkup import AnsiMarkup, parse
import argparse
from app_settings import app_settings
import configparser
import os
from pathlib import Path
import sys
import traceback

user_tags = {
    'title'     : parse('<bold><green>'),    # bold green
    'text'      : parse('<bold><white>'),    # bold white
    'alttext'   : parse('<white>'),          # white
    'name'      : parse('<bold><cyan>'),     # bold cyan
    'altname'   : parse('<cyan>'),           # cyan
    'error'     : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

def _get_default_conf_path():
    return str(Path(os.path.expandvars('$HOME/.config/motd/motd.conf')))

def _existing_conf_path(p):
    updated_path = Path(os.path.expandvars(p))
    if not updated_path.is_file:
        raise argparse.ArgumentTypeError(f'ERROR: configuration file {p} must exist')
    return str(updated_path)

def _new_conf_path(p):
    return str(Path(p))

def _parse_args():
    default_conf_path = _get_default_conf_path()
    parser = argparse.ArgumentParser(description='Helper script which looks up login info and caches it in sqlite3 databse')
    config_group = parser.add_mutually_exclusive_group()
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-d', '--databse', metavar='<DB PATH>', help='directory to find and store databse')
    config_group.add_argument('-c', '--config', default=argparse.SUPPRESS, type=_existing_conf_path, metavar='<CONFIG PATH>', help='config ini file to specify parameters')
    config_group.add_argument('-w', '--write-default-config', dest='write_config', default=argparse.SUPPRESS, type=_new_conf_path, metavar='<CONFIG PATH>', help='write default ini file')

    args = parser.parse_args()
    app_settings.update(vars(args))
    app_settings.print(f'config: {app_settings.config}')
    app_settings.print(f'write config: {app_settings.write_config}')
    app_settings.print_settings(print_always=False)

def cache_motd_info():
    pass

def write_motd_config(path):
    app_settings.verbose('creating new motd config in {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    config['DEFAULT'] = {} 
    config['DEFAULT']['database'] = str(path.with_name('motd.db'))
    config['DEFAULT']['values'] = [ 
    'computer-name', 'hostname', 'public-ip', 'mail', 
    'system-load', 'processes', 
    'root-usage', 'users-logged-in',
    'memory-usage', 'swap-usage', 
    config[


def main():
    _parse_args()
    try:
        if app_settings.write_config:
            write_motd_config(Path(app_settings.write_config))
        cache_motd_info()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

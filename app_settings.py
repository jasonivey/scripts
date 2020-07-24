#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
from collections import UserDict
from enum import IntEnum
import os
import sys
import traceback

class OutputType(IntEnum):
    NONE = 0
    INFO = 1
    LOWINFO = 2
    DEBUG = 3
    WARN = 4
    ERROR = 5
    ASSERT = 6

user_tags = {
    OutputType.NONE.name     : parse('<bold><white>'),    # bold white
    OutputType.INFO.name     : parse('<bold><green>'),    # bold green
    OutputType.LOWINFO.name  : parse('<bold><cyan>'),     # bold cyan
    OutputType.DEBUG.name    : parse('<bold><blue>'),     # bold blue 
    OutputType.WARN.name     : parse('<bold><yellow>'),   # bold yellow
    OutputType.ERROR.name    : parse('<bold><red>'),      # bold red
    OutputType.ASSERT.name   : parse('<bold><magenta>'),  # bold magenta
}

am = AnsiMarkup(tags=user_tags)

class AppSettings(UserDict):
    def __init__(self):
        UserDict.__init__(self)

    def __getattr__(self, name):
        return self.data[name]

    def __setattr__(self, name, value):
        UserDict.__setattr__(self, name, value)

    def __delattr__(self, name):
        del self.data[name]

    def update(self, other):
        for name, value in other.items():
            # flatten the list when its a list-of-lists (i.e. [['apple'], ['orange', 'carrot'], ['pea']])
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
                value = [item for sublist in value for item in sublist]
            self.data[name] = value

    # The one built-in setting that we assume will always be in every app
    def _set_verbosity(self):
        # if its not set -- set it to no verbosity
        if 'verbose' not in self.data:
            self.data['verbose'] = 0
        # if its set to True/False -- switch it to 1/0 respectively
        if isinstance(self.data['verbose'], bool):
            self.data['verbose'] = int(getattr(self, 'verbose'))

    def _get_verbosity(self):
        self._set_verbosity()
        return self.data['verbose']

    def print_settings(self, print_always=False):
        if print_always or self._get_verbosity() >= OutputType.INFO:
            msg = 'app settings:\n'
            for name, value in self.data.items():
                if isinstance(value, list):
                    value = ', '.join([str(elem) for elem in value])
                msg += f'  {name}: "{value}"\n'
            am.ansiprint('<{0}>{1}</{0}>'.format(OutputType.INFO.name, msg), end='', file=sys.stdout)

    @staticmethod
    def _internal_fmt(prefix_type, prefix, msg_type, msg):
        return am.ansistring('<{0}>{1}:</{0}> <{2}>{3}</{2}>'.format(prefix_type, prefix, msg_type, msg))

    # Always return true/false from these output functions so they can be used as short-circuit methods
    #  when wanting to print a failure and return False. NOTE: warn returns true. Is this OK?
    @staticmethod
    def print(msg):
        am.ansiprint('<{0}>{1}</{0}>'.format(OutputType.NONE.name, msg), file=sys.stdout)
        return True

    def info(self, msg):
        verbosity = self._get_verbosity()
        if verbosity >= OutputType.INFO:
            print(AppSettings._internal_fmt(OutputType.INFO.name, 'INFO', OutputType.NONE.name, msg), file=sys.stdout)
        return True

    def lowinfo(self, msg):
        verbosity = self._get_verbosity()
        if verbosity >= OutputType.LOWINFO:
            print(AppSettings._internal_fmt(OutputType.LOWINFO.name, 'LOWINFO', OutputType.NONE.name, msg), file=sys.stdout)
        return True

    def debug(self, msg):
        verbosity = self._get_verbosity()
        if verbosity >= OutputType.DEBUG:
            print(AppSettings._internal_fmt(OutputType.DEBUG.name, 'DEBUG', OutputType.NONE.name, msg), file=sys.stdout)
        return True

    @staticmethod
    def warn(msg):
        print(AppSettings._internal_fmt(OutputType.WARN.name, 'WARN', OutputType.NONE.name, msg), file=sys.stderr)
        return True

    @staticmethod
    def error(msg):
        print(AppSettings._internal_fmt(OutputType.ERROR.name, 'ERROR', OutputType.NONE.name, msg), file=sys.stderr)
        return False

    @staticmethod
    def assertion(msg):
        return AppSettings._internal_fmt(OutputType.ASSERT.name, 'ASSERT', OutputType.NONE.name, msg)

    def __str__(self):
        return 'App Settings:\n' + '\n'.join([f'  {key}={value}' for key, value in self.data.items()])

app_settings = AppSettings()

def main():
    app_settings.update({'verbose' : 4})
    app_settings.print('test print message')
    app_settings.info('test info message')
    app_settings.lowinfo('test lowinfo message')
    app_settings.debug('test debug message')
    app_settings.warn('test warn message')
    app_settings.error('test error message')
    print(app_settings.assertion('test assertion message'), file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())

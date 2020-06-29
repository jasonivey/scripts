#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
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
    OutputType.LOWINFO.name  : parse('<green>'),          # green
    OutputType.DEBUG.name    : parse('<bold><cyan>'),     # bold cyan
    OutputType.WARN.name     : parse('<bold><yellow>'),   # bold yellow
    OutputType.ERROR.name    : parse('<bold><red>'),      # bold red
    OutputType.ASSERT.name   : parse('<bold><magenta>'),  # bold magenta
}

am = AnsiMarkup(tags=user_tags)

class AppSettings(object):
    class __AppSettings(object):
        def __init__(self):
            super(AppSettings.__AppSettings, self).__setattr__('values', {})

        def __getattr__(self, name):
            try:
                return self.values[name]
            except KeyError:
                raise AttributeError

        def __setattr__(self, name, value):
            self.values[name] = value

        def set(self, args):
            for name, value in args.items():
                self.values[name] = value

        def _set_verbosity(self):
            # if its not set -- set it to no verbosity
            if 'verbose' not in self.values:
                self.values['verbose'] = 0
            # if its set to True/False -- switch it to 1/0 respectively
            if isinstance(self.values['verbose'], bool):
                self.values['verbose'] = int(self.values['verbose'])

        def _get_verbosity(self):
            self._set_verbosity()
            return self.values['verbose']

        def print_settings(self, print_always=False):
            if print_always or self._get_verbosity() >= OutputType.INFO:
                msg = 'app settings:\n'
                for name, value in self.values.items():
                    if isinstance(value, list):
                        value = ', '.join(value)
                    msg += f'  {name}: "{value}"\n'
                am.ansiprint('<{0}>{1}</{0}>'.format(OutputType.INFO.name, msg), end='', file=sys.stdout)

        def print(self, msg):
            am.ansiprint('<{0}>{1}</{0}>'.format(OutputType.NONE.name, msg), file=sys.stdout)

        def info(self, msg):
            verbosity = self._get_verbosity()
            if verbosity >= OutputType.INFO:
                am.ansiprint('<{0}>INFO: {1}</{0}>'.format(OutputType.INFO.name, msg), file=sys.stdout)

        def lowinfo(self, msg):
            verbosity = self._get_verbosity()
            if verbosity >= OutputType.LOWINFO:
                am.ansiprint('<{0}>LOWINFO: {1}</{0}>'.format(OutputType.LOWINFO.name, msg), file=sys.stdout)

        def debug(self, msg):
            verbosity = self._get_verbosity()
            if verbosity >= OutputType.DEBUG:
                am.ansiprint('<{0}>DEBUG: {1}</{0}>'.format(OutputType.DEBUG.name, msg), file=sys.stdout)

        def warn(self, msg):
            am.ansiprint('<{0}>WARNING: {1}</{0}>'.format(OutputType.WARN.name, msg), file=sys.stderr)

        def error(self, msg):
            am.ansiprint('<error>ERROR: {msg}</error>', file=sys.stderr)

        def assertion(self, msg):
            return am.ansistring('<{0}>ASSERTION: {1}</{0}>'.format(OutputType.ASSERT.name, msg), file=sys.stderr)

        def __str__(self):
            return 'App Settings:\n' + '\n'.join([f'  {key}={value}' for key, value in self.values.items()])

    __instance = None
    def __new__(cls): # __new__ always a classmethod
        if not AppSettings.__instance:
            AppSettings.__instance = AppSettings.__AppSettings()
        return AppSettings.__instance

    def __getattr__(self, name):
        return self.__instance.getattr(name)

    def __setattr__(self, name, value):
        self.__instance.settattr(name, value)

    def set(self, args):
        self.__instance.set(args)

    def print_settings(self, print_always=False):
        self.__instance.print_settings(print_always)

    def print(self, msg):
        self.__instance.print(msg)

    def info(self, msg):
        self.__instance.info(msg)

    def lowinfo(self, msg):
        self.__instance.lowinfo(msg)

    def debug(self, msg):
        self.__instance.debug(msg)

    def warn(self, msg):
        self.__instance.warn(msg)

    def error(self, msg):
        self.__instance.error(msg)

    def assertion(self, msg):
        return self.__instance.assertion(msg)

    def __str__(self):
        return str(self.__instance)

app_settings = AppSettings()

def main():
    # quote, name = _parse_args()
    # try:
    #     if list_system_environment_variables:
    #         _output_all_system_environment_variables()
    #     if environment_variables:
    #         _output_environment_variable_values(environment_variables, output_one_line, seperators)
    #     if values:
    #         _output_values(values, seperators)
    # except:
    #     exc_type, exc_value, exc_traceback = sys.exc_info()
    #     traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    #     return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

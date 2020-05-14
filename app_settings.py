#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
import os
import sys
import traceback

class AppSettings(object):
    class __AppSettings(object):
        def __init__(self):
            super(AppSettings.__AppSettings, self).__setattr__('values', {})
            #self.values = {}

        def __getattr__(self, name):
            #if name == 'values':
            #    return self.values
            #elif name not in self.values:
            #    self.values[name] = default
            try:
                return self.values[name]
            except KeyError:
                raise AttributeError

        def __setattr__(self, name, value):
            #if name == 'values':
            #    self.values = value
            #else:
            self.values[name] = value

        def print(self, s):
            verbose_enabled = 'verbose' in self.values and self.values['verbose']
            no_verbose_setting = 'verbose' not in self.values
            if verbose_enabled or no_verbose_setting:
                print(s, file=sys.stdout)

        def __str__(self):
            return 'App Settings:\n  verbose: {}\n  live run: {}\n  directories: {}' \
                   .format(self.verbose,self.live_run, self.directories)

    __instance = None
    def __new__(cls): # __new__ always a classmethod
        if not AppSettings.__instance:
            AppSettings.__instance = AppSettings.__AppSettings()
        return AppSettings.__instance

    def __getattr__(self, name):
        return self.__instance.getattr(name)

    def __setattr__(self, name, value):
        self.__instance.settattr(name, value)

    def print(self, s):
        self.__instance.print(s)

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

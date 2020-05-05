#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import sys
import traceback

class AppSettings(object):
    class __AppSettings:
        def __init__(self):
            self.verbose = False
            self.live_run = False
            self.directories = None

        def print(self, s):
            if self.verbose:
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
        return getattr(self.__instance, name)

    def __setattr__(self, name):
        return setattr(self.__instance, name)

    def print(self, s):
        AppSettings.__instance.print(s)

    def __str__(self):
        return str(AppSettings.__instance)

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

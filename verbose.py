#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import sys
import traceback

class Verbose(object):
    __instance = None
    def __new__(cls):
        if Verbose.__instance is None:
            Verbose.__instance = object.__new__(cls)
            Verbose.__instance.verbose = False
        return Verbose.__instance

    @property
    def value(self):
        Verbose.__instance.verbose

    @x.setter
    def value(self, value):
        Verbose.__instance.verbose = value

    def print(s):
        if Verbose.__instance.verbose:
            print(s, file=sys.stdout)

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

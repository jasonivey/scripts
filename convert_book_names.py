#!/usr/bin/env python

import argparse
import logging
import os
import re
import string
import sys
import traceback


def parse_command_line():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

def main():
    parse_command_line()
    
    output = []
    pattern = r'(?P<title>.*)\s+-\s+(?P<author>.*)\.(?P<extension>epub|pdf)'
    for filename in os.listdir(os.getcwd()):
        match = re.match(pattern, filename)
        assert match
        output.append('{author} - {title}.{extension}'.format(**match.groupdict()).replace('_', ':'))
    output.sort(key=string.lower)
    print('\n'.join(output))
    return 0

if __name__ == '__main__':
    sys.exit(main())

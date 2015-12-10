#!/usr/bin/python

import argparse
import exceptions
import base64
import binascii
import sys
import traceback
import uuid

def _parse_args():

    return ['file1.txt', 'file2.txt']

def main():
    try:
        print(s)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

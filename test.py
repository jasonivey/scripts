#!/usr/bin/env python
from __future__ import print_function
import argparse
import collections
import exceptions
import glob
import os
import re
import sys
import subprocess

def main(args):
    avi_dir = r'G:\movies\avi'
    ipod_dir = r'G:\movies\ipod'
    avi_files = []
    for root, dirs, files in os.walk(avi_dir):
        for filename in files:
            full_path = os.path.join(root, filename)
            if not os.path.isfile(full_path) or not filename.endswith('.avi'):
                continue
            ipod_path = r'{0}\{1}.*'.format(ipod_dir, os.path.splitext(filename)[0])
            ipod_path1 = r'{0}\{1} - iP?d.*'.format(ipod_dir, os.path.splitext(filename)[0])
            if len(glob.glob(ipod_path)) == 0 and len(glob.glob(ipod_path1)) == 0:
                avi_files.append(full_path)
            print('.', end='')
    print('\n{0}\n'.format('\n'.join(avi_files)))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

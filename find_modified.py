#!/usr/bin/env python

import os, sys, Utils
from stat import *

def IsNotReadOnly(filename):
    return os.stat(filename)[ST_MODE] & S_IWRITE != 0

if __name__ == '__main__':
    files = Utils.RecurseDirectory( os.getcwd(), IsNotReadOnly, False )
    files.sort()
    for file in files:
        print(file)

#!/usr/bin/env python
import os
import sys
import argparse

def DiffDumpFiles(file1, file2):
    
    len
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lists differences between two files created with DumpDir.py')
    parser.add_argument('file1', type=argparse.FileType('r'), metavar='"input file 1"', help='First file to compare')
    parser.add_argument('file2', type=argparse.FileType('r'), metavar='"input file 2"', help='Second file to compare')
    args = parser.parse_args()
    
    file1 = args.file1
    file2 = args.file2
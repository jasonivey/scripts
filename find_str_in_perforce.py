#!/usr/bin/env python
import os
import sys
import re
import fnmatch
import subprocess

global P4EXE, P4PORT, P4_PREFIX_PATH
P4EXE = 'p4'
P4PORT = r'10.160.2.60:1667'
P4_PREFIX_PATH = r'//SEABU/ProductSource'


class Match:
    "Structure to encapsulate a text match in a file."
    def __init__(self, filename, number, line):
        self.mFileName = filename
        self.mLineNumber = number
        self.mLine = line
        
    def __str__(self):
        if self.mLineNumber != 0:
            return '%s:%s:%s' % (self.mFileName, self.mLineNumber, self.mLine)
        elif self.mLine:
            return '%s:%s' % (self.mFileName, self.mLine)
        else:
            return '%s' % self.mFileName


def GetPerforceCommand(cmd):
    return '%s -p %s %s' % ( P4EXE, P4PORT, cmd )


def SearchFile(filename, str, insensitve, fast):
    matches = []
    command = GetPerforceCommand('print -q "%s"' % filename)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flags = re.I if insensitve else 0
    
    if fast:
        output = p.stdout.read()
        regex = re.compile(str, flags)
        if regex.search(output):
            match = Match(filename, 0, None)
            key = '%s' % filename
            matches.append(match)
    else:
        output = p.stdout.readlines()
        number = 1
        for line in lines:
            if re.search(str, line, flags):
                match = Match(filename, number, line)
                matches.append(match)
            number += 1
            
    return matches

    
def GetFiles(dir, recursive):
    suffix = '...' if recursive else '*'
    if dir:
        command = GetPerforceCommand('files %s/%s/%s' % (P4_PREFIX_PATH, dir, suffix))
    else:
        command = GetPerforceCommand('files %s/%s' % (P4_PREFIX_PATH, suffix))
    print('Running command %s' % command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.stdout.read()
    print('Output: %s' % output[0:200])
    pattern = r'(?P<name>%s[^#]+)#\d+ *- *(add|edit|integrate|branch) *change *\d+ *\(text\)\n' % P4_PREFIX_PATH
    files = []
    for i in re.finditer(pattern, output, re.S):
        files.append( i.group('name') )
        
    print('Found %d files.' % len(files))
    return files


def ParseArgs(args):
    insensitve = False
    recursive = False
    lineNumbers = False
    pattern = None
    dir = None
    searchStr = None
    
    for arg in args:
        if arg.startswith('-') or arg.startswith('/'):
            for letter in arg.lower():
                if letter == 'i':
                    insensitve = True
                elif letter == 's':
                    recursive = True
                elif letter == 'n':
                    lineNumbers = True
        elif not arg.startswith('-') and not arg.startswith('/') :
            if not searchStr:
                searchStr = arg
            elif not pattern:
                pattern = arg.replace('\\', '/')
                index = pattern.rfind('/')
                if index != -1:
                    dir = pattern[:index + 1].strip('/')
                    pattern = pattern[index + 1:]
            else:
                print('ERROR: Invalid command line argument "%s".' % arg)
                sys.exit(1)
                
    if not pattern or not searchStr:
        print 'ERROR: A search string and depot folder must be specified.'
        sys.exit(1)
    
    print(searchStr)
    print(dir)
    print(pattern)
    
    return insensitve, recursive, lineNumbers, pattern, dir, searchStr


if __name__ == '__main__':
    #print len(sys.argv)
    #if len(sys.argv) < 3:
    #    print('Usage: FindStrInPerforce.py <search string> <depot folder & wildcards>')
    #    sys.exit(1)
    
    insensitve, recursive, lineNumbers, pattern, dir, searchStr = ParseArgs(sys.argv[1:])
    
    #print('insensitive: %s' % insensitve)
    #print('recursive: %s' % recursive)
    #print('dir: %s' % dir)
    #print('pattern: %s' % pattern)
    #print('searchStr: %s' % searchStr)
    
    files = GetFiles(dir, recursive)
    for file in fnmatch.filter( files, pattern ):
        print('Searching file: %s' % file)
        for match in SearchFile(file, searchStr, insensitve, not lineNumbers):
            print match

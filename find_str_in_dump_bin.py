#!/usr/bin/env python

import os
import sys
import re
import fnmatch
import subprocess
import tempfile
import Utils

def GetFiles(dir, filePattern):
    paths = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if fnmatch.fnmatch(os.path.join(root, file), filePattern):
                paths.append(os.path.join(root, file))
    return paths

    
def ParseArgs(args):
    filePattern = None
    strPattern = None
    ignoreCase = False
    
    i = 0
    count = len(args)
    while i < count:
        arg = args[i]
        if Utils.IsSwitch(arg) and arg[1:].lower().startswith('f') and i + 1 < count:
            filePattern = args[i + 1]
            i += 1
        elif Utils.IsSwitch(arg) and arg[1:].lower().startswith('s') and i + 1 < count:
            strPattern = args[i + 1]
            i += 1
        elif Utils.IsSwitch(arg) and arg[1:].lower().startswith('i'):
            ignoreCase = True
        i += 1
    
    if 'VS90COMNTOOLS' not in os.environ:
        print('ERROR: VS90COMNTOOLS not defined in the environment!')
        sys.exit(1)
        
    if not filePattern or not strPattern:
        print('ERROR: Specify a file pattern and a search string with -f and -s!')
        sys.exit(1)
        
    return filePattern, strPattern, ignoreCase


def DumpBin(filename):
    filehandle, tmpfilename = tempfile.mkstemp()
    os.close(filehandle)

    vcvars = os.path.normpath( os.path.join( os.environ['VS90COMNTOOLS'], '..', '..', 'vc', 'bin', 'vcvars32.bat' ) )
    command = '"%s" && dumpbin.exe /all /out:%s %s' % (vcvars, tmpfilename, filename)
    print(command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    
    return tmpfilename


if __name__ == '__main__':
    filePattern, strPattern, ignoreCase = ParseArgs(sys.argv)

    for filename in GetFiles(os.getcwd(), filePattern):
        output_file_name = DumpBin(filename)
        printHeader = False
        with open(output_file_name) as file:
            for line in file.readlines():
                match = re.search(strPattern, line, re.I if ignoreCase else 0)
                if not match:
                    continue
                if not printHeader:
                    printHeader = True
                    print('%s:' % filename)
                print('\t%s' % line.strip('\n'))
        os.remove(output_file_name)


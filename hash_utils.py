#!/usr/bin/env python
import argparse
import os
import hashlib
import re
import stat
import string
import subprocess
import sys
import traceback
import zlib

import custom_utils

#class Hasher:
#    mHashObj = None # hashlib.md5
#    mHashObj.update(str) # m.update(str) -- iteratively!!!
#    return mHashObj.hexdigest()

_HASH_FUNCTIONS = [hashlib.md5]

class Hasher(object):
    def __init__(self, hash_type):
        self.mHashObject = hash_type
    def update(self, str_value):
        self.mHashObject.update(str_value)
    def hexdigest(self):
        return self.mHashObject.hexdigest()

def CreateHasher(hash_type):
    hasher = Hasher(hash_type)
    return hasher
    #create object of type and be useable afterwards here!

#class shell_hash_types:
#    '''Given a platform type it will return the subset of available hash functions available'''
#    def __init__(self):
#        platform_id = custom_utils.get_platform_id()

#class hash_types:
#    '''Given a platform type it will return the subset of available hash functions available'''
#    def __init__(self):
#        platform_id = custom_utils.get_platform_id()

#class hash_util:
#    '''Creates a crc/md5/sha1/etc. based on file like objects'''
#    def __init__(self, hash_obj=None, shell=None):
#        self.mHashObj = hashlib.md5() if hash_obj is None else hash_obj
#        self.mShell = 'md'

def _md5sum_shell(file_name):
    '''Calls the md5sum shell binary to calculate the hash of a file.'''
    command = 'md5sum {0}'.format(custom_utils.prepare_filename_for_shell(file_name))
    process = subprocess.Popen(command, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        raise Exception('md5sum returned an error processing file {0}'.format(file_name))
    match = re.search(r'^(?P<md5sum>\w+)\s+', stdoutdata.strip('\\'))
    if match is None:
        raise Exception('md5sum did not return the expected output for file {0}'.format(file_name))
    return match.group('md5sum').lower()
    
def md5sum_shell(file_name):
    '''Calls the md5sum/md5 shell binary to calculate the hash of a file.'''
    if not custom_utils.is_binary_in_path('md5sum'):
        raise Exception('md5sum is not available -- \'brew brew install coreutils\' will install on Mac')
    return _md5sum_shell(file_name)

def _sumstr(s):
    '''Returns a md5 hash for a string.'''
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()
    
def _sumfile(fobj, size):
    '''Returns a md5 hash for an object with read() method.'''
    m = hashlib.md5()
    while True:
        d = fobj.read(size)
        if not d:
            break
        m.update(d)
    return m.hexdigest()

def md5sum(fname_or_str):
    '''Returns a md5 hash for a file or a string.'''
    if os.path.isfile(fname_or_str):
        fname = fname_or_str
        size = min(os.stat(fname)[stat.ST_SIZE], 16 * 1048576)
        with open(fname, 'rb') as f:
            return _sumfile(f, size)
    else:
        s = fname_or_str
        return _sumstr(s)

def _crc32_shell(file_name):
    '''Calls the crc32 shell binary to calculate the crc of a file.'''
    command = 'crc32 {0}'.format(custom_utils.prepare_filename_for_shell(file_name))
    process = subprocess.Popen(command, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        raise Exception('crc32 failed processing file {0}'.format(file_name))
    return stdoutdata.strip()

def _crc_shell(file_name):
    '''Calls the Windows crc shell binary to calculate the crc of a file.'''
    command = 'crc {0}'.format(custom_utils.prepare_filename_for_shell(file_name))
    process = subprocess.Popen(command, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        raise Exception('crc failed processing file {0}'.format(file_name))
    match = re.search(r'CRC of file .*? is 0x(?P<crc>\w+)\r\n', stdoutdata)
    if match is None:
        raise Exception('failed to find crc from output for file {0}'.format(file_name))
    return match.group('crc').lower()

def crc32_shell(file_name):
    '''Calls the appropriate crc shell binary to calculate the crc of a file.'''
    if os.name == 'nt' and not custom_utils.is_binary_in_path('crc32'):
        return _crc_shell(file_name)
    else:
        return _crc32_shell(file_name)

def _crcstr(s):
    '''Returns a crc hash for a string.'''
    ret = zlib.crc32(data)
    return '%08x' % (ret & 0xFFFFFFFF)

def _crcfile(fobj, size):
    '''Returns a crc hash for a file.'''
    ret = None
    while True:
        data = fobj.read(size)
        if not data:
            break
        ret = zlib.crc32(data) if not ret else zlib.crc32(data, ret) 
    return '%08x' % ((0 if not ret else ret) & 0xFFFFFFFF)

def crc32(fname_or_str):
    '''Returns a crc hash for a file or a string.'''
    if os.path.isfile(fname_or_str):
        fname = fname_or_str
        size = min(os.stat(fname)[stat.ST_SIZE], 16 * 1048576)
        with open(fname, 'rb') as f:
            return _crcfile(f, size)
    else:
        s = fname_or_str
        return _crcstr(s)

def _parse_args():
    parser = argparse.ArgumentParser(description='Creates chksum\'s of files')
    #parser.add_argument('-'
    parser.add_argument('-c', '--crc32', dest='crc32', default=False, action='store_true', help='hash input using python zlib crc32')
    parser.add_argument('-cs', '--crc32-shell', dest='crc32_shell', default=False, action='store_true', help='hash input using shell crc32 program')
    parser.add_argument('-m', '--md5sum', dest='md5sum', default=False, action='store_true', help='hash input using python hashlib md5')
    parser.add_argument('-ms', '--md5sum-shell', dest='md5sum_shell', default=False, action='store_true', help='hash input using shell md5sum program')
    parser.add_argument('input', nargs='+', metavar='<input>', help='input to use for creating hash')
    args = parser.parse_args()

    md5sum = args.md5sum
    if not args.crc32 and not args.crc32_shell and not args.md5sum and not args.md5sum_shell:
        md5sum = True

    input_files = []
    input_names = args.input
    for name in input_names:
        if os.path.isdir(name):
            input_files += custom_utils.get_files_in_directory(name)
        elif os.path.isfile(name):
            input_files.append(name)
    input_files.sort(key=string.lower)

    if len(input_files) == 0:
        raise argparse.ArgumentError('input', 'must specify either one or more files/directories to hash')

    return input_files, md5sum, args.md5sum_shell, args.crc32, args.crc32_shell

def main():
    input_files, calc_md5sum, calc_md5sum_shell, calc_crc32, calc_crc32_shell = _parse_args()
    try:
        for input_file in input_files:
            if calc_md5sum:
                print(('%s %s' % (md5sum(input_file), os.path.abspath(input_file))))
            if calc_md5sum_shell:
                print(('%s %s' % (md5sum_shell(input_file), os.path.abspath(input_file))))
            if calc_crc32:
                print(('%s %s' % (crc32(input_file), os.path.abspath(input_file))))
            if calc_crc32_shell:
                print(('%s %s' % (crc32_shell(input_file), os.path.abspath(input_file))))
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1

if __name__ == '__main__':
    hasher = CreateHasher(_HASH_FUNCTIONS[0])
    os.system('md5 .bazaar/ignore')
    hasher.update('asdfasdfasdf')
    os.system('internal hasher: {0}'.format(hasher.hexdigest))
    sys.exit(main())


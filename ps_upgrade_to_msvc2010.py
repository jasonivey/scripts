#!/usr/bin/env python
import argparse
import re
import os
import shutil
import subprocess
import sys


def FindFileInHeirarchy(dir, filename):
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if os.path.exists(os.path.join(dir, filename)):
            return os.path.abspath(dir)
        else:
            dir = parent
            parent = os.path.abspath(os.path.join(dir, '..' ))
    return None


def FindSvnText(dir):
    # Try searching up!
    dev_dir = FindFileInHeirarchy(dir, 'svn.txt')
    if dev_dir:
        return dev_dir
    
    # Try searching down
    down_dirs = os.listdir(dir)
    new_down_dir = dir
    while len(down_dirs) == 1 or (len(down_dirs) == 2 and '.info' in down_dirs):
        for sub_dir in dirs:
            if sub_dir == '.info':
                continue
            full_sub_dir = os.path.join(new_down_dir, sub_dir)
            if os.path.isfile(os.path.join(full_sub_dir, 'svn.txt')):
                return full_sub_dir
            else:
                new_down_dir = full_sub_dir
        down_dirs = os.listdir(new_down_dir)
    return None
    
    
def IsInSandbox(dir):
    if not os.path.isdir(dir):
        raise argparse.ArgumentTypeError('%s was not a valid directory' % dir)
    svn_dir = FindSvnText(dir)
    if not svn_dir:
        raise argparse.ArgumentTypeError('Unable to find a valid sandbox within %s' % dir)
    return svn_dir
    

def ParseArgs():
    desc = 'Upgrade the sandbox to compile with Visual Studio 2010'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('sandbox_dev_directory', metavar='<directory within the sandbox>', type=IsInSandbox, default=os.getcwd(), nargs='?')
    args = parser.parse_args()
    return args.sandbox_dev_directory


def RemoveBoost(code_dir):
    shutil.rmtree(os.path.join(code_dir, 'boost'))
    return True


def UpdateExternalsTxt(filename):
    with open(filename) as file:
        data = file.read()
    
    pattern = r'(boost\s+)(?P<rev>-r\d+)(\s+https://subversion.assembla.com/svn/ps-share/trunk/tools/external/)(?P<branch>boost[^\s]+)'
    match = re.search(pattern, data, re.MULTILINE | re.IGNORECASE)
    if not match:
        print('ERROR: unable to update the boost component. It wasn\'t found in externals.txt')
        return False
    
    # Already updated, good!
    if match.group('branch').lower() == 'boost_1_46_1':
        return True

    new_data = re.sub(pattern, r'\1-r9876\3boost_1_46_1', data)
    assert data != new_data
        
    with open(filename, 'w') as file:
        file.write(new_data)
    
    command = 'svn propset svn:externals -F externals.txt .'
    if subprocess.Popen(command, cwd=os.path.dirname(filename)).wait() != 0:
        print('ERROR: while updating externals.txt')
        return False
    
    RemoveBoost(os.path.dirname(filename))
    return True
    

def FixBinaryTypeInCMake(code_dir, rel_path):
    filename = os.path.join(code_dir, rel_path)
    with open(filename) as file:
        data = file.read()
    
    pattern = r'(add_executable\s*\(\s*%s\s+)WIN32\s+(\$\{SOURCES\}\s+\$\{HEADERS\}\s+\))' % os.path.basename(os.path.dirname(filename))
    match = re.search(pattern, data, re.MULTILINE | re.IGNORECASE)
    if not match:
        pattern = r'(add_executable\s*\(\s*%s\s+)(\$\{SOURCES\}\s+\$\{HEADERS\}\s+\))' % os.path.basename(os.path.dirname(filename))
        match = re.search(pattern, data, re.MULTILINE | re.IGNORECASE)
        if not match:
            print('ERROR: unable to update %s since \'add_executable\' wasn\'t found' % rel_path)
            return False
        else:
            print('INFO: %s has already been updated' % rel_path)
            return True
    
    new_data = re.sub(pattern, r'\1\2', data)
    assert data != new_data

    with open(filename, 'w') as file:
        file.write(new_data)
    return True


def DisableIncrementalLinkingInCMake(code_dir, rel_path):
    filename = os.path.join(code_dir, rel_path)
    with open(filename) as file:
        if re.search('USE_MSVC_INCREMENTAL_LINKING', file.read()):
            return True

    additional_script = \
'''
IF(MSVC)
    IF (NOT USE_MSVC_INCREMENTAL_LINKING)
        SET( MSVC_INCREMENTAL_YES_FLAG "/INCREMENTAL:NO")

        STRING(REPLACE "/INCREMENTAL:YES" "" replacementFlags ${CMAKE_EXE_LINKER_FLAGS_DEBUG})
        STRING(REPLACE "/INCREMENTAL" "" replacementFlags ${replacementFlags}) 
        SET(CMAKE_EXE_LINKER_FLAGS_DEBUG "/INCREMENTAL:NO ${replacementFlags}" )

        STRING(REPLACE "/INCREMENTAL:YES" "" replacementFlags3 ${CMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO})
        STRING(REPLACE "/INCREMENTAL" "" replacementFlags3 ${replacementFlags3})
        SET(CMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO "/INCREMENTAL:NO ${replacementFlags3}" )
    ENDIF (NOT USE_MSVC_INCREMENTAL_LINKING)
ENDIF(MSVC)

'''

    with open(filename, 'a') as file:
        file.write(additional_script)
    return True

    
def ProcessCMakeFiles(code_dir):
    FIX_BINARY_TYPE = 1
    REMOVE_INCREMENTAL_LINKING = 2
    
    cmakes = [(r'PsHost\CMakeLists.txt', FIX_BINARY_TYPE | REMOVE_INCREMENTAL_LINKING),
              (r'RPMUtil\CMakeLists.txt', FIX_BINARY_TYPE | REMOVE_INCREMENTAL_LINKING),
              (r'PsCppUnit\test\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'PsUtil\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'nlplib\test\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'nlplib\test\test-library-loaders\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'nlplib\test\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'PsEngine\test\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'RPMUtil\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'psaCache\test\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING),
              (r'psaCache\CMakeLists.txt', REMOVE_INCREMENTAL_LINKING), ]
    
    for cmake in cmakes:
        if (cmake[1] & FIX_BINARY_TYPE) == FIX_BINARY_TYPE:
            FixBinaryTypeInCMake(code_dir, cmake[0])
        if (cmake[1] & REMOVE_INCREMENTAL_LINKING) == REMOVE_INCREMENTAL_LINKING:
            DisableIncrementalLinkingInCMake(code_dir, cmake[0])
    return True


def UpdateSourceFiles(code_dir):
    file = ['PsFramework\any-gsetter-types.h',
            'PsFramework\atomic.h',
            'PsFramework\connectionimp.h',
            'PsFramework\connectionimp.cpp',
            'PsFramework\numtraits.cpp',
            'PsFramework\psdefs.h',
            'PsFramework\thread.cpp', ]
    
    with open(os.path.join(code_dir, 'PsFramework\any-gsetter-types.h')) as file:
        lines = file.readlines()
    
    if lines[34] == 'ANY_GSETTER_TYPE(int, int)' and lines[35] == 'ANY_GSETTER_TYPE(unsigned, unsigned)':
        lines[34] = '//' + line
        lines[35] = '//' + line
        
    with open(os.path.join(code_dir, 'PsFramework\any-gsetter-types.h'), 'w') as file:
        file.writelines(lines)
    
    if lines[93].strip() == 'return InterlockedIncrement(pValue);':
        lines[93] = '	return InterlockedIncrement(reinterpret_cast<long *>(pValue));'
    if lines[108].strip() == 'return InterlockedDecrement(pValue);':
        lines[108] = '	return InterlockedDecrement(reinterpret_cast<long *>(pValue));'
    if lines[124].strip() == 'return InterlockedExchange(pTarget, value);':    
        lines[124] = '	return InterlockedExchange(reinterpret_cast<long *>(pTarget), static_cast<long>(value));'
    if lines[151].strip() == 'return InterlockedExchangeAdd(pTarget, value);':
        lines[151] = '	return InterlockedExchangeAdd(reinterpret_cast<long *>(pTarget), static_cast<long>(value));'



if __name__ == '__main__':
    dev_dir = ParseArgs()
    code_dir = os.path.join(dev_dir, 'code')
    
    #UpdateExternalsTxt(os.path.join(code_dir, 'externals.txt'))
    ProcessCMakeFiles(code_dir)
    
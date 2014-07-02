import os, string, shutil, sys, win32api, win32file    
from .Utils import *

def IsFileInDepot( file ):
    command = 'p4 files ' + file
    lines = os.popen4( command, 't' )[1].readlines()
    return lines[0].find( 'no such file' ) == -1 and lines[0].find( ' - delete change ' ) == -1


def IsReadOnly( file ):
    return win32api.GetFileAttributes( file ) & win32file.FILE_ATTRIBUTE_READONLY != 0


def SetAttributes( dir, openedFiles ):
    print('Searching for files in ' + dir)
    dirs = []
    
    regex = re.compile( r'^.*\.(?:c|cpp|h|hpp|inl)$', re.I )
    for root, dirs, files in os.walk( dir ):
        for file in files:
            pathname = os.path.join( root, file )
            if regex.match(pathname) and not IsReadOnly( pathname ) and IsFileInDepot( pathname ) and not pathname.lower() in openedFiles:
                win32api.SetFileAttributes( file, win32file.FILE_ATTRIBUTE_READONLY )
                print('Setting file ' + file + ' to be read-only')


def GetOpenedFiles( dir, sandbox ):
    command = 'p4 opened %s\\...' % dir
    output = os.popen4( command, 't' )[1].read()
    files = []

    pattern = '//\w+/\w+/\w+/(?P<ComponentName>\w+)/\w+/(?P<Path>[^#]*)#[- \w]*(edit|add).*'
    for iter in re.finditer( pattern, output ):
        component = iter.group( 'ComponentName' )
        subpath = iter.group( 'Path' )
        name = os.path.normpath( os.path.join( sandbox, 'ws', component,  subpath ) )
        CHECK( os.path.exists( name ), 'File \'%s\' is opened for edit but doesn\'t exist.' % name )
        files.append( name.lower() )
        
    return files
    
    
if __name__ == '__main__':
    dir = os.getcwd()
    openedFiles = GetOpenedFiles(dir, FindSandbox(dir))
    SetAttributes( dir, openedFiles )
            
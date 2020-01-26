import os, sys, re, Perforce, Utils
import win32api, win32file

def IsFileWritable( file ):
    return win32api.GetFileAttributes( file ) & win32file.FILE_ATTRIBUTE_READONLY == 0

def IsFileOpened( name ):
    return IsFileWritable(name) and Perforce.IsFileInDepot(name)

if __name__ == '__main__':
    dir = os.getcwd()
    files = Perforce.GetOpenedFiles( dir, Utils.FindSandbox(dir) )
    for i in range( len(files) ):
        files[i] = files[i].lower()

    for name in Utils.RecurseDirectory( dir, IsFileOpened ):
        if not name.lower() in files:
            attribs = win32api.GetFileAttributes( name )
            win32api.SetFileAttributes( name, attribs | win32file.FILE_ATTRIBUTE_READONLY )
            print(('Resetting read-only on the file %s.' % name))

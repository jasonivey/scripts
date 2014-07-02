import os, sys, shutil, re, Perforce
from Utils import *
#import win32api, win32file


def PrintHeader( file ):
    file.write( 'Copy Opened Files.py - Version 1.00\n' )


def PrintHelp():
    print('\nCopy all of the perforce files opened for edit to the directory specified.')
    print('\nUsage:')
    print('\tCopyOpenedFiles.py {-backup <output directory> [-dontrevert] [-except <files>] | -restore <input directory>}\n')
    
    print('\tSpecify either the \'-backup\' or the \'-restore\' switch')
    print('\tto tell the script where to backup or restore the files.')
    print('\tThe \'-dontrevert\' switch tells the script not to revert')
    print('\tall the opened files after copying them to the specified')
    print('\tdirectory.')
    print('\tThe \'-except\' switch provides a list of files (base')
    print('\tnames only) deliminated by a space for the backup to')
    print('\tnot copy and revert.')


def MakeRecursiveDir( dir ):
    parts = dir.split( os.path.sep )
    current = ''
    i = 0
    while i < len( parts ):
        if i == 0:
            current = parts[i] + os.path.sep
        else:
            path = os.path.join( current, parts[i] )            
            if not os.path.isdir( path ):
                os.mkdir( path )
            current = path
        i = i + 1


def CreateDestination(dir):
    if os.path.exists( dir ):
        if len( os.listdir(dir) ):
            print('Destination directory, %s must not exist or be empty.' % dir)
            sys.exit(1)
    else:
        os.mkdir( dir )


def CopyDifferences(perforce, src, dst):
	output = perforce.GetDifferences( src )
	name = os.path.splitext(dst)[0] + '.diff'
	file = open(name, 'w')
	file.write(output)
	file.close()


def CopyOpenedFile( perforce, src, sandbox, dir, include_diff ):
    basename = os.path.basename( src )
    begin = src.find( sandbox ) + len( sandbox ) + 1
    if file[begin] == os.path.sep:
        begin += 1
    end = len( src ) - len( basename )
    dst = os.path.join( dir, file[begin:end] )
    MakeRecursiveDir( dst )                
    shutil.copy( src, dst )
    if include_diff:
        CopyDifferences(perforce, src, os.path.join(dst, basename))
    print('Copied %s to %s successfully' % ( src, dst ))


def CopyFileToWorkspace( perforce, src, dir, sandbox ):
    begin = src.find( dir ) + len( dir ) + 1
    dst = os.path.join( sandbox, src[begin:] )
    CHECK( os.path.exists( dst ), 'The source file, %s, must exist in the sandbox' % dst )
    #perforce.OpenForEdit( dst )
    CHECK( perforce.OpenForEdit( dst ), 'Error while opening the file, %s, for edit' % dst )
    shutil.copyfile( src, dst )
    print('Copied %s to %s successfully' % ( src, dst ))


def ParseArgs( argv ):
    dir = ''
    revert = True
    backup = False
    restore = False
    change = None
    exceptions = []
    i = 1
    count = len( argv )

    while i < count:
        if IsSwitch(argv[i]) and ( argv[i][1:].lower().startswith('r') or argv[i][1:].lower().startswith('b') ) and i + 1 < count:
            restore = argv[i].lower().startswith( '-r' )
            backup = argv[i].lower().startswith( '-b' )
            i = i + 1
            dir = argv[i]
        elif IsSwitch(argv[i]) and argv[i][1:].lower().startswith('e') and i + 1 < count:
            looping = True
            while looping:
                if i + 1 < count and not argv[i + 1].lower().startswith( '-' ):
                    i = i + 1
                    exceptions.append( argv[i].lower() )
                else:
                    looping = False
        elif IsSwitch(argv[i]) and argv[i][1:].lower().startswith('d'):
            revert = False
        elif IsSwitch(argv[i]) and argv[i][1:].lower().startswith('c') and i + 1 < count:
            i = i + 1
            change = int( argv[i] )
        i = i + 1
    
    if dir == '':
        PrintHelp()
        sys.exit(2)
    elif ( not backup and not restore ) or ( backup and restore ):
        PrintHelp()
        sys.exit(2)        
        
    return os.path.normpath( os.path.abspath(dir) ), backup, change, restore, revert, exceptions


#def IsNotReadOnly( file ):
#    return win32api.GetFileAttributes( file ) & win32file.FILE_ATTRIBUTE_READONLY == 0

if __name__ == '__main__':

    PrintHeader( sys.stdout )
    
    dir, backup, change, restore, revert, exceptions = ParseArgs( sys.argv )
    sandbox = FindSandbox( os.getcwd() )
    perforce = Perforce.Perforce()
    
    if backup:
        CreateDestination( dir )
        if change:
            files = perforce.GetChangeListFiles( change, os.getcwd(), sandbox )
        else:
            files = perforce.GetOpenedFiles( os.getcwd(), sandbox )
        for file in files:
        #for file in RecurseDirectory( os.getcwd(), IsNotReadOnly ):
            if file.lower() not in exceptions:
                CopyOpenedFile( perforce, file, sandbox, dir, False )
                if revert:
                    perforce.Revert(file)
    else:
        for file in RecurseDirectory(dir):
            if not file.lower().endswith('.diff'):
                CopyFileToWorkspace( perforce, file, dir, sandbox )

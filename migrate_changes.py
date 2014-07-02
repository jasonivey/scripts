#! /usr/bin/python
# migrateChanges.py

import os, sys, zipfile
import difflib

INDEX_FILE = ".p4_fileInfo.txt"

def p4opened( sandbox=None ):
    if sandbox is not None:
        currDir = os.getcwd()
        os.chdir( sandbox )
        
    output = os.popen( 'p4 opened' ).read().strip()
    
    if sandbox is not None:
        os.chdir( currDir )
    
    lines = output.split('\n')
    openedFiles = {'edit':[], 'add':[], 'delete':[]}
    if len(output) == 0:
        return openedFiles

    for line in lines:
        openFile = line.split('#')[0]
        openType = line.split('-')[-1].split(' ')[1]
        try:
            openedFiles[openType].append( openFile )
        except:
            openedFiles[openType] = [ openFile ]
        
    return openedFiles

def p4where( file, sandbox=None ):
    if sandbox is not None:
        currDir = os.getcwd()
        os.chdir( sandbox )
    
    output = os.popen( 'p4 where %s' % file ).read().strip()
    
    if sandbox is not None:
        os.chdir( currDir )
    
    result = output.split(' ')
    if len( result ) == 3:
        return tuple(result)
    elif len( result ) % 2 == 0 and len( result ) % 3 == 0:
        sliceLen = len( result ) / 3
        return ( " ".join(result[ :sliceLen ]), " ".join(result[sliceLen:-sliceLen]), " ".join(result[-sliceLen:]) )
    else:
        raise Exception( "File not in sandbox" )
        
        raw_input( 'What do I do with <<%s>>?' % repr( result ) )
    return ( result[0], " ".join(result[1:-1]), result[-1] )
    
def p4edit( file, sandbox=None ):
    if sandbox is not None:
        currDir = os.getcwd()
        os.chdir( sandbox )
        
    ret = os.system( 'p4 edit %s' % file )
        
    if sandbox is not None:
        os.chdir( currDir )
    
    return ret

def p4add( file, sandbox=None ):
    if sandbox is not None:
        currDir = os.getcwd()
        os.chdir( sandbox )
        
    ret = os.system( 'p4 add %s' % file )
    
    if sandbox is not None:
        os.chdir( currDir )
        
    return ret

def p4delete( file, sandbox=None ):
    if sandbox is not None:
        currDir = os.getcwd()
        os.chdir( sandbox )
        
    ret = os.system( 'p4 delete %s' % file )
    
    if sandbox is not None:
        os.chdir( currDir )
        
    return ret

def checkoutFiles( fileInfo, sandbox=None ):
    for file in fileInfo:
        if not fileInfo[file].has_key('type'):
            print "This zip was created with an old revision of migrateChanges!"
            fileInfo[file]['type'] = "edit"
        if fileInfo[file]['type'] == "edit":
            p4edit( fileInfo[file]['p4path'], sandbox )
        elif fileInfo[file]['type'] == "add":
            #p4add( fileInfo[file]['destpath'], sandbox )
            print "%s will be added after the zip is extracted" % file
        elif fileInfo[file]['type'] == "delete":
            p4delete( fileInfo[file]['destpath'], sandbox )
        else:
            print "p4%s action is not supported" % fileInfo[file]['type']
            
def addNewFiles( fileInfo, sandbox=None ):
    for file in fileInfo:
        if fileInfo[file].has_key('type') and fileInfo[file]['type'] == "add":
            p4add( fileInfo[file]['destpath'], sandbox )

def markFilesAlreadyCheckedOut( fileInfo, zipFileName, sandbox=None ):
    filesOpened = p4opened( sandbox )
    
    for fileType in filesOpened:
        for file in filesOpened[fileType]:
            if file in fileInfo.keys():
                selection = 3
                while selection == 3:
                    print "%s is already opened in this sandbox." % file
                    print "What would you like to do?"
                    print "    1) Keep the version in this sandbox"
                    print "    2) Use the version from the zip file"
                    print "    3) Show me a diff, then I'll decide"
                    print "    4) Abort.  I need to resolve this manually before"
                    print "           I can migrate this changes zip file."
                    
                    try:
                        selection = int( raw_input( "Your Selection(1-4): " ) )
                    except:
                        selection = "Bad Input"
                        
                    if selection == 1:
                        fileInfo[file]['destpath'] = None
                    elif selection == 2:
                        pass
                    elif selection == 3:
                        differ = difflib.Differ()
                        zipFile = zipfile.ZipFile( zipFileName, 'r', zipfile.ZIP_DEFLATED )
                        fileA = open( fileInfo[file]['destpath'], 'r' ).readlines()
                        fileB = zipFile.read( fileInfo[file]['zippath'] ).split('\n')
                        for item in differ.compare( fileA, fileB ):
                            print item.strip()
                    elif selection == 4:
                        print "Aborting."
                        sys.exit(0)
                    else:
                        print "I did not understand that input, try again."
                        selection = 3
                        
    return fileInfo

def makeZip( fileInfo, zipFileName ):
    if os.path.isfile( zipFileName ):
        zipFile = zipfile.ZipFile( zipFileName, 'a', zipfile.ZIP_DEFLATED )
    else:
        zipFile = zipfile.ZipFile( zipFileName, 'w', zipfile.ZIP_DEFLATED )
        
    for file in fileInfo:
        if fileInfo[file].has_key('type') and fileInfo[file]['type'] != "delete":
            if os.path.isfile( fileInfo[file]['sourcepath'] ):
                zipFile.write( fileInfo[file]['sourcepath'], fileInfo[file]['zippath'] )
            else:
                print "File %s (opened for %s) does not exist and will not be in the zip file" % ( fileInfo[file]['sourcepath'], fileInfo[file]['type'] )
        
    zipFile.writestr( INDEX_FILE, repr(fileInfo) )
        
    zipFile.close()

def extractZip( fileInfo, zipFileName ):
    zipFile = zipfile.ZipFile( zipFileName, 'r', zipfile.ZIP_DEFLATED )
    for file in fileInfo:
        if not fileInfo[file]['type'] == "delete":
            try:
                if not os.path.isdir( os.path.dirname( fileInfo[file]['destpath'] ) ):
                    os.makedirs( os.path.dirname( fileInfo[file]['destpath'] ) )
                fileHandle = open( fileInfo[file]['destpath'], 'wb' )
                fileHandle.write( zipFile.read( fileInfo[file]['zippath'] ) )
                fileHandle.close()
            except:
                print "Error reading %s from zip, assuming it was never included" % fileInfo[file]['zippath']
    zipFile.close()
    
def getFileInfo( file, sandbox, type, zipPaths ):
    fileInfo = {}
    fileWhere = p4where( file, sandbox )
    
    fileInfo['p4path'] = fileWhere[0]
    fileInfo['sbpath'] = fileWhere[1]
    fileInfo['sourcepath'] = fileWhere[2]
    fileInfo['type'] = type
    if sandbox is not None:
        fileInfo['sbroot'] = sandbox
    else:
        fileInfo['sbroot'] = os.getcwd()
    
    basePath = fileWhere[2].split( os.sep )[-1]
    zipPath = basePath
    i = 0
    while zipPath in zipPaths:
        zipPath = '%s.%i' % ( basePath, i )
        i += 1
    zipPaths.append( zipPath )
    fileInfo['zippath'] = zipPath
    
    return fileInfo
    
def createFileInfo( sandbox=None ):
    fileInfo = {}
    
    zipPaths = []
    openedFiles = p4opened( sandbox )
    for fileType in openedFiles:
        for file in openedFiles[fileType]:
            fileInfo[file] = getFileInfo( file, sandbox, fileType, zipPaths )
        
    return fileInfo

def readFileInfo( changeFileName, sandbox=None ):
    fileInfo = {}
    
    try:
        zipFile = zipfile.ZipFile( changeFileName, 'r', zipfile.ZIP_DEFLATED )
        fileInfoStr = zipFile.read( INDEX_FILE )
        zipFile.close()
        fileInfo = eval( fileInfoStr )
    except:
        print "This is not a valid change migration zip file."
        raise AssertionError( "Invalid change migration zip file", changeFileName )
    
    for file in fileInfo:
        try:
            fileInfo[file]['destpath'] = p4where( fileInfo[file]['p4path'], sandbox )[2]
        except:
            if sandbox is not None:
                fileInfo[file]['destpath'] = fileInfo[file]['sourcepath'].replace( fileInfo[file]['sbroot'], sandbox )
            else:
                fileInfo[file]['destpath'] = fileInfo[file]['sourcepath'].replace( fileInfo[file]['sbroot'], os.getcwd() )
    
    return fileInfo
    

def createChangeFile( changeFileName, sandbox=None ):
    fileInfo = createFileInfo( sandbox )
    makeZip( fileInfo, changeFileName )

def extractChangeFile( changeFileName, sandbox=None ):
    fileInfo = readFileInfo( changeFileName, sandbox )
    fileInfo = markFilesAlreadyCheckedOut( fileInfo, changeFileName, sandbox )
    checkoutFiles( fileInfo, sandbox )
    extractZip( fileInfo, changeFileName )
    addNewFiles( fileInfo, sandbox )

if __name__ == "__main__":
    if len( sys.argv ) != 3 and len( sys.argv ) != 5:
        print "Usage:"
        print "    To create a changes zipfile to migrate: migrateChanges.py -c <new zip file name>"
        print "    To extract a changes zipfile to your sandbox: migrateChanges.py -x <existing zip file name>"
        print "    There is a parameter -s to specify the sandbox directory if it is different from your current directory"
        
    elif len( sys.argv ) == 3:
        if sys.argv[1] == '/c' or sys.argv[1] == '-c':
            createChangeFile( sys.argv[2] )
        elif sys.argv[1] == '/x' or sys.argv[1] == '-x':
            extractChangeFile( sys.argv[2] )
    
    elif len( sys.argv ) == 5:
        if (sys.argv[1] == '/c' or sys.argv[1] == '-c') and (sys.argv[3] == '/s' or sys.argv[3] == '-s'):
            createChangeFile( sys.argv[2], sys.argv[4] )
        elif (sys.argv[1] == '/x' or sys.argv[1] == '-x') and (sys.argv[3] == '/s' or sys.argv[3] == '-s'):
            extractChangeFile( sys.argv[2], sys.argv[4] )
        elif (sys.argv[3] == '/c' or sys.argv[3] == '-c') and (sys.argv[1] == '/s' or sys.argv[1] == '-s'):
            createChangeFile( sys.argv[2], sys.argv[4] )
        elif (sys.argv[3] == '/x' or sys.argv[3] == '-x') and (sys.argv[1] == '/s' or sys.argv[1] == '-s'):
            extractChangeFile( sys.argv[2], sys.argv[4] )


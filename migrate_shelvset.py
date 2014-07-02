#!/usr/bin/env python

import os
import sys
import datetime
import Tfs

# Important Note: This script makes the assmption that there is only one local 
#                 mapping per branch on a particular computer.  For example if
#                 there are two local mappings to the $/Boston/Main/Source/EV/Vault
#                 source repository pointing to two different locations and you
#                 attempt to migrate a shelveset from another branch into Boston
#                 I'm not sure which mapping it will choose. (I'm guessing the
#                 first one you created.)

def ParseArgs(args):
    #source = None
    destination = os.getcwd()
    shelveset = None
    i = 1
    
    while i < len(args):
        # source branch mapping -- i.e. $/Boston/Main/Source/EV/Vault
        #if (args[i].startswith('-') or args[i].startswith('/')) and args[i][1:].startswith('s') and i + 1 < len(args):
        #    i += 1
        #    source = args[i]
        #    if not source.endswith('/'):
        #        source += '/'
            
        # destination branch mapping -- i.e. $/Prototypes/Dev/Casablanca/ArchiveAllContent/Source/EV/Vault
        if (args[i].startswith('-') or args[i].startswith('/')) and args[i][1:].startswith('d') and i + 1 < len(args):
            i += 1
            destination = args[i]

        # shelveset branch mapping -- i.e. "Some shelveset in quotes most likely"
        if (args[i].startswith('-') or args[i].startswith('/')) and args[i][1:].startswith('n') and i + 1 < len(args):
            i += 1
            shelveset = args[i]

        # Print all shelvset names
        if (args[i].startswith('-') or args[i].startswith('/')) and args[i][1:].startswith('p'):
            print( '\n'.join(Tfs.CmdTfs().GetShelvesetNames()) )
            sys.exit()

        i += 1

    destination = os.path.abspath(destination)
    if not destination.endswith('\\'):
        destination += '\\'
        
    if not os.path.isdir(destination):
        print('ERROR: Please specify the root of the destination TFS mapping!')
        sys.exit()

    if shelveset == None:
        print('ERROR: Please specify a shelvset name (usually needs quotes)!')
        sys.exit()
    
    return destination, shelveset


def BuildReverseDir(parts, index):
    newParts = parts[: index]
    newParts.reverse()
    return '\\'.join(newParts)


def GetSourceServerPath(items, destDir):
    # Find one which we should be able to find in the local file system
    found = False
    for i, item in enumerate(items):
        if item[1] != 'add':
            found = True
            break
    assert(found)
    
    # Now find it in the local file system and keep track of how many directories we traverse
    src = items[i][0]
    parts = src.split('/')
    parts.reverse()
    filename = parts[0]
    parts = parts[1:]
    dst = None
    for index, part in enumerate(parts):
        currDir = os.path.abspath(os.path.join(destDir, part, BuildReverseDir(parts, index)))
        dst = os.path.abspath(os.path.join(currDir, filename))
        if os.path.isfile(dst):
            tempParts = parts[index + 1:]
            tempParts.reverse()
            sourceServerPath = '/'.join(tempParts)
            return sourceServerPath + '/'
    assert(False)

    
def GetDestinationFilename(src, srcServerDir, destLocalDir):
    return os.path.abspath(src.replace(srcServerDir, destLocalDir))

    
def MigrateFiles(items, srcServerDir, destLocalDir, shelveset):
    for item in items:
        src = item[0]
        type = item[1]
        dst = GetDestinationFilename(src, srcServerDir, destLocalDir)
        print('Migrating %s' % src)
        
        if type == 'edit':
            Tfs.CmdTfs().Checkout(dst)
            with open(dst, 'w') as file:
                data = Tfs.CmdTfs().GetFileData(src, shelveset)
                file.write(data)
        elif type == 'add':
            with open(dst, 'w') as file:
                data = Tfs.CmdTfs().GetFileData(src, shelveset)
                file.write(data)
            Tfs.CmdTfs().Add(dst)
        elif type == 'delete':
            Tfs.CmdTfs().Delete(dst)
            
    return None


if __name__ == '__main__':
    beginTime = datetime.datetime.now()
    print('Started                 :  ' + beginTime.strftime( '%I:%M:%S %p' ))

    try:
        destination, shelveset = ParseArgs(sys.argv)
        shelvesetFiles = Tfs.CmdTfs().GetShelvesetFiles(shelveset)
        source = GetSourceServerPath(shelvesetFiles, destination)
        MigrateFiles(shelvesetFiles, source, destination, shelveset)
    finally:    
        endTime = datetime.datetime.now()
        print('Finished                :  ' + endTime.strftime( '%I:%M:%S %p' ))
        elapsed = endTime - beginTime
        hours = int( elapsed.seconds / 3600 )
        minutes = int( ( elapsed.seconds % 3600 ) / 60 )
        seconds = int( ( elapsed.seconds % 3600 ) % 60 )
        print('Total time for operation:  %02d:%02d:%02d:%03d' % ( hours, minutes, seconds, elapsed.microseconds / 1000 ))

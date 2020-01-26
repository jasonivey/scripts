import os, string, shutil, sys
from stat import *

def CompareIgnoreCase( x, y ):
    return cmp( x.lower(), y.lower() )

def RecurseDirectory( srcDir, files ):
    dirs = []
    
    for f in os.listdir( srcDir ):
        if f.find( '?' ) != -1 or \
           f.find( 'System Volume Information' ) != -1:
            continue

        pathname = '%s\\%s' % ( srcDir, f )
        
        if os.path.isdir( pathname ):
            dirs.append( pathname )
        elif f.endswith('.vcproj'):
            files.append( pathname )

    for d in dirs:
        RecurseDirectory( d, files )


def CheckoutFiles( files ):
    for f in files:
        if os.path.exists( f ):
            print('CHECKING OUT ' + f.upper())
            os.system( 'p4 edit ' + f )
            RemoveWin64Configuration( f )
        else:
            print('ERROR: File Not Found ' + f)


def RemoveWin64Configuration( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()
    file = open( filename, 'w' )
    
    bInsideConfig = False
    bFoundConfig = False
    bFoundFileConfig = False
    
    for line in lines:
##        file.write( line.replace( 'Amd64', 'x64' ) )
        if line.strip().upper() == '<CONFIGURATION':
            bFoundConfig = True
            
        elif line.strip().upper() == '<FILECONFIGURATION':
            bFoundFileConfig = True
            
        elif( bFoundConfig or bFoundFileConfig ) and \
             ( line.strip().upper() == 'NAME="WIN64 RELEASE|WIN32"' or \
               line.strip().upper() == 'NAME="WIN64 DEBUG|WIN32"' ):
            bInsideConfig = True
            bFoundConfig = False
            bFoundFileConfig = False
            
        elif bInsideConfig and \
             ( line.strip().upper() == '</CONFIGURATION>' or \
               line.strip().upper() == '</FILECONFIGURATION>' ):
            bInsideConfig = False

        elif bInsideConfig:
            continue
        
        elif bFoundConfig:
            file.write( '\t\t<Configuration\n' )
            file.write( line )
            bFoundConfig = False
            
        elif bFoundFileConfig:
            file.write( '\t\t\t\t<FileConfiguration\n' )
            file.write( line )
            bFoundFileConfig = False
            
        else:
            file.write( line )
        
    file.close()


if __name__ == '__main__':
    if len( sys.argv ) > 1:
        dir = sys.argv[1]
    else:
        dir = os.getcwd()

    files = []
    RecurseDirectory( dir, files )
    CheckoutFiles( files )
        
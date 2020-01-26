import os, string, shutil, sys, Perforce
from stat import *
from .Utils import RecurseDirectory


def IsProjectFile(file):
    return not re.search('wsfiles', file, re.I) and re.match('^.*\.vcproj$', file, re.I)


def UpdateVCProj( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()

    basename = filename[ filename.rfind( '\\' ) + 1 : len( filename ) ]

    if Perforce.OpenForEdit( filename ) == False:
        return                
    
    print(('Processing file "' + basename + '"'))
    file = open( filename, 'w' )
    
    insideConfig = False
    insideFileConfig = False
    insideWin64 = False
    
    for line in lines:
        
        if line.strip().lower() == '<configuration':
            insideConfig = True
            
        elif line.strip().lower() == '<fileconfiguration':
            insideFileConfig = True
            
        elif( insideConfig or insideFileConfig ) and \
             line.strip().lower().find( 'name="win64' ) != -1:
            insideWin64 = True
            insideConfig = False
            insideFileConfig = False

        elif insideWin64 and \
             ( line.strip().lower() == '</configuration>' or \
               line.strip().lower() == '</fileconfiguration>' ):
            insideWin64 = False
            insideConfig = False
            insideFileConfig = False                

        elif insideWin64:
            continue
        
        elif insideConfig or insideFileConfig:
            if insideConfig:
                file.write( '\t\t<Configuration\n' )
                insideConfig = False
            elif insideFileConfig:
                file.write( '\t\t\t\t<FileConfiguration\n' )
                insideFileConfig = False
                
            if line.strip().find( 'x64' ):
                line = line.replace( 'x64', 'Win64-x64' )
                
            file.write( line )

        elif not insideWin64 and line.strip().find( 'x64' ):
            line = line.replace( 'x64', 'Win64-x64' )
            file.write( line )
            
        else:
            file.write( line )
        
    file.close()


if __name__ == '__main__':
    if len( sys.argv ) > 1:
        dir = sys.argv[1]
    else:
        dir = os.getcwd()

    for file in RecurseDirectory( dir, IsProjectFile ):
        UpdateVCProj( file )
        
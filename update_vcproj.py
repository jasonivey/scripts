import os, sys, Perforce
from .Utils import RecurseDirectory


def IsProjectFile( file ):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)


def UpdateVCProj( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()

    basename = filename[ filename.rfind( '\\' ) + 1 : len( filename ) ]
    if basename.lower().startswith( 'z_' ):
        return

    if Perforce.OpenForEdit( filename ) == False:
        return                
    
    print(('Processing file "' + basename + '"'))
    file = open( filename, 'w' )
    
    bInsideConfig = False
    bFoundConfig = False
    release = False
    bInsideCompilerTool = False
    bInsideLinkerTool = False
    bInsideLibrarianTool = False
    foundCompilerOptimizations = False
    foundLinkerOptimizations = False
    foundLibrarianOptimizations = False
    
    for line in lines:

        if bFoundConfig == False and line.strip().upper() == '<CONFIGURATION':
            #print 'Found a configuration section'
            file.write( line )
            bFoundConfig = True
            
        elif bFoundConfig and line.strip().upper().startswith( 'NAME="' ):
            file.write( line )
            if line.strip().upper() == 'NAME="RELEASE|WIN32"':
                #print 'Found the release win32 configuration section'
                bInsideConfig = True
            else:
                #print 'Not a valid configuration section'
                bInsideConfig = False
            bFoundConfig = False
            
        elif bInsideConfig and line.strip().upper() == '</CONFIGURATION>':
            file.write( line )
            release = False
            bInsideCompilerTool = False
            bInsideLinkerTool = False
            bInsideConfig = False
            bInsideLibrarianTool = False

        elif bInsideConfig and line.strip() == 'Name="VCLinkerTool"':
            #print 'Found begin of linker tool'
            file.write( line )
            bInsideLinkerTool = True
            bInsideCompilerTool = False
            bInsideLibrarianTool = False            
            
        #elif bInsideConfig and bInsideLinkerTool and \
        #     line.strip().startswith( 'LinkIncremental=' ):
        #    #print 'Found LinkIncremental in linker tool'
        #    if line.strip().endswith( '"2"' ):
        #        line = line.replace( '2', '1' )
        #    file.write( line )

        elif bInsideConfig and bInsideLinkerTool and \
             line.strip().startswith( 'LinkTimeCodeGeneration=' ):
            #print 'Removing LinkTimeCodeGeneration in linker tool'
            #file.write( line )
            foundLinkerOptimizations = True

        elif bInsideConfig and bInsideLinkerTool and line.strip().find( '/>' ) != -1:
            #print 'Found end of linker tool'
            if foundLinkerOptimizations == False:
                print('Didn\'t find any linker optimizations')
            #    file.write( '\t\t\t\tLinkTimeCodeGeneration="1"\n' )
            file.write( line )
            bInsideCompilerTool = False
            bInsideLinkerTool = False

        elif bInsideConfig and line.strip() == 'Name="VCLibrarianTool"':
            #print 'Found begin of compiler tool'
            file.write( line )
            bInsideCompilerTool = False
            bInsideLinkerTool = False
            bInsideLibrarianTool = True
            
        elif bInsideConfig and bInsideLibrarianTool and \
             line.strip().startswith( 'AdditionalOptions=' ):
            #print 'Found LinkTimeCodeGeneration in librarian tool'
            if line.strip().upper().find( '/LTCG' ) == -1:
                print('Didn\'t find LinkTimeCodeGeneration in librarian tool additional options')
                file.write( line )
            else:
                if line.strip().upper().find( ' /LTCG' ) != -1:
                    line = line.replace(' /LTCG', '')
                    file.write( line )
                #    print line
                #else:
                #    print 'AdditionalOptions="/LTCG" removed'
                foundLibrarianOptimizations = True
            
        elif bInsideConfig and bInsideLibrarianTool and line.strip().find( '/>' ) != -1:
            #print 'Found end of librarian tool'
            if foundLibrarianOptimizations == False:
                print('Didn\'t find any librarian optimizations')
            #    file.write( '\t\t\t\tAdditionalOptions="/LTCG"\n' )
            file.write( line )
            bInsideCompilerTool = False
            bInsideLinkerTool = False
            bInsideLibrarianTool = False

        elif bInsideConfig and line.strip() == 'Name="VCCLCompilerTool"':
            #print 'Found begin of compiler tool'
            file.write( line )
            bInsideCompilerTool = True
            bInsideLinkerTool = False
            bInsideLibrarianTool = False
            
        elif bInsideConfig and bInsideCompilerTool and \
             line.strip().startswith( 'WholeProgramOptimization=' ):
            #print 'Removing WholeProgramOptimization in compiler tool'
            #print 'Found WholeProgramOptimization in compiler tool'
            #file.write( line )
            foundCompilerOptimizations = True
            
        elif bInsideConfig and bInsideCompilerTool and line.strip().find( '/>' ) != -1:
            #print 'Found end of compiler tool'
            if foundCompilerOptimizations == False:
                print('Didn\'t find WholeProgramOptimization in the compiler tool')
                #file.write( '\t\t\t\tWholeProgramOptimization="true"\n' )
            file.write( line )
            bInsideCompilerTool = False
            bInsideLinkerTool = False
            bInsideLibrarianTool = False
        
        #if line.strip().lower().startswith( 'additionalincludedirectories' ) and \
        #   line.lower().find( 'boost' ) == -1 and \
        #   line.lower().find( 'vs.net' ) != -1:
        #    index = line.lower().find( 'vs.net' )
        #    addition = ';' + line[ line.rfind( ';', 0, index ) + 1 : index ] + 'Boost'
        #    line = line[ 0 : line.rfind('"') ] + addition + line[ line.rfind('"') : len( line ) ]
        #    file.write( line )
        #    print line.strip()
        
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
        
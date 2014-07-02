import os, string, shutil, sys, re
from stat import *
from .Utils import RecurseDirectory


def IsProjectFile( file ):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)


def UpdateX64Configuration( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()
    file = open( filename, 'w' )
    
    bInsideConfig = False
    bFoundConfig = False
    bX64Release = False
    bX64Debug = False
    bInsideCompilerTool = False
    
    for line in lines:

        if line.strip().upper() == '<CONFIGURATION':
            file.write( line )
            bFoundConfig = True
            
        elif bFoundConfig and \
             ( line.strip().upper() == 'NAME="RELEASE|X64"' or \
               line.strip().upper() == 'NAME="DEBUG|X64"' ):
            if line.strip().upper() == 'NAME="RELEASE|X64"':
                bX64Release = True
            elif line.strip().upper() == 'NAME="DEBUG|X64"':
                bX64Debug = True
            file.write( line )
            bInsideConfig = True
            bFoundConfig = False
            
        elif bInsideConfig and line.strip().upper() == '</CONFIGURATION>':
            file.write( line )
            bX64Release = False
            bX64Debug = False
            bInsideConfig = False

        elif bInsideConfig and line.strip() == 'Name="VCCLCompilerTool"':
            file.write( line )
            bInsideCompilerTool = True

        elif bInsideConfig and bInsideCompilerTool and line.strip() == '/>':
            file.write( line )
            bInsideCompilerTool = False
            
        elif bInsideConfig and bInsideCompilerTool and \
             line.strip().startswith( 'PreprocessorDefinitions=' ):
            file.write( '%s;WIN64"\n' % line.rstrip()[ 0 : len(line.rstrip()) - 1 ] )
            
        elif bInsideConfig and \
             ( line.strip() == 'OutputDirectory="$(PlatformName)\\$(ConfigurationName)"' or \
               line.strip() == 'IntermediateDirectory="$(PlatformName)\\$(ConfigurationName)"' ):
            if bX64Release:
                file.write( line.replace( '$(PlatformName)\\$(ConfigurationName)', '.\\x64_release' ) )
            elif bX64Debug:
                file.write( line.replace( '$(PlatformName)\\$(ConfigurationName)', '.\\x64_debug' ) )

        elif bInsideConfig and line.find( '".\\win32_' ) != -1:
            file.write( line.replace( '".\\win32_', '".\\x64_' ) )
    
        elif bFoundConfig:
            file.write( line )
            bFoundConfig = False
            
        else:
            file.write( line )
        
    file.close()


if __name__ == '__main__':
    if len( sys.argv ) > 1:
        dir = sys.argv[1]
    else:
        dir = os.getcwd()

    for file in RecurseDirectory( dir, IsProjectFile ):
        UpdateX64Configuration( file )
        
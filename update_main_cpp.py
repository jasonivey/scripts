import os, sys, Perforce
from .Utils import RecurseDirectory


def IsMainCpp(file):
    return os.path.dirname(file).lower().endswith('test') and file.lower().endswith('main.cpp')


def UpdateMainCpp( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()

    if Perforce.OpenForEdit( filename ) == False:
        return                
    
    print(('Processing file "' + filename + '"'))
    file = open( filename, 'w' )
    updated = False
    deleteBlankSpaces = False
    foundUnitMain = False
    
    for line in lines:
        
        if not updated and line.strip().lower() == '#include "base/dev/cppunit/cppunitmain.h"':
            file.write( '#define _CRTDBG_MAP_ALLOC\n' )
            file.write( '#include <stdlib.h>\n' )
            file.write( '#include <crtdbg.h>\n' )
            file.write( line )
            foundInclude = True
        
        elif not updated and deleteBlankSpaces and line.strip() == '':
            continue
        
        elif not updated and deleteBlankSpaces and line.strip().lower() == 'int main( int argc, char * argv[] )':
            file.write( line )
            deleteBlankSpaces = False
            continue
        
        elif not updated and line.strip().lower() == '#include "base/dev/timing.h"':
            file.write( line + '\n' )
            deleteBlankSpaces = True
            
        #elif foundInclude and line.strip() == '':
        #    file.write( '#include "Base/Dev/Timing.h"\n' )
        #    file.write( line )
        #    foundInclude = False
            
        elif line.strip().lower().find( '_crtdbg_map_alloc' ) != -1 or \
             line.strip().lower().startswith( '_crtsetdbgflag' ):
            file.write( line )
            updated = True
        
        elif not updated and line.strip().lower() == 'cleartimers(log_if_data, "before testrunner");':
            if not foundUnitMain:
                file.write( '\t_CrtSetDbgFlag( _CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF );\n\n' )
            else:
                line = line.replace( 'Before', 'After' )
                foundUnitMain = False
            file.write( line )
            
        elif not updated and line.strip().lower() == 'cppunitmain( argc, argv );':
            file.write( line )
            foundUnitMain = True
            
        #elif not updated and line.strip().lower() == 'return 0;':
        #    file.write( '\tClearTimers(LOG_IF_DATA, "Before TestRunner");\n' )
        #    file.write( '\tg_pTimingManager->PreserveTransientTimers();\n' )
        #    file.write( line )
            
        else:
            file.write( line )
        
    file.close()


if __name__ == '__main__':
    if len( sys.argv ) > 1:
        dir = sys.argv[1]
    else:
        dir = os.getcwd()

    for file in RecurseDirectory( dir, IsMainCpp ):
        UpdateMainCpp( file )
        
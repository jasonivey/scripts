import os, string, shutil, re
from stat import *

def FindVsErrors( filename ):
    infile = file( filename, 'r' )
    lines = infile.readlines()
    infile.close()

    reErrorsAndWarnings = re.compile( '\w+ - [1-9]\d* error\(s\), [1-9]\d* warning\(s\)' )
    reErrors = re.compile( '\w+ - [1-9]\d* error\(s\), 0 warning\(s\)' )
    reWarnings = re.compile( '\w+ - 0 error\(s\), [1-9]\d* warning\(s\)' )
    
    for str in lines:
        if reErrorsAndWarnings.match( str ) or reErrors.match( str ) or reWarnings.match( str ):
            print str
    

def FindTestallErrors( filename ):
    return 1
    
if __name__ == '__main__':
    if os.path.exists( 'vsBuildAllLog.txt' ):
        FindVsErrors( 'vsBuildAllLog.txt' )
    if os.path.exists( 'Testalllog.txt' ):
        FindTestallErrors( 'Testalllog.txt' )

        
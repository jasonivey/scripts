import os, string, shutil, time
from stat import *

def RecurseDirectory( dir ):

    directories = []
    files = []
    
    for f in os.listdir( dir ):
        if f.find( '?' ) != -1:
            continue

        pathname = '%s/%s' % ( dir, f )
        mode = os.stat( pathname ).st_mode

        if S_ISDIR( mode ):
            directories.append( pathname )
        else:
            files.append( pathname )


    #for filename in files:
    #    
    #    filehandle = file( filename, 'r' )
    #    for 

if __name__ == '__main__':
    RecurseDirectory( 'famhistbak' )
import os, md5, sys, datetime
from DumpDir import *

if __name__ == '__main__':
    now = datetime.datetime.now()

    print('Outputting files with MD5 checksums for "Download"')
    os.chdir( 'e:\\' )
    filename = now.strftime("%Y-%m-%d Download.txt")
    outfile = file( filename, 'w' )
    print('Created file named "' + filename + '"\n')
    os.chdir( 'e:\Download' )
    DumpDir( '.', outfile, 1, 1 )
    outfile.close()

    os.chdir( 'e:\\' )

    print('\n\nCompleted Successfully...')

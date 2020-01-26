import os
import string
import shutil
import sys

import hash_utils

dirs = []

def GetFiles(dir, files, outfile):
    for d in dirs:
        dirs.remove(d)
    for f in os.listdir(dir):
        if f.find( '?' ) != -1 or f.find( 'System Volume Information' ) != -1 or f.find( 'RECYCLER' ) != -1:
            continue
        pathname = os.path.join(dir, f)
        if os.path.isdir(pathname):
            if recurse == 1:
                dirs.append( pathname )
        else:
            chksum = hash_utils.md5sum(pathname)
            if chksum in files:
                filestr = pathname[2:len(pathname)] + ' == ' + (files[chksum])[2:len( (files[chksum]) )]
                print(filestr)
                outfile.write( filestr + '\n' )
            else:
                files[chksum] = pathname
    return files    

def FindDuplicates( dir, recurse, files, outfile ):
    files = GetFiles( dir, files, outfile )
    if recurse == 0:
        return
    localdirs = dirs    
    for d in localdirs:
        files = FindDuplicates( d, recurse, files, outfile )

if __name__ == '__main__':
    if( len( sys.argv ) < 2 or sys.argv[1].startswith('-') ):
        print('DumpDir <output file name> [-norecurse]')
        print('\tBy default recursing directories is on')
        sys.exit(1)

    filename = sys.argv[1]
    recurse = 1

    if '-norecurse' in sys.argv:
        recurse = 0

    with open(filename, 'w') as outfile:
        files = {}
        FindDuplicates('.', recurse, files, outfile)

    sys.exit(0)

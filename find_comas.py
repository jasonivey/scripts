import os, string, shutil
from stat import *

def RecurseDirectory( dir ):

    for f in os.listdir( dir ):

        oldname = '%s/%s' % (dir, f)
        newname = ''

        if oldname.find( ',' ) != -1:
            newname = string.replace( oldname, ',', ' -' )
            print(f)

        if len( newname ) != 0:
            os.rename( oldname, newname )
        else:
            newname = oldname

        mode = os.stat( newname ).st_mode

        if S_ISDIR( mode ):
            RecurseDirectory( newname )


if __name__ == '__main__':
    RecurseDirectory( '.' )

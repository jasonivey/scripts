import sys, os, EXIF
from mx.DateTime import *

if __name__ == '__main__':
    for root, dirs, files in os.walk( os.getcwd() ):
        for f in files:
            if os.path.splitext( f )[1].lower() == '.jpg':
                oldName = os.path.join( root, f )
                file = open( oldName, 'rb' )
                header = EXIF.process_file( file )
                file.close()
                if header and header['EXIF DateTimeOriginal']:
                    parts = str(header['EXIF DateTimeOriginal']).split()
                    originalStr = parts[0].replace(':', '-') + ' ' + parts[1]
                    originalDateTime = DateTimeFrom( originalStr )
                    #if originalStr != str( originalDateTime )[ : len(str( originalDateTime )) - 3 ]:
                    #    print originalStr + ' <==> ' + str( originalDateTime )[ : len(str( originalDateTime )) - 3 ]
                    newName = os.path.join( root, originalDateTime.strftime('%Y-%m-%d - ') + f )
                    if oldName != newName:
                        os.rename( oldName, newName )
                        print(('Renaming %s to %s.' % ( oldName, newName )))
                    else:
                        print(('Both old and new names are identical, %s.' % oldName))
                else:
                    print(('Photo %s did not have an original date/time attribute.' % oldName))

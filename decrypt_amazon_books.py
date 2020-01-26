#!/usr/bin/env python
import os
import sys

lib_path = r'N:\downloads\eBooks\tools_v4.8\KindleBooks\lib'
if os.path.isdir(lib_path):
    sys.path.append(lib_path)

import mobidedrm
#import k4pcdedrm

##
## Jason's Ivey Info
## Serial #: B002A1A093051939
## Type    : Kindle 2
## PID     : SBIXFR8*7D
##
class DrmException(Exception):
    pass

#def DecryptPrcBook(src, dst):
#    data_file = file(src, 'rb').read()
#    try:
#        strippedFile = k4pcdedrm.DrmStripper(data_file)
#        file(dst, 'wb').write(strippedFile.getResult())
#    except k4pcdedrm.DrmException, e:
#        print 'Error in %s: %s' % (src, e)
    
def DecryptAzwBook(src, dst):
    #data_file = file(src, 'rb').read()
    pidlist = ['SBIXFR8*7D']
    try:
        book = mobidedrm.MobiBook(src)
        book.processBook(pidlist)
        file(dst, 'wb').write(book.mobi_data)
        print('Decrypted %s successfully' % src)
    except mobidedrm.DrmException as e:
        print('Error in %s: %s' % (src, e))

def DecryptBooks(dir):
    paths = []
    for root, dirs, files in os.walk( dir ):
        for file in files:
            extension = os.path.splitext(file)[1].lower()
            if extension == '.azw' or extension == '.prc':
                paths.append( os.path.join( root, file ) )

    for path in paths:
        basename, extension = os.path.splitext(path)
        if extension.lower() == '.azw':
            DecryptAzwBook(path, basename + '.mobi')
        else:
            DecryptPrcBook(path, basename + '-decrypted' + extension)

if __name__ == '__main__':
    DecryptBooks( os.getcwd() )

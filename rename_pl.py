import os, string, shutil, sys

def Error( msg ):
    sys.stdout.write( '\nERROR: ' + msg + '\n' )
    

def CHECK( expression, description ):
    if not expression:
        Error('Check failed: ' + description + '\n\n')
        sys.exit(1)
    

if __name__ == '__main__':

    dir = os.getcwd()
    
    for f in os.listdir( dir ):

        pathname = '%s\\%s' % ( dir, f )
        extension = os.path.splitext( pathname )[1].lower()
        if not os.path.isdir( pathname ) and extension == '':
            os.rename( pathname, pathname + '.pl' )
import os

if __name__ == '__main__':
    for f in os.listdir( os.getcwd() ):
        pathname = '%s\\%s' % ( dir, f )
        extension = os.path.splitext( pathname )[1].lower()
        if not os.path.isdir( pathname ) and extension == '':
            os.rename( pathname, pathname + '.pl' )
import os, string, shutil
from stat import *

class IncludeFile:
    def __init__( self, name ):
        self.mCount = 1
        self.mName = name
        
    def IncInstance( self ):
        self.mCount += 1
        
    def IncludeFileSort( a, b ):
        if a.mCount == b.mCount:
            if a.mName == b.mName:
                return 0
            elif a.mName < b.mName:
                return -1
            else:
                return 1
        elif a.mCount < b.mCount:
            return 1
        else:
            return -1
        
includes = []

def InList( thelist, item ):
    i = 0
    while i < len( thelist ):
        if thelist[i].mName == item:
            return i
        i += 1
    return -1

def ParseIncludes( filename ):
    
    sourcefile = file( filename, 'r' )
    lines = sourcefile.readlines()
    sourcefile.close()
    
    for str in lines:

        if str.find( '#include' ) != -1:
            includeline = str.strip().lower()

            startdelim = '<'
            enddelim = '>'

            if includeline.find( "\"" ) != -1:
                startdelim = enddelim = "\""
                
            start = includeline.find( startdelim )
            end = includeline.rfind( enddelim )

            if start == -1 or end == -1:
                continue
            includeline = includeline[start + 1:end]

            index = InList( includes, includeline )
            if index == -1:
                includes.append( IncludeFile( includeline ) )
            else:
                includes[index].IncInstance()
                
        elif str.find( 'using namespace' ) != -1 and filename.lower().endswith('.h'):
            print('File: ' + filename + ': ' + str.strip())


def RecurseDirectory( dir, dirList ):

    for f in os.listdir( dir ):
        if f.find( '?' ) != -1:
            continue
        
        pathname = '%s/%s' % (dir, f)
        mode = os.stat( pathname ).st_mode
        
        if S_ISDIR( mode ):
            dirList += RecurseDirectory( pathname, dirList )
        elif f.lower().endswith('.h'):## or f.lower().endswith('.cpp'):
            ParseIncludes( pathname )

    return dirList


if __name__ == '__main__':
    dirList = []
    RecurseDirectory( '.', dirList )
    includes.sort( IncludeFile.IncludeFileSort )

    outfile = file( 'out.txt', 'w' )
    for i in includes:
        outfile.write( str( i.mCount ) + '.  ' + i.mName + '\n' )
        
    outfile.close()
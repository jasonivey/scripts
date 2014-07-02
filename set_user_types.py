import os, re
from bisect import bisect_right
from .Utils import RecurseDirectory

class StringI:
    "Case insensitive string wrapper"
    def __init__(self, str):
        self.mStr = str
    
    def __cmp__(self, other):
        return cmp( self.mStr.lower(), other.mStr.lower() )


def GetInsertionIndex( types, type ):
    index = bisect_right( types, type )
    if index and index - 1 < len( types ):
        if types[index - 1] != type:
            return index
        else:
            return -1
    else:
        return 0


def AddType( types, type ):
    if type == '':
        return
    
    str = StringI( type )
    index = GetInsertionIndex( types, str )
    if index != -1:
        types.insert( index, str )

    
def GetExistingTypes( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()
    
    types = []
    for line in lines:
        AddType( types, line.strip() )

    return types


def IsSourceFile(file):
    return not os.path.dirname(file).lower().endswith('test') and re.compile( '^.*\.(?:h|hpp|c|cpp)$', re.IGNORECASE )
    

def GetTypes( filename, types ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()
    invalidStrings = [['//', True], ['\\', True], ['<', True],
                      ['__', True], [';', True], ['{', True],
                      [',', True], ['::', False ], [':', False ],
                      ['[', True], ['TEMPLATE_DECLSPEC', True],]
    for line in lines:
        parts = []
        
        #if line.strip().lower().find( 'typedef' ) != -1:
        #    parts = line.strip().split()
        if line.strip().lower().startswith( 'struct' ) or \
           line.strip().lower().startswith( 'class' ):
            parts = line.strip().split()
            if parts[0].strip().lower() != 'struct' and \
               parts[0].strip().lower() != 'class':
                parts = []
            
        if len( parts ) > 1:
            type = parts[1].strip()
            for substr in invalidStrings:
                index = type.find( substr[0] )
                if index != -1:
                    if substr[1]:
                        type = type[ 0 : index ].strip()
                    else:
                        type = type[ index + len( substr[0] ) : len( type ) ].strip()
            AddType( types, type )
    
    return types


def OutputTypes( filename, existingTypes, types ):
    
    file = open( filename, 'a+' )
    if len( existingTypes ):
        file.write( '\n' )
    
    for type in types:
        if type.mStr == 'boost':
            type = type
        if GetInsertionIndex( existingTypes, type ) != -1:
            file.write( type.mStr + '\n' )
            
    if len( types ):
        file.write( '\n' )
        
    file.close()

    
if __name__ == '__main__':
    usertype = os.path.normpath( os.path.join( os.environ["VS80COMNTOOLS"], '../IDE/usertype.dat' ) )

    types = []
    if os.path.exists( usertype ):
        types = GetExistingTypes( usertype )
    
    existingTypes = []
    for type in types:
        newType = StringI(type.mStr)
        existingTypes.append( newType )
    
    for file in RecurseDirectory(os.getcwd(), IsSourceFile):
        types = GetTypes( file, types )

    OutputTypes( usertype, existingTypes, types )

    
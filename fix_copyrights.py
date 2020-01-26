import os, sys, re, string, datetime, p4

perforce = p4.P4()
perforce.connect()

def IsFileInDepot( file ):
    result = perforce.run_files(file)
    if len(result) >= 1:
        data = result[0]
        return re.search(r' - (?:edit|add) change ', data, re.I )
    return False

def OpenForEdit( filename ):
    success = len( perforce.run_edit(filename) ) >= 1
    if not success:
        print(('Error while opening %s for edit.' % filename))
    return success

if __name__ == '__main__':
    paths = []
    dir = os.getcwd()
    regex = re.compile( '^.*\.(?:h|hpp|c|cpp|inl)$', re.I )

    
    for root, dirs, files in os.walk( dir ):
        for file in files:
            filename = os.path.join(root, file)
            if regex.match(filename) and IsFileInDepot(filename):
                paths.append( os.path.join( root, file ) )
                
    for filename in paths:
        file = open(filename, 'r')
        lines = file.readlines()
        file.close()
        
        if not re.search('2007', lines[0]):
            print(('Updating %s' % os.path.basename(filename)))
            lines[0] = '/*Copyright (c)2007 Symantec Corporation. All rights reserved.\n'
            
            if not OpenForEdit( filename ):
                sys.exit(1)
                
            file = open(filename, 'w')
            data = file.writelines(lines)
            file.close()
        else:
            print(('DON\'T NEED TO UPDATE %s' % os.path.basename(filename)))

import os, string, shutil, sys, re, Perforce
from .Utils import RecurseDirectory


def IsProjectFile(file):
    return not re.search('wsfiles', file, re.I) and re.match('^.*\.vcproj$', file, re.I)


def RemoveWin64Configuration( filename ):
    file = open( filename, 'r' )
    text = file.read()
    file.close()
    
    pattern = '\t+StripPrivateSymbols *= *"[^"]+"\n'
    regex = re.compile( pattern, re.I |re.S )
    newtext = regex.sub('', text)

    if text != newtext and Perforce.OpenForEdit( filename ):
        file = open( filename, 'w' )
        text = file.write(newtext)
        file.close()
    

def SetCurrentDirectory( dir ):
    oldDir = os.getcwd()
    if oldDir.lower() != dir.lower():
        os.chdir( dir )
    return oldDir    


if __name__ == '__main__':
    if len( sys.argv ) > 1:
        dir = os.path.abspath( sys.argv[1] )
        oldDir = SetCurrentDirectory( dir )
    else:
        oldDir = dir = os.getcwd()

    for file in RecurseDirectory( dir, IsProjectFile ):
        RemoveWin64Configuration( file )

    SetCurrentDirectory( oldDir )

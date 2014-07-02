import os, string, shutil, sys, re, Perforce
from .Utils import RecurseDirectory


def IsProjectFile( file ):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)


def CreateX64Configuration( text ):
    text = re.sub( 'win32_', 'win64-x64_', text )
    
    match = re.search( 'Name="VCMIDLTool"', text, re.S )
    if match:
        index = text.rfind( '\n', 0, match.start() )
        if index != -1:
            str = text[index + 1 : match.start()] + 'TargetEnvironment="3"\n'
            insertion = match.start() + len( match.group(0) ) + 1
            text = text[ : insertion ] + str + text[ insertion : ]
            
    regex = re.compile( '(Name="(?:Release|Debug)\|)(Win32)"', re.I | re.S )
    text = regex.sub( '\\1x64"', text )

    regex = re.compile( '(TargetMachine=)"1"', re.I | re.S )
    text = regex.sub( '\\1"17"', text )
    
    return text
    
    
def AddX64Configuration( filename ):
    file = open( filename, 'r' )
    text = file.read()
    file.close()
    
    last = 0
    vcproj = ''
    pattern = '(\t+<Platform\n\t+Name=)"Win32"(\n\t+/>\n)'
    regex = re.compile( pattern, re.I |re.S )
    match = regex.search( text )
    if match:
        vcproj += text[ : match.end() ] + match.group(1) + '"x64"' + match.group(2)
        last = match.end()
    
    pattern = '(?:\t+<(?:file)?configuration\s+name="(?:debug|release)\|win32"\s+)(?:.*?)(?:</(?:file)?configuration>\n)'
    regex = re.compile( pattern, re.I |re.S )
    match = regex.search( text, last )
    found = match != None

    while match:
        vcproj += text[ last : match.end() ] + CreateX64Configuration( text[ match.start() : match.end() ] )
        last = match.end()
        match = regex.search( text, last )

    if found and Perforce.OpenForEdit( filename ):
        vcproj += text[last:]
        file = open( filename, 'w' )
        file.write( vcproj )
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

    for file in RecurseDirectory(dir, IsProjectFile):
        AddX64Configuration( file )

    SetCurrentDirectory( oldDir )

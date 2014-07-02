import os, string, shutil, sys, re, Perforce
from .Utils import *


def IsProjectFile(file):
    return not re.search('wsfiles', file, re.I) and re.match('^.*\.vcproj$', file, re.I)


def RemoveDetect64BitPortabilityProblems( filename ):
    file = open( filename, 'r' )
    text = file.read()
    file.close()
    
    pattern = r'\t+Detect64BitPortabilityProblems="[^"]+"[^\n]*\n'
    regex = re.compile( pattern, re.I |re.S )
    newtext = regex.sub('', text)
    
    if newtext != text and Perforce.OpenForEdit( filename ):
        file = open( filename, 'w' )
        file.write( newtext )
        file.close()


def RemoveWin64Configuration( filename ):
    file = open( filename, 'r' )
    text = file.read()
    file.close()
    
    #pattern = '(?P<pre><(?:file)?configuration\s+name="(?:debug|release)\|x64"\s+)(?P<config>.*?)(?P<post></(?:file)?configuration>)'
    pattern = '(?:\t+<(?:file)?configuration\s+name="win64 (?:debug|release)\|win32"\s+)(?:.*?)(?:</(?:file)?configuration>\n)'
    regex = re.compile( pattern, re.I |re.S )
    match = regex.search( text )
    found = match != None

    while match:
        begin = match.start()
        end = match.start() + len( match.group(0) )
        text = text[ : begin ] + text[ end : ]
        match = regex.search( text )

    if found and Perforce.OpenForEdit( filename ):
        file = open( filename, 'w' )
        file.write( text )
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
    
    for file in RecurseDirectory( dir, IsProjectFile, False ):
        RemoveWin64Configuration( file )
        RemoveDetect64BitPortabilityProblems( file )

    SetCurrentDirectory( oldDir )

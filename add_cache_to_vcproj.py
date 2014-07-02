import os, sys, re

def Error( msg ):
    if sys.stderr:
        sys.stderr.write( '\nERROR: ' + msg + '\n' )
    

def CHECK( expression, description ):
    if not expression:
        Error('Check failed: %s' % description)
        raise AssertionError
    return expression


def OpenForEdit( filename ):
    command = 'p4 edit %s' % filename
    lines = os.popen4( command, 't' )[1].readlines()
    success = False
    for line in lines:
        if line.lower().find('opened for edit') != -1:
            success = True
    return success


def IsProjectFile( file ):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)


def FindCachePath(filename):
    dir = os.path.dirname(filename)
    parent = os.path.join( dir, '..' )
    while os.path.abspath( parent ) != os.path.abspath( dir ):
        if os.path.exists( os.path.join( dir, 'sandbox.txt' ) ):
            origdir = os.path.dirname(filename)
            dir = os.path.join( dir, 'cache' )
            CHECK( os.path.isdir(dir), 'The cache directory is not located in the sandbox.' )
            return dir[len(origdir) + 1:].replace('\\', '/')
        else:
            dir = parent
            parent = os.path.join( dir, '..' )
    CHECK( False, 'Tried to find sandbox.txt but instead dropped out in the root directory.' )

    
def AddAdditionalIncludeDirectories(text, config, cache):
    match = re.search(r'AdditionalIncludeDirectories=(?P<includes>"[^"]*")', text, re.I)
    if match == None:
        return text
    
    line = match.group('includes')
    if line.lower().find( 'cache' ) == -1 and line.lower().find( 'vs.net' ) != -1:
        end = line.lower().find( 'vs.net' )
        if line.rfind( ';', 0, end ) != -1:
            start = line.rfind( ';', 0, end )
        else:
            start = line.rfind( '"', 0, end )
        addition = line[start + 1 : end] + 'cache'
        if line[-2] != ';':
            addition = ';' + addition
        line = line[ :line.rfind('"') ] + addition + line[ line.rfind('"'): ]
    text = text[ :match.start('includes') ] + line + text[ match.end('includes'): ]
    return text


def UpdateCompilerSettings( new_text, cache, regex ):
    offset = 0
    for i in regex.finditer(new_text):
        config = AddAdditionalIncludeDirectories(i.group('data'), i.group('platform').lower(), cache)
        new_text = new_text[:offset + i.start('data')] + config + new_text[offset + i.end('data'):]
        offset += len( config ) - len( i.group('data') )
    return new_text


def UpdateVcProj(filename, regex, analyze):
    file = open( filename, 'r' )
    org_text = file.read()
    file.close()
    new_text = org_text
    
    cache = FindCachePath(filename)
    new_text = UpdateCompilerSettings(new_text, cache, regex)
    if new_text != org_text:
        print('Updating %s' % filename)
        if analyze:
            return
        CHECK( OpenForEdit(filename), 'Unable to open %s for editing' % filename )
        file = open( filename, 'w' )
        file.write(new_text)
        file.close()
    

if __name__ == '__main__':
    if len( sys.argv ) > 1 and os.path.isdir(sys.argv[1]):
        dir = sys.argv[1]
    else:
        dir = os.getcwd()
        
    analyze = '-a' in sys.argv

    pattern = r'''(?:\t+<(?:file)?                              # can be file configuration or just
                        configuration\s+                        # configuration
                        name="(?:debug|release)\|               # pick up debug or release configurations
                        (?P<platform>win32|x64)"\s+)            # pick up win32 or x64 platforms and store that info for later retrieval
                        .*?                                     # it will most likely have some stuff preceding the linker section
                        <Tool\s+                                # followed by a tool opening
                        Name="VCCLCompilerTool"                 # marked by the compiler tool
                        (?P<data>.*?)                           # grab all of the insides of the linker tool
                        />                                      # followed by the tool closer
                        .*?                                     # all the remaining section of the configuration
                        (?:</(?:file)?configuration>\n)'''      # followed by a close configuration

    regex = re.compile( pattern, re.I | re.S | re.X )
    for root, dirs, files in os.walk( dir ):
        for file in files:
            path = os.path.join( root, file )
            if IsProjectFile(path):
                UpdateVcProj( path, regex, analyze )

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
    #return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)
    return file.lower().find('wsfiles') == -1 and file.lower().endswith('.vcproj')


def AddIgnoreWarning(text):
    if re.search(r'DisableSpecificWarnings="4127;4702;4063"', text):
        print('Warnings already set correctly')
        return text
    
    new_text = re.sub(r'DisableSpecificWarnings="[^"]+"', r'DisableSpecificWarnings="4127;4702;4063"', text)
    if text != new_text:
        print('Warnings set correctly via re.sub()')
        return new_text
    
    match = re.search('\n(?P<tabs>\s+)AdditionalIncludeDirectories="[^"]+"\s*\n', text, re.I)
    if not match:
        print('AdditionalIncludeDirectory setting not found in this VCPROJ file.')
        return text
    
    new_text = text[ :match.end() ] + match.group('tabs') + r'DisableSpecificWarnings="4127;4702;4063"' + text[ match.end(): ]
    print('Manually added warnings')
    return new_text 


def UpdateCompilerSettings( new_text, regex ):
    offset = 0
    for i in regex.finditer(new_text):
        config = AddIgnoreWarning(i.group('data'))
        new_text = new_text[:offset + i.start('data')] + config + new_text[offset + i.end('data'):]
        offset += len( config ) - len( i.group('data') )
    return new_text


def UpdateVcProj(filename, compilerRegex):
    file = open( filename, 'r' )
    org_text = file.read()
    file.close()
    new_text = org_text
    
    print(('Updating %s' % filename))
    new_text = UpdateCompilerSettings(new_text, compilerRegex)

    if new_text != org_text:
        print(('Updating %s' % filename))
        CHECK( OpenForEdit(filename), 'Unable to open %s for editing' % filename )
        file = open( filename, 'w' )
        file.write(new_text)
        file.close()
    

if __name__ == '__main__':
    if len( sys.argv ) > 1:
        dir = sys.argv[1]
    else:
        dir = os.getcwd()

    compilerPattern = r'''(?:\t+<                                 # can be file configuration or just
                        configuration\s+                          # configuration
                        name="(?:debug|release)\|                 # pick up debug or release configurations
                        (?P<platform>win32|x64)"\s+)              # pick up win32 or x64 platforms and store that info for later retrieval
                        .*?                                       # it will most likely have some stuff preceding the linker section
                        <Tool\s+                                  # followed by a tool opening
                        Name="VCCLCompilerTool"                   # marked by the compiler tool
                        (?P<data>.*?)                             # grab all of the insides of the linker tool
                        />                                        # followed by the tool closer
                        .*?                                       # all the remaining section of the configuration
                        (?:</(?:file)?configuration>\n)'''        # followed by a close configuration

    compilerRegex = re.compile( compilerPattern, re.I | re.S | re.X )
    
    for root, dirs, files in os.walk( dir ):
        for file in files:
            path = os.path.join( root, file )
            if IsProjectFile(path):
                UpdateVcProj( path, compilerRegex )

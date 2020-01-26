import os, sys, re
from xml.dom.minidom import Document
from xml.dom.minidom import parse

class Include:
    "Structure to encapsulate an file included from a source file."
    def __init__(self, name):
        self.mName, self.mExtension = os.path.splitext(name.lower())
        self.mQueried = False

    def GetModuleName(self):
        return self.mName
    
    def IsQueried(self):
        return self.mQueried == True
    
    def SetQueried(self, value = True):
        self.mQueried = value

    def __cmp__(self, other): 
        thisName = self.mName + self.mExtension
        otherName = other.mName + other.mExtension
        return cmp( thisName, otherName )

    def __eq__(self, other):
        return self.mName + self.mExtension == other.mName + other.mExtension
    
    def __str__(self):
        return self.mName + self.mExtension
    
    def __hash__(self):
        return hash(self.mName + self.mExtension)


class CycleFinder:
    "Object which controlls all the aspects of finding cycles in source files."
    def __init__(self, dir):
        self.mDirectory = dir
        self.mFiles = []
        self.mXmlDocument = Document()
        self.mXml = None
        
    def Execute(self, filename):
        extensions = ['.inl', '.h', '.hpp', '.c', '.cc', '.cpp']
        files = []
        for root, dirs, f in os.walk( self.mDirectory ):
            paths = []
            searched = False
            for file in f:
                if not searched:
                    searched = True
                    paths = GetIncludePaths(root)
    
                extension = os.path.splitext(file)[1].lower()
                if extension in extensions:
                    name = os.path.join( root, file ).lower();
                    file = CppFile(name, paths, self)
                    file.ParseIncludes()
                    self.AddFile(file)

        self.mXml = self.mXmlDocument.createElement( "CycleFinder" )
        
        for file in self.mFiles:
            if os.path.basename(file.mName) == 'bytes.inl':
                print('.')
            print(('Processing %s.' % os.path.basename(file.mName)))
            file.AnalyzeDependencies()
        
        self.mXmlDocument.appendChild( self.mXml )
        file = open( filename, 'w' )
        file.write( self.mXmlDocument.toprettyxml() )
        self.mXmlDocument.unlink()
        file.close()
        

    def AddFile(self, file):
        if file not in self.mFiles:
            self.mFiles.append(file)
    
    def GetHeaderFile(self, name):
        retfile = None
        file = CppFile(name, [], self)
        if file not in self.mFiles:
            print(('Unable to find existing file %s.' % name))
        else:
            retfile = self.mFiles[self.mFiles.index(file)]
        return retfile
    
    def __str__(self):
        str = 'Parsing Files In %s' % self.mDirectory
        for file in self.mFiles:
            str += '%s' % file
        return str


class CppFile:
    "Structure to encapsulate an any C++ source/header/inline file."
    def __init__(self, name, path, finder):
        self.mName = name
        self.mIncludePath = path
        self.mIncludes = []
        self.mFinder = finder

    def ParseIncludes(self):
        file = open( self.mName, 'r' )
        contents = file.read()
        file.close()
        
        # Match all #include lines that don't have '//' comments preceeding them
        #  The #include can have white spaces and the path is enclosed by a "" or <>
        pattern = '(?<=\n)\s*#\s*include\s*["<]([^">]+)[">]'
        for match in re.finditer( pattern, contents ):
            name = match.group(1)
            include = None
            path = os.path.join( os.path.dirname(self.mName), name )
            if os.path.isfile( path ):
                include = Include( path )
            else:
                for path in self.mIncludePath:
                    fullpath = os.path.abspath( os.path.join( path, name ) )
                    if os.path.isfile( fullpath ):
                        include = Include( fullpath )
                        break;
            if include and include not in self.mIncludes:
                self.mIncludes.append( include )
            elif not include and not IsInvalidFile(name):
                print(('ERROR: "%s"\n\tCouldn\'t find "%s".' % (self.mName, name)))
    
    def AnalyzeDependencies(self):
        xmlFile = self.mFinder.mXmlDocument.createElement("File")
        xmlFile.setAttribute( "Name", self.mName )
        
        workspace = GetWorkspaceDir(os.path.dirname(self.mName))
        children = {}
        for include in self.mIncludes:
            
            xmlInclude = self.mFinder.mXmlDocument.createElement("Include")
            xmlInclude.setAttribute( "Name", str(include) )
            
            if str(include).startswith(workspace):
                assert( include not in list(children.keys()) )
                children[include] = xmlInclude
                #children[include] = '%s\n\t      includes %s.\n' % (self.mName, include)
                xmlInclude.setAttribute( "Queried", "True" )
            else:
                xmlInclude.setAttribute( "Queried", "False" )
            
            xmlFile.appendChild(xmlInclude)
        
        self.Recurse(children, workspace)
        #i = 1
        #print 'ANALYZING %s' % self.mName
        #for child in children.keys():
        #    if child in cycles:
        #        sys.stdout.write('CYCLE: ')
        #    sys.stdout.write( '%s. %s' % ( i, children[child] ) )
        #    i = i + 1
        
        self.mFinder.mXml.appendChild( xmlFile )
            
    def Recurse( self, children, workspace ):
        totalQueried = 0
        
        for child in list(children.keys()):
            if child.IsQueried():
                continue
            else:
                totalQueried = totalQueried + 1
                child.SetQueried()

            xmlChild = children[child]
            childFile = self.mFinder.GetHeaderFile(str(child))
            if not childFile:
                continue

            for grandChild in childFile.mIncludes:
                
                xmlGrandChild = self.mFinder.mXmlDocument.createElement("Include")
                xmlGrandChild.setAttribute( "Name", str(grandChild) )

                if str(grandChild).startswith(workspace):
                    #children[child] += '\tWhich includes %s.\n' % grandChild
                    if str(grandChild) != self.mName and grandChild not in list(children.keys()):
                        #children[grandChild] = '%s\n\t      includes %s.\n' % (child, grandChild)
                        children[grandChild] = xmlGrandChild
                    if not self.IsSource() and grandChild.GetModuleName() == self.GetModuleName():
                        xmlGrandChild.setAttribute( "Cycle", "True" )
                    else:
                        xmlGrandChild.setAttribute( "Cycle", "False" )
                    xmlGrandChild.setAttribute( "Queried", "True" )
                else:
                    xmlGrandChild.setAttribute( "Cycle", "False" )
                    xmlGrandChild.setAttribute( "Queried", "False" )

                xmlChild.appendChild( xmlGrandChild )

        if totalQueried == 0:
            return
        
        self.Recurse(children, workspace)

    def IsSource(self):
        return os.path.splitext(self.mName)[1] in ['.inl', '.c', '.cc', '.cpp']
    
    def GetModuleName(self):
        return os.path.splitext(self.mName)[0]
    
    def __cmp__(self, other):
        return cmp( self.mName, other.mName )
    
    def __eq__(self, other):
        return self.mName == other.mName

    def __str__(self):
        str = '\nFile: %s\n' % self.mName
        for include in self.mIncludes:
            str += '\t%s\n' % include
        return str

def IsInvalidFile(name):
    invalidFiles = ['termios.h',
                    'unistd.h',
                    'localresult.h',
                    'dirent.h',
                    'screen.h',
                    'fsio.h',
                    'utime.h',
                    'mntent.h',
                    'pthread.h',
                    'iostream.h',
                    'stdint.h',
                    'base/dev/hash/hash.h',]
    invlidPrefixes = ['sys/',
                      'iniparser/dev',
                      'sys/fcntl.h',
                      'scsi/scsi_ioctl.h',
                      'linux/major.h',
                      'testmonitor/dev',
                      'datetime/dev',
                      'cppunit/dev',
                      'base/cppunit',
                      'base/assertion.h',
                      'base/cppunit',
                      'global/dev',
                      'c:/proj2',
                      'boost/',]
    
    if name.lower() in invalidFiles:
        return True
    else:
        for prefix in invlidPrefixes:
            if name.lower().startswith( prefix ):
                return True
        return False


def GetEnvironmentVariable( var ):
    if var in os.environ:
        return os.environ[var]
    else:
        return ''
    

def GetEnvironmentDirs():
    environIncludes = GetEnvironmentVariable('INCLUDE')
    dirs = []
    if environIncludes:
        for part in environIncludes.split(';'):
            index = 0
            start == 0
            while start != -1:
                start = part.find('%', index)
                if start == -1:
                    break
                end = part.find('%', start + 1)
                assert( end != -1 )
                sub = GetEnvironmentVariable( part[start + 1 : end] )
                part = part[:start] + sub + part[end + 1:]
                index = start + 1
            if part.lower() not in dirs:
                dirs.append( part.lower() )
    return dirs


def GetStandardIncludes(name):
    dirs = []
    file = open( name, 'r' )
    data = file.read()
    file.close()
    match = re.search( 'include *=([^\n]*)\n', data, re.I | re.M )
    if match:
        line = match.group(1)
        for part in line.split(';'):
            if part.find('%') == -1 and part.lower() not in dirs and os.path.isdir(part):
                dirs.append(part.lower())

    for dir in GetEnvironmentDirs():
        if os.path.isdir(dir):
            dirs.append(dir.lower())

    return dirs

    
def GetVcProjIncludePaths(dir):
    dirs = []
    name = [name for name in os.listdir(dir) if os.path.splitext(name)[1].lower() == '.vcproj']
    if name and len( name ):
        name = os.path.join( dir, name[0] )
        file = open( name, 'r' )
        data = file.read()
        file.close()
        for match in re.finditer( 'AdditionalIncludeDirectories *= *"([^"]*)"', data ):
            for path in match.group(1).split(';'):
                path = os.path.abspath( os.path.join(dir, path) ).lower()
                if os.path.isdir(path) and path not in dirs:
                    dirs.append(path)
    return dirs


def GetWorkspaceDir(dir):
    parent = os.path.abspath( os.path.join( dir, '..' ) ) + os.path.sep
    if os.path.isfile( os.path.join(parent, 'sandbox.txt') ):
        return dir
    elif parent == os.path.splitdrive( dir.lower() )[0] + os.path.sep:
        print('Tried to find sandbox.txt but instead dropped out in the root directory.')
        sys.exit(1)
    else:
        return GetWorkspaceDir(parent)


def GetPathsRelativeToSandbox(dir):
    dirs = []
    parent = os.path.normpath( os.path.join( dir, '..' ) ).lower()
    while parent != os.path.splitdrive( dir.lower() )[0] + os.path.sep:
        dirs.append(parent)
        if os.path.isfile( os.path.join( parent, 'sandbox.txt' ) ):
            break
        parent = os.path.normpath( os.path.join( parent, '..' ) ).lower()
    if not os.path.isfile( os.path.join( parent, 'sandbox.txt' ) ):
        print('Tried to find sandbox.txt but instead dropped out in the root directory.')
        sys.exit(1)
    return dirs


def GetIncludePaths( dir ):
    sandboxDirs = GetPathsRelativeToSandbox(dir)
    vcprojDirs = GetVcProjIncludePaths(dir)
    includeDirs = []
    tool = GetEnvironmentVariable('VS80COMNTOOLS')
    if tool and os.path.isfile(os.path.join( tool, 'vsvars32.bat' )):
        includeDirs = GetStandardIncludes(os.path.join( tool, 'vsvars32.bat' ))

    dirs = []
    for i in [sandboxDirs, vcprojDirs, includeDirs]:
        for name in i:
            if name.lower() not in dirs:
                dirs.append(name.lower())

    return dirs


if __name__ == '__main__':
    finder = CycleFinder( os.getcwd() )
    finder.Execute('d:/out.xml')
    file = open( 'd:/output.txt', 'w' )
    file.write(str(finder))
    file.close()
    


import sys, os, re, time, Utils, Perforce

def FixupBuildLog(data):
    return Utils.CompressWideChars(data).replace('&quot;', '"')

class Project:
    def __init__(self, path, cfg):
        self.mPath = path
        self.mConfig = cfg 
        self.mBuildLog = os.path.join( path, self.mConfig, 'buildlog.htm' )
        self.mHeaders = []
        self.mSources = []
        self.mCompileOptions = ''
        assert( os.path.isfile( self.mBuildLog ) )
        data = self.ReadBuildLog()
        self.ParseBuildLog(data)

    def AddFile(self, name):
        if os.path.basename(name).startswith('!'):
            return
        assert( os.path.isfile( name ) )
        extension = os.path.splitext(name)[1]
        assert( extension in ['.h', '.hpp', '.c', '.cpp'] )
        if extension in ['.h', '.hpp']:
            self.mHeaders.append(name)
        else:
            self.mSources.append(name)
            
    def HasFiles(self):
        return len(self.mHeaders) > 0 or len(self.mSources) > 0
        
    def ReadBuildLog(self):
        file = open(self.mBuildLog, 'r')
        data = FixupBuildLog( file.read() )
        if not re.search( r' - 0 error\(s\), 0 warning\(s\)', data ):
            print(('ERROR: Build log found for project %s was not successful.' % self.mPath))
        file.close()
        return data
    
    def ParseBuildLog(self, data):
        pattern = r'creating command line "(?P<cl_command>cl.exe) @(?P<response_file>[^ ]*) (?P<cl_switches>[^"]*)"'
        match1 = re.search( pattern, data, re.I )
        assert( match1 )
        
        response_file = match1.group('response_file')
        begin = 0
        end = match1.start()
        
        match2 = re.search( os.path.basename(response_file), data[begin:end], re.I )
        assert( match2 )
        
        begin = match2.end()
        end = match1.start()
        match3 = re.search( r'\[\r\n(?P<compile_options>[^\n]*)\r\n', data[begin:end], re.M )
        assert( match3 )
        
        options = match3.group('compile_options')
        match4 = re.match( r'(?P<compile_options>.*) .*\.cpp', options, re.I )
        if match4:
            options = match4.group('compile_options')
        
        self.mCompileOptions = '%s %s' % ( options, match1.group('cl_switches') )
    
    def EliminateIncludes(self):
        pattern = r'(?<!//)#\s*include ["<][^">]*[">].*'
        regex = re.compile(pattern)
        
        for header in self.mHeaders:
            file = open( header, 'r' )
            data = file.read()
            file.close()
            match = regex.search(data)
            if match and Perforce.OpenForEdit(header):
                while match:
                    begin = match.start()

                    file = open( header, 'w' )
                    file.write( data[:begin] + '//' + data[begin:] )
                    file.close()

                    sourceFile = os.path.join( os.path.dirname(header), 'EliminateIncludes.cpp' )
                    file = open( sourceFile, 'w' )
                    file.write( '#include "%s"\n' % os.path.basename(header) )
                    file.close()

                    if self.Compile(sourceFile) == 0:
                        data = data[:begin] + '//' + data[begin:]
                    else:
                        file = open( header, 'w' )
                        file.write( data )
                        file.close()

                    os.remove(sourceFile)
                    match = regex.search(data, match.end())

    def Compile(self, source):
        os.chdir(self.mPath)
        command = 'd:\\vcvars32.bat && cl.exe %s %s' % (self.mCompileOptions, source)
        return os.system(command)

    def __str__(self):
        retstr = 'Project:   %s\n' % self.mPath
        files = self.mSources + self.mHeaders
        files.sort()
        for f in files:
            retstr += '\t%s\n' % f
        retstr += '\n'
        return retstr

class Component:
    def __init__(self, path, cfg):
        self.mName = os.path.basename(path)
        self.mPath = path
        self.mConfig = cfg
        self.mProjects = {}

        regex = re.compile( '^.*\.(?:h|hpp|c|cpp)$', re.I )
        devdir = os.path.join( self.mPath, 'Dev' )

        for root, dirs, files in os.walk(devdir):
            for dir in dirs:
                if dir.lower() == cfg.lower():
                    keyname = root.lower
                    self.mProjects[ keyname ] = Project( root, cfg )
                    print(root)
                    for file in files:
                        filename = os.path.join(root, file)
                        if regex.match(filename) and Perforce.IsFileInDepot(filename):
                            self.mProjects[ keyname ].AddFile(filename)
                            
    def HasFiles(self):
        valid = False
        for key in list(self.mProjects.keys()):
            if self.mProjects[key].HasFiles():
                valid = True
                break
        return valid
    
    def EliminateIncludes(self):
        for key in list(self.mProjects.keys()):
            self.mProjects[key].EliminateIncludes()

    def __str__(self):
        retstr = 'Component: %s\n' % self.mName
        #for key in self.mProjects.keys():
            #retstr += str( self.mProjects[key] )
        return retstr

def FindComponents(sandbox, cfg):
    components = []
    for comp in os.listdir( os.path.join( sandbox, 'ws' ) ):
        dir = os.path.join( sandbox, 'ws', comp )
        componenttxt = os.path.join(dir, 'components.txt')
        if os.path.isdir(dir) and os.path.isfile(componenttxt):
            component = Component( dir, cfg )
            if component.HasFiles():
                components.append(component)
    return components
    
if __name__ == '__main__':
    start = time.clock()
    
    sandbox = Utils.FindSandbox( os.curdir )
    components = FindComponents(sandbox, 'win32_debug')
    for c in components:
        c.EliminateIncludes()
        
    end = time.clock()
    print(('Elapsed Time: %0.03f Seconds' % ( end - start )))

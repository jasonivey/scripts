import os, sys, re

global P4EXE, P4PORT, P4_PREFIX_PATH
P4EXE = 'p4'
P4PORT = r'172.16.79.3:1666'
P4_PREFIX_PATH = r'//SEABU/ProductSource/'


def GetPerforceCommand(cmd):
    return '%s -p %s %s' % ( P4EXE, P4PORT, cmd )


class Match:
    "Structure to encapsulate a text match in a file."
    def __init__(self, number, line):
        self.mLineNumber = number
        self.mLine = line
        
    def __str__(self):
        return 'Line %s: %s' % (self.mLineNumber, self.mLine)


class File:
    "Structure to encapsulate a text file located in Perforce."
    def __init__(self, name, revision):
        self.mName = name
        self.mRevision = revision
    
    def __str__(self):
        str = '%s' % self.mName
        if self.mRevision:
            str += '#%s' % self.mRevision
        return str


class Project:
    "Structure to encapsulate a raptor project."
    def __init__(self):
        self.mName = ''
        self.mCategory = ''
        self.mBranch = ''
        self.mLabel = ''
        self.mMatches = {}
        
    def Initialize(self, name, category, branch, label, views):
        key = name.lower()
        if key in list(views.keys()):
            assert( category.lower() == views[key][1].lower() )
            assert( branch.lower() == views[key][2].lower() )
            self.mName = views[key][0]
            self.mCategory = views[key][1]
            self.mBranch = views[key][2]
        else:
            print('ERROR: Couldn\'t find project name, "%s", in the workspace view' % name)
            self.mName = name
            self.mCategory = category
            self.mBranch = branch
        self.SetLabel(label)

    def SetLabel(self, label):
        if label.lower().startswith( 'buildnumber_' ):
            self.mLabel = 'BuildNumber%s' % label[label.find('_'):]
        elif label.lower().startswith( 'release_' ):
            self.mLabel = 'Release%s' % label[label.find('_'):]
        else:
            if label:
                print('ERROR: Label, "%s", didn\t match the standard BuildNumber or Release format.' % label)
            self.mLabel = label
        
    def GetFiles(self):
        path = '"%s%s/%s/%s/"...' % ( P4_PREFIX_PATH, self.mCategory, self.mName, self.mBranch )
        if self.mLabel: path += '@%s' % self.mLabel
        command = GetPerforceCommand( 'files %s' % path )
        output = os.popen4( command, 't' )[1].read()
        
        pattern = '(?P<name>%s[^#]*)#(?P<revision>\d+) *- *(add|edit) *change *\d+ *\(text\)\n' % P4_PREFIX_PATH
        files = []
        for i in re.finditer(pattern, output):
            files.append( File(i.group('name'), i.group('revision')) )
            
        return files
    
    def GetFlags(self, caseInsensitive):
        if caseInsensitive:
            return re.I
        else:
            return 0
        
    def FindString(self, str, caseInsensitive, fast):
        flags = self.GetFlags(caseInsensitive)
            
        for filename in self.GetFiles():
            command = GetPerforceCommand( 'print -q "%s"' % filename )
            if fast:
                output = os.popen4( command, 't' )[1].read()
                regex = re.compile(str, flags)
                if regex.search(output):
                    match = Match('Unknown', 'One or more matches found in file.')
                    key = '%s' % filename
                    self.mMatches[key] = [match]
            else:
                lines = os.popen4( command, 't' )[1].readlines()
                number = 1
                for line in lines:
                    if re.search(str, line, flags):
                        match = Match(number, line)
                        if filename.mName not in list(self.mMatches.keys()):
                            self.mMatches[str(filename)] = [match]
                        else:
                            self.mMatches[str(filename)].append(match)
                    number = number + 1

    def __str__(self):
        self.mMatches = {}
        str  = 'Name     : %s\n' % self.mName
        str += 'Category : %s\n' % self.mCategory
        str += 'Branch   : %s\n' % self.mBranch
        str += 'Label    : %s\n' % self.mLabel
        for filename in list(self.mMatches.keys()):
            str += '%s\n' % filename
            for match in self.mMatches[filename]:
                str += '\t%s\n' % match
        return str


def GetSandbox(dir):
    parent = os.path.abspath( os.path.join( dir, '..' ) )
    if parent == dir:
        print('ERROR: While searching for sandbox.txt we found the root directory')
        sys.exit(1)
    elif os.path.isfile( os.path.join( dir, 'sandbox.txt' ) ):
        return dir
    else:
        return GetSandbox(parent)
    

def EnumerateProjects(sandbox, dir, views):
    file = open( os.path.join(sandbox, 'sandbox.txt'), 'r' )
    data = file.read()
    file.close()
    
    projects = []
    pattern = pattern = 'item\s*=\s*(?P<category>[^;]*);\s*(?P<name>[^;]*);\s*(?P<branch>[^;]*);\s*(?P<label>[^;\n]*)\n'
    for i in re.finditer( pattern, data ):
        if os.path.isdir( os.path.join(dir, i.group('name') ) ):
            project = Project()
            project.Initialize(i.group('name'), i.group('category'), i.group('branch'), i.group('label'), views)
            projects.append(project)
        
    return projects


def GetViews():
    command = GetPerforceCommand('workspace -o')
    output = os.popen4( command, 't' )[1].read()
    views = {}
    pattern = '%s(?P<category>[^/]+)/(?P<name>[^/]+)/(?P<branch>[^/]+)/' % P4_PREFIX_PATH
    for i in re.finditer(pattern, output):
        views[i.group('name').lower()] = [i.group('name'), i.group('category'), i.group('branch')]
    return views


def ParseArgs( args, dir ):
    caseInsensitive = False
    searchStr = None
    fast = False
    for arg in args:
        if arg.startswith('-') or arg.startswith('/'):
            argName = arg[1:]
            if argName.startswith('i'):
                caseInsensitive = True
            elif argName.startswith('f'):
                fast = True
        else:
            searchStr = arg
            
    if not searchStr:
        print('ERROR: Command line doesn\'t specify a string to search for')
    else:
        if caseInsensitive:
            suffix = 'in'
        else:
            suffix = ''
        sandbox = GetSandbox(dir)
        print('Searching for "%s" in the sandbox %s, case %ssensitive.' % ( searchStr, sandbox, suffix ))

    return searchStr, caseInsensitive, fast


if __name__ == '__main__':
    dir = os.getcwd()
    sandbox = GetSandbox(dir)
    searchStr, caseInsensitive, fast = ParseArgs(sys.argv, dir)
    views = GetViews()
    for project in EnumerateProjects(sandbox, dir, views):
        project.FindString(searchStr, caseInsensitive, fast)
        print('%s\n' % project)


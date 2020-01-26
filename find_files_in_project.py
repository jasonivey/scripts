import sys, os, glob, re
from Utils import *

def GetProjectFile(dir):
    for file in glob.glob(os.path.join(dir, '*.vcproj')):
        if file.lower().endswith('.vcproj'):
            return file
    return None


class HasProjectFile:
    def __init__(self):
        self.mDirs = {}
        self.mRegex = re.compile('^.*\.(?:h|hpp|c|cpp|inl)$', re.I)
        
    def __call__(self, file):
        if not self.mRegex.match(file) or os.path.dirname(file).lower().endswith('cppapi'):
            return False
        dir = os.path.dirname(file).lower()
        if dir not in self.mDirs:
            self.mDirs[dir] = GetProjectFile(dir) != None
        return self.mDirs[dir]


class Project:
    def __init__(self, name):
        file = open(name, 'r')
        self.mText = file.read()
        file.close()
        
    def HasFile(self, name):
        return re.search(name, self.mText, re.I) != None #re.S
    

def ParseArgs( argv ):
    dir = ''
    verbose = False
    
    for arg in argv:
        if IsSwitch(arg) and arg[1:].lower().startswith('v'):
            verbose = True
        elif os.path.isdir(arg):
            dir = arg
    
    if dir == '':
        dir = os.getcwd()
        
    return dir, verbose


if __name__ == '__main__':
    dir, verbose = ParseArgs(sys.argv)
    
    total = 0
    projects = {}
    for file in RecurseDirectory(dir, HasProjectFile(), False):
        dirname = os.path.dirname(file)
        projectName = GetProjectFile(dirname)
        CHECK( os.path.isfile(projectName), 'Project file does not exist.' )
        
        if projectName not in projects:
            projects[projectName] = Project(projectName)
            
        basename = os.path.basename(file)
        if not projects[projectName].HasFile(basename):
            total += 1
            print(('%s not found in %s' % (basename, os.path.basename(os.path.abspath(projectName)))))
            
    print(('\n%d files not found' % total))

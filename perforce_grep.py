import os, sys, re, datetime, Perforce, Utils

class SearchLocations:
    def __init__(self):
        self.mDirectories = []

    def ParseDirectories(self, category, component, branch):
        if not category:
            self.mDirectories.extend( Perforce.GetDirectories('//SEABU/ProductSource') )
        else:
            self.mDirectories.append('//SEABU/ProductSource/%s' % category)
            
        if not component:
            categories = self.mDirectories
            self.mDirectories = []
            for dir in categories:
                self.mDirectories.extend( Perforce.GetDirectories(dir) )
        else:
            categories = self.mDirectories
            self.mDirectories = []
            for dir in categories:
                self.mDirectories.append('%s/%s' % (dir, component))
        
        if not branch:
            components = self.mDirectories
            self.mDirectories = []
            for dir in components:
                self.mDirectories.extend( Perforce.GetDirectories(dir) )
        else:
            components = self.mDirectories
            self.mDirectories = []
            for dir in components:
                self.mDirectories.append('%s/%s' % (dir, branch))
                
    def AddDirectory(self, dir):
        self.mDirectories.append(dir)

    def GetDirectories(self):
        return self.mDirectories
    

def PrintMatch(match):
    str = match.string
    start = str.rfind('\n', 0, match.start()) + 1 if str.rfind('\n', 0, match.start()) != -1 else 0
    end = str.find('\n', match.start()) if str.find('\n', match.start()) != -1 else len(str)
    return '(%d): %s' % (str[:start].count('\n') + 1, str[start:end])


def GrepFile(search, filename, ignoreCase):
    if not Perforce.IsFileInDepot(filename):
        print('ERROR: %s is not in the depot.' % filename)
        return

    contents = Perforce.GetFileContents(filename)
    if ignoreCase:
        regex = re.compile(search, re.I | re.S)
    else:
        regex = re.compile(search, re.S)
    
    for match in regex.finditer(contents):
        print('%s %s' % (filename, PrintMatch(match)))
    

def PrintTiming(verbose, startTime, endTime = None):
    if not verbose:
        return
    
    if startTime:
        print('Started                 :  ' + startTime.strftime( '%I:%M:%S %p' ))
    elif endTime:
        print('Finished                :  ' + endTime.strftime( '%I:%M:%S %p' ))
        elapsed = endTime - startTime
        hours = int( elapsed.seconds / 3600 )
        minutes = int( ( elapsed.seconds % 3600 ) / 60 )
        seconds = int( ( elapsed.seconds % 3600 ) % 60 )
        print('Total time for operation:  %02d:%02d:%02d:%03d' % ( hours, minutes, seconds, elapsed.microseconds / 1000 ))


def ParseCommandLine(args):
    search = None
    category = None
    branch = None
    version = None
    component = None
    ignoreCase = False
    componentsTxt = False
    path = None
    verbose = False
    i = 0    
    while i < len(args):
        arg = args[i]
        param = arg.startswith('-') or arg.startswith('/')
        
        if param and (arg[1:].lower().startswith('t') or arg[1:].lower() == 'category') and i + 1 < len(args): # type or category
            i += 1
            category = args[i].strip()
            if not category.lower().endswith('s'):
                category += 's'
        elif param and arg[1:].lower().startswith('b') and i + 1 < len(args):   # branch
            i += 1
            branch = args[i].strip()
        elif param and arg[1:].lower().startswith('version') and i + 1 < len(args):    # version
            i += 1
            version = args[i].strip()
        elif param and arg[1:].lower().startswith('c') and i + 1 < len(args):   # component
            i += 1
            component = args[i].strip()
        elif param and arg[1:].lower().startswith('p') and i + 1 < len(args):   # depot path
            i += 1
            path = args[i].strip()
        elif param and arg[1:].lower() == 'i':                                  # ignore case
            ignoreCase = True
        elif param and arg[1:].lower().startswith('d'):                         # dependencies
            componentsTxt = True
        elif param and arg[1:].lower().startswith('verbose'):                   # verbose
            verbose = True
        else:
            search = arg
        i += 1
        
    if not search:
        print('Must specify some string to search for!')
        sys.exit(2)
        
    return search, component, version, branch, category, path, ignoreCase, componentsTxt, verbose


if __name__ == '__main__':
    search, component, version, branch, category, path, ignoreCase, componentsTxt, verbose = ParseCommandLine(sys.argv[1:])
    #print 'search = %s' % search
    #print 'component = %s' % component
    #print 'version = %s' % version
    #print 'branch = %s' % branch
    #print 'category = %s' % category
    #print 'path = %s' % path
    #print 'ignoreCase = %s' % ignoreCase
    #print 'componentsTxt = %s' % componentsTxt

    startTime = datetime.datetime.now()
    Utils.PrintTiming(startTime, None, verbose)
    
    locations = SearchLocations()
    if path:
        locations.AddDirectory(path)
    else:
        locations.ParseDirectories(category, component, branch)
        
    if componentsTxt:
        for dir in locations.GetDirectories():
            path = dir
            if not path.endswith('/'):
                path += '/'
            if not path.lower().endswith('components.txt'):
                path += 'Components.txt'
            GrepFile(search, path, ignoreCase)
    else:
        for dir in locations.GetDirectories():
            for file in Perforce.GetFiles(dir):
                GrepFile(search, file, ignoreCase)

    Utils.PrintTiming(startTime, datetime.datetime.now(), verbose)

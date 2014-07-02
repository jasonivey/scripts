import os, sys, re, datetime

def IsDebugLog(name):
    return re.search('DebugLog\.txt', name, re.I)


def SortByTime( x, y ):
    return cmp(y.mElapsed, x.mElapsed)


def SortByName( x, y ):
    return cmp(x.mName.lower(), y.mName.lower())


class TestTiming:
    def __init__(self, name, elapsed):
        self.mName = name
        self.mElapsed = elapsed

    def __str__(self):
        #return '%s,%s\n' % (self.mElapsed, self.mName)
        return '%9d.%06d,%s\n' % (self.mElapsed.seconds, self.mElapsed.microseconds, self.mName)


class Tests:
    def __init__(self, verbose, sortByTime, sortByName):
        self.mConfigurations = {}
        self.mVerbose = verbose
        self.mSortByTime = sortByTime
        self.mSortByName = sortByName
        
    def AddTest(self, filename, testname, elapsed):
        config = os.path.basename( os.path.dirname(filename) ).lower()
        if config not in list(self.mConfigurations.keys()):
            self.mConfigurations[config] = []
        self.mConfigurations[config].append( TestTiming(testname, elapsed) )

    def __str__(self):
        retval = ''
        configs = list(self.mConfigurations.keys())
        configs.sort()
        for config in configs:
            retval += '\n%s\n%s\n' % (config, '-' * 80)
            if self.mSortByName:
                self.mConfigurations[config].sort( cmp=SortByName )
            elif self.mSortByTime:
                self.mConfigurations[config].sort( cmp=SortByTime )
            total = datetime.timedelta(0)
            for test in self.mConfigurations[config]:
                if self.mVerbose:
                    retval += '%s' % test
                total += test.mElapsed
            #retval += '%s total seconds\n' % total
            retval += '%9d.%06d total seconds\n' % (total.seconds, total.microseconds)
        return retval
    
    
def RoundMicroSecond(microsecond):
    while microsecond > 1000000:
        microsecond /= 10
    return microsecond

    
def IsSwitch(arg):
    return arg.startswith('-') or arg.startswith('/')

    
def ParseArgs(args):
    verbose = False
    sortByTime = True
    sortByName = False
    dir = None
    foundName = False
    foundTime = False
    
    for arg in args:
        if IsSwitch(arg) and arg[1:].lower().startswith('v'):   # output the entire test list
            verbose = True
        if IsSwitch(arg) and arg[1:].lower().startswith('n'):   # sort by name
            sortByName = True
            sortByTime = False
            foundName = True
        if IsSwitch(arg) and arg[1:].lower().startswith('t'):   # sort by time
            sortByTime = True
            sortByName = False
            foundTime = True
        elif os.path.isdir(arg):                                # explicitly specify the directory to parse
            dir = os.path.abspath(arg)
    
    if not dir:
        dir = os.getcwd()
    
    if foundName and foundTime:
        print('ERROR: Can\'t specify to sort by both name and time on the command line.')
        sys.exit(2)
    if not verbose:
        sortByTime = sortByName = False
        
    return verbose, sortByTime, sortByName, dir


def RecurseDirectory( dir, function ):
    paths = []
    for root, dirs, files in os.walk( dir ):
        for file in files:
            if not function or function(os.path.join( root, file )):
                paths.append( os.path.join( root, file ) )
    return paths

    
if __name__ == '__main__':
    verbose, sortByTime, sortByName, dir = ParseArgs(sys.argv)
    pattern = r'Ending Unit Test: (?P<name>[^ ]+) - Elapsed Time: (?P<second>[^. ]+)(?:\.(?P<microsecond>[^ ]*))? seconds'

    tests = Tests(verbose, sortByTime, sortByName)
    for name in RecurseDirectory(dir, IsDebugLog):
        file = open(name, 'r')
        data = file.read()
        file.close()
        
        test_count = data.count('Ending Unit Test')
        total_count = 0
        for i in re.finditer(pattern, data):
            test_name = i.group('name')
            if i.lastgroup == 'microsecond':
                microsecond = RoundMicroSecond( int( i.group('microsecond') ) )
            else:
                microsecond = 0
            elapsedTime = datetime.timedelta(0, int( i.group('second') ), microsecond)
            tests.AddTest(name, test_name, elapsedTime)
            total_count += 1
        
        if test_count != total_count:
            print('Test count (%d) didn\'t match regex iterator count (%d) in file %s' % (count, total, name))

    print(tests)

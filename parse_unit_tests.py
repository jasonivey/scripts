import os, sys, re, Utils
from mx.DateTime import DateTimeDeltaFromSeconds

def IsDebugLog(name):
    return re.search('DebugLog\.txt', name, re.I)

def ReadFile( filename ):
    file = open( filename, 'r' )
    data = file.read()
    file.close()
    return data

class Test:
    def __init__(self, name, elapsed):
        self.mName = name
        self.mElapsed = DateTimeDeltaFromSeconds(elapsed)
    
    def __str__(self):
        return '\t%9.6f seconds : %s\n' % (self.mElapsed.seconds, self.mName)
    
class TestSuite:
    def __init__(self, name):
        self.mName = name
        self.mTests = []
        self.mTotal = DateTimeDeltaFromSeconds(0)
        
    def AddTest(self, name, elapsed):
        self.mTests.append( Test(name, elapsed) )
        self.mTotal += DateTimeDeltaFromSeconds(elapsed)

    def __str__(self):
        retstr  = 'Suite: %s\n' % self.mName
        retstr += 'Total Time: %9.6f seconds\n' % self.mTotal.seconds
        retstr += 'Test Count: %d\n' % len(self.mTests)
        for test in self.mTests:
            retstr += str(test)
        return retstr
    
    def GetTotalTime(self):
        return self.mTotal.seconds

if __name__ == '__main__':
    pattern = r'Ending Unit Test: (?P<test_suite>[^.]+)\.(?P<test_name>[^ ]+) - Elapsed Time: (?P<time>\d+\.\d*) seconds'
    regex = re.compile(pattern)
    suites = {}
    
    for filename in Utils.RecurseDirectory( os.getcwd(), IsDebugLog, False ):
        data = ReadFile(filename)
        for i in regex.finditer(data):
            suite = i.group('test_suite')
            key = suite.lower()
            test = i.group('test_name')
            elapsed = i.group('time')
            
            if key not in list(suites.keys()):
                suites[key] = TestSuite(suite)
                
            suites[key].AddTest(test, float(elapsed))
    
    total = 0
    for key in list(suites.keys()):
        print((suites[key]))
        total += suites[key].GetTotalTime()
        
    print(('Total Time For Tests: %9.6f seconds' % total))


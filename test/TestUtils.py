import os, sys, unittest, re

sys.path.append( os.path.abspath('..') )
from Utils import *

class TestAssertionAndError(unittest.TestCase):
    def setUp(self):
        self.mStdErr = sys.stderr
        self.mFile = open('stderr.log', 'w+')
        sys.stderr = self.mFile

    def tearDown(self):
        if not self.mFile.closed:
            self.mFile.close()
        if os.path.isfile('stderr.log'):
            os.remove('stderr.log')
        if sys.stderr != self.mStdErr:
            sys.stderr = self.mStdErr
        
    def GetStderr(self):
        self.assertFalse( self.mFile.closed )
        self.mFile.seek(0)
        data = self.mFile.read()
        self.mFile.seek(0)
        return data
    
    def testError(self):
        input = 'This should go to standard error pipe.'
        Error(input)
        output = self.GetStderr()
        self.assertEqual('\nERROR: %s\n' % input, output, 'Didn\'t write to stderr like expected.')
        
    def testCHECK(self):
        self.assert_( CHECK(True, 'This should not fail') )
        self.assertRaises( AssertionError, CHECK, False, 'This is going to fail' )


class TestCompareIgnoreCase(unittest.TestCase):
    def testCompareIgnoreCase(self):
        str1 = 'tHIS IS a tESt'
        str2 = 'this is a test'
        self.assert_(CompareIgnoreCase(str1, str2) == 0)
        self.assertFalse(cmp(str1, str2) == 0)
        str1 = 'this should fail'
        self.assert_(CompareIgnoreCase(str1, str2) == 1)
        str1 = 'THIS IS ALSO A TEST'
        self.assert_(CompareIgnoreCase(str1, str1) == 0)
        self.assert_(cmp(str1, str1) == 0)
        str1 = 'this is also a test'
        self.assert_(CompareIgnoreCase(str1, str1) == 0)
        self.assert_(cmp(str1, str1) == 0)


class TestFindSandbox(unittest.TestCase):
    def setUp(self):
        self.mStderr = sys.stderr
        sys.stderr = None
        self.mTempDir = os.path.join(os.path.dirname(sys.argv[0]), 'tempdir')
        os.mkdir(self.mTempDir)
        self.CreateFile( os.path.join(self.mTempDir, 'stop'), 'stop here.' )
        
    def CreateFile(self, name, text):
        file = open(name, 'w')
        file.write(text)
        file.close()

    def tearDown(self):
        if sys.stderr != self.mStderr:
            sys.stderr = self.mStderr
        if os.path.isdir(self.mTempDir):
            os.remove(os.path.join(self.mTempDir, 'stop'))
            os.removedirs(self.mTempDir) 
            
    def testFindSandbox(self):
        curdir = os.path.join(self.mTempDir, 'dir1', 'dir2', 'dir3')
        os.makedirs(curdir)
        self.assertRaises( AssertionError, FindSandbox, curdir )
        os.removedirs(curdir)
        sandboxtext = os.path.join(self.mTempDir, 'dir1', 'dir2', 'sandbox.txt')
        curdir = os.path.join(self.mTempDir, 'dir1', 'dir2', 'ws', 'component', 'dev', 'subdir1', 'subdir2')
        os.makedirs(curdir)
        self.CreateFile(sandboxtext, 'sandbox file')
        self.assert_( FindSandbox(curdir) )
        os.remove(sandboxtext)
        os.removedirs(curdir)
    
if __name__ == '__main__':
    unittest.main()

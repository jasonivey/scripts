import os, sys, stat, unittest

sys.path.append( os.path.abspath('..') )
from Perforce import *

class TestTorrent(unittest.TestCase):
    #def setUp(self):

    def testListLabel(self):
        category, component, branch = ListLabel('BuildNumber_19321')
        self.assertEqual( category, 'Component' )
        self.assertEqual( component, 'VProServer' )
        self.assertEqual( branch, 'Main' )

if __name__ == '__main__':
    unittest.main()

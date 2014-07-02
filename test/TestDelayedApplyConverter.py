import os, sys, unittest

sys.path.append( os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..')) )
from DelayedApplyConverter import *

class TestTorrent(unittest.TestCase):
    def testParse(self):
        DelayedApply('d:/sandboxes/main/ws', os.path.join(os.path.dirname(sys.argv[0]), 'create_volume.job'))
        
if __name__ == '__main__':
    unittest.main()

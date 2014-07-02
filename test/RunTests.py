import os, sys, re

sys.path.append( os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..')) )
from DelayedApplyConverter import *

if __name__ == '__main__':
    dir = os.path.dirname(sys.argv[0])
    for file in os.listdir(dir):
        if re.match(r'Test\w*\.py', file, re.I):
            print('Running %s...' % file)
            os.system( os.path.join(dir, file) )


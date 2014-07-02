#Copyright (c)2005, 2006, 2008 Symantec Corporation. All rights reserved.
#
#THIS SOFTWARE CONTAINS CONFIDENTIAL INFORMATION AND TRADE SECRETS OF SYMANTEC
#CORPORATION. USE, DISCLOSURE OR REPRODUCTION IS PROHIBITED WITHOUT THE PRIOR
#EXPRESS WRITTEN PERMISSION OF SYMANTEC CORPORATION.
#
#The Licensed Software and Documentation are deemed to be "commercial computer
#software" and "commercial computer software documentation" as defined in FAR
#Sections 12.212 and DFARS Section 227.7202.
import os, sys, stat, unittest

sys.path.append( os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..')) )
import Raptor

def IsSourceFileAndWritable(filename):
    return( filename.lower().endswith('.cpp') or \
            filename.lower().endswith('.inl') or \
            filename.lower().endswith('.h') ) and \
            os.stat(filename)[stat.ST_MODE] & stat.S_IWRITE != 0
#def IsSourceFileAndWritable(filename):
#    return( filename.lower().endswith('.cpp') or \
#            filename.lower().endswith('.inl') or \
#            filename.lower().endswith('.h') )


def EndsWithNewline( filename ):
    file = open(filename, 'r')
    data = file.read()
    file.close()
    value = data.lstrip('\t ').endswith('\n')
    if not value:
        print filename
    return value


class NewLinesTest(unittest.TestCase):
    def testSource(self):
        raptor = Raptor.Sandbox()
        for component in raptor.items.keys():
            found = False
            for platforms in raptor.items[component].platforms:
                if platforms.lower().startswith('linux'):
                    found = True
            if not found or not raptor.items[component].dir.lower().startswith(raptor.wsdir.lower()):
                continue
            
            print component
            for root, dirs, files in os.walk( raptor.items[component].dir ):
                for file in files:
                    if IsSourceFileAndWritable( os.path.join(root, file) ):
                        self.assert_( EndsWithNewline( os.path.join(root, file) ) )

if __name__ == '__main__':
    unittest.main()

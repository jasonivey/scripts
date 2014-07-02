import os, sys, uuid, unittest, CompileSource

class TestSourceFiles(unittest.TestCase):
    def setUp(self):
        self.assert_( 'TEMP' in os.environ )    
        self.mTempDirectory = os.path.join( os.environ['TEMP'], 'VerifySource-%s' % uuid.uuid1() )
        os.mkdir(self.mTempDirectory)

    def tearDown(self):
        #os.remove(os.path.join(self.mTempDirectory, 'buildlog.txt'))
        #os.rmdir(self.mTempDirectory)
        pass
        
    def testComileSourceIndividually(self):
        dir = os.getcwd()
        sources = []
        for root, dirs, files in os.walk(dir):
            for file in files:
                if CompileSource.IsSourceFile(os.path.join(root, file)):
                    sources.append(os.path.join(root, file))
    
        for source in sources:
            if source.lower().endswith('.h'):
                self.assert_( CompileSource.CompileHeader(source, self.mTempDirectory) )
            else:
                #CompileSource.CompileCpp(source)
                pass


if __name__ == '__main__':
    unittest.main()
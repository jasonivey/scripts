import os, sys, re, time, Utils

class FindFixes:
    def __init__(self, dir):
        self.mAcceptFiles = re.compile( '^.*\.(?:h|hpp|c|cpp|inl)$', re.IGNORECASE )
        self.mBadDirs = re.compile( '(?:wsfiles|win32_debug|win32_release)', re.IGNORECASE )
        self.mFixes = {}
        self.mCount = 0
        self.mFiles = 0
        self.mTotalFiles = 0
        self.SearchForFixes(dir)
        
    def __call__(self, file):
        return not self.mBadDirs.search(file) and self.mAcceptFiles.match(file)
    
    def __str__(self):
        values = []
        types = list(self.mFixes.keys())
        types.sort()
        for fix in types:
            values.append( [ fix, self.mFixes[fix] ] )
        formatter = Utils.TableFormatter('Fix_ Report', ['Type', 'Count'], values)
        return '%s\nFound %d instances of \'fix_\' in %d files, %d total files searched.' % ( formatter, self.mCount, self.mFiles, self.mTotalFiles )
    
    def GetFileContents(self, name):
        f = open(name, 'r')
        data = f.read()
        f.close()
        return data
    
    def SearchForFixes(self, dir):
        regex = re.compile( r'fix_[^-\s!\'#$%&()*+,\./:;<=>?@\[/\]\^_{|}~]*', re.I )
        for file in Utils.RecurseDirectory(dir, self):
            self.mTotalFiles += 1
            data = self.GetFileContents(file)
            found = False
            for i in regex.finditer(data):
                key = i.group().lower()
                if key in list(self.mFixes.keys()):
                    self.mFixes[key] += 1
                else:
                    self.mFixes[key] = 1
                if not found:
                    self.mFiles += 1
                found = True
                self.mCount += 1


if __name__ == '__main__':
    begin = time.clock()    
    finder = FindFixes(os.getcwd())
    print(str(finder))
    end = time.clock()
    print('Total time elapsed: %f seconds' % round(end - begin, 3))

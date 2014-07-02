import os, sys, re, Utils, datetime

def CountLinesInFile( filename ):
    file = open( filename, 'r' )
    lines = file.readlines();
    file.close()
    
    count = 0
    inComment = False
    
    for line in lines:
        if len(line.strip()) == 0:
            continue
        elif not inComment and line.strip().startswith( '//' ):
            continue
        elif line.strip().startswith( '/*' ) and line.find( '*/' ) == -1:
            inComment = True
            continue

        if not inComment and line.find( '/*' ) != -1:
            str = line.strip()
            while str != '':
                index = str.find( '/*' )
                if index != -1:
                    str = str[ index + 2 : len(str) ].strip()
                    index = str.find( '*/' )
                    if index != -1:
                        str = str[ index + 2 : len(str) ].strip()
                    else:
                        inComment = True
                else:
                    str = ''
                    inComment = False
            if line.strip().find( '/*' ) == 0:
                continue

        if inComment and line.find( '*/' ) != -1:
            inComment = False
            if line.find( '/*' ) == -1:
                continue
        if not inComment:
            count = count + 1
            
    return count
    

def IterateSourceCode( srcDir ):
    print('Searching for files in ' + srcDir)
    dirs = []
    count = 0
    
    for f in os.listdir( srcDir ):
        if f.find( '?' ) != -1 or \
           f.find( 'System Volume Information' ) != -1:
            continue

        pathname = '%s\\%s' % ( srcDir, f )
        extension = os.path.splitext( pathname )[1].lower()
        
        if os.path.isdir( pathname ) and os.path.basename( pathname ).lower() != 'wsfiles':
            dirs.append( pathname )
        elif( extension == '.cpp' or \
              extension == '.c' or \
              extension == '.h' or \
              extension == '.hpp' or \
              extension == '.inl' ) and \
             IsFileInDepot( pathname ):
            count = count + CountLinesInFile( pathname )

    for d in dirs:
        count = count + IterateSourceCode( d )
        
    return count


class IsSourceFile:
    def __init__(self):
        self.mRegex = re.compile( '^.*\.(?:h|hpp|c|cpp|inl|py)$', re.IGNORECASE )
    
    def __call__(self, file):
        return self.mRegex.match(file)


class Stats:
    def __init__(self, lines, blank, comment, code):
        self.mFileCount = 1
        self.mLines = lines
        self.mBlankLines = blank
        self.mCommentLines = comment
        self.mCodeLines = code
    
    def Update(self, lines, blank, comment, code):
        self.mFileCount += 1
        self.mLines += lines
        self.mBlankLines += blank
        self.mCommentLines += comment
        self.mCodeLines += code


class LineCounts:
    def __init__(self, dir):
        self.mFiles = Utils.RecurseDirectory(dir, IsSourceFile())
        self.mFileCount = len(self.mFiles)
        self.mStats = {}
        self.ParseFiles()
        
    def ParseFiles(self):
        script = os.path.join( os.path.dirname(sys.argv[0]), 'sclc.pl' )
        regex = re.compile( r'\n\s*?(?P<lines>\d+?)\s+?(?P<blank>\d+?)\s+?(?P<comments>\d+?)\s+?(?P<code>\d+?)[^\d][^(]*\((?P<language>[^)]*?)\)', re.I | re.S )
        for file in self.mFiles:
            command = 'perl %s "%s"' % (script, file)
            output = os.popen4( command, 't' )[1].read()
            self.InsertStats( regex.search(output), file )

    def InsertStats(self, match, file):
        if not match:
            Utils.LogError('ERROR: File, \'%s\' did not output the expected counts.\n' % os.path.basename(file))
            return
    
        language = match.group('language')
        lines = int( match.group('lines') )
        blank = int( match.group('blank') )
        comments = int( match.group('comments') )
        code = int( match.group('code') )
    
        if language in list(self.mStats.keys()):
            self.mStats[language].Update( lines, blank, comments, code )
        else:
            self.mStats[language] = Stats( lines, blank, comments, code )
            
    def __str__(self):
        names = ['Language', 'Files', 'Total Lines', 'Blank Lines', 'Comments', 'Lines Of Code']
        values = []
        for language in list(self.mStats.keys()):
            values.append( [language,
                            str(self.mStats[language].mFileCount),
                            str(self.mStats[language].mLines),
                            str(self.mStats[language].mBlankLines),
                            str(self.mStats[language].mCommentLines),
                            str(self.mStats[language].mCodeLines)] )
        return '%s' % Utils.TableFormatter( 'Lines Of Code Report', names, values )
    
    
if __name__ == '__main__':
    beginTime = datetime.datetime.now()
    print('Started                 :  ' + beginTime.strftime( '%I:%M:%S %p' ))
    print('%s' % LineCounts(os.getcwd()))
    endTime = datetime.datetime.now()
    print('Finished                :  ' + endTime.strftime( '%I:%M:%S %p' ))
    elapsed = endTime - beginTime
    hours = int( elapsed.seconds / 3600 )
    minutes = int( ( elapsed.seconds % 3600 ) / 60 )
    seconds = int( ( elapsed.seconds % 3600 ) % 60 )
    print('Total time for operation:  %02d:%02d:%02d:%03d' % ( hours, minutes, seconds, elapsed.microseconds / 1000 ))

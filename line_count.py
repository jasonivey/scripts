#!/usr/bin/env python
# vim: aw:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from pathlib import Path
import datetime
import os
import re
import subprocess
import sys
import tableformatter as tf

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


def IsSourceFile(file_path):
    regex = re.compile('^.*\.(?:h|hpp|c|cpp|inl|py)$', re.IGNORECASE)
    return regex.match(file_path.resolve().as_posix())


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
    def __init__(self):
        self.mFileCount = 0
        self.mStats = {}
        self.ParseFiles()

    def ParseFiles(self):
        script_path = Path(os.path.expandvars('${HOME}/scripts/sclc.pl'))
        regex = re.compile(r'\n\s*?(?P<lines>\d+?)\s+?(?P<blank>\d+?)\s+?(?P<comments>\d+?)\s+?(?P<code>\d+?)[^\d][^(]*\((?P<language>[^)]*?)\)', re.I | re.S)
        for file_path in Path('.').rglob('*'):
            if not IsSourceFile(file_path):
                continue
            self.mFileCount += 1
            args = ['perl', f'"{script_path.resolve().as_posix()}"', f'"{file_path.resolve().as_posix()}"']
            completed_process = subprocess.run(args, capture_output=True, shell=True, check=True, text=True)
            self.InsertStats(regex.search(completed_proces.stdout), file_path)

    def InsertStats(self, match, file_path):
        if not match:
            print(f'ERROR: File, "{file_path.name}" did not output the expected counts.\n')
            return

        language = match.group('language')
        lines = int( match.group('lines') )
        blank = int( match.group('blank') )
        comments = int( match.group('comments') )
        code = int( match.group('code') )
        if language in list(self.mStats.keys()):
            self.mStats[language].Update(lines, blank, comments, code)
        else:
            self.mStats[language] = Stats(lines, blank, comments, code)

    def __str__(self):
        names = ['Language', 'Files', 'Total Lines', 'Blank Lines', 'Comments', 'Lines Of Code']
        values = []
        for language in list(self.mStats.keys()):
            values.append([language,
                           str(self.mStats[language].mFileCount),
                           str(self.mStats[language].mLines),
                           str(self.mStats[language].mBlankLines),
                           str(self.mStats[language].mCommentLines),
                           str(self.mStats[language].mCodeLines)])
        return tf.generate_table(values, names)


if __name__ == '__main__':
    beginTime = datetime.datetime.now()
    print(('Started                 :  ' + beginTime.strftime( '%I:%M:%S %p' )))
    print(str(LineCounts()))
    endTime = datetime.datetime.now()
    print(('Finished                :  ' + endTime.strftime( '%I:%M:%S %p' )))
    elapsed = endTime - beginTime
    hours = int( elapsed.seconds / 3600 )
    minutes = int( ( elapsed.seconds % 3600 ) / 60 )
    seconds = int( ( elapsed.seconds % 3600 ) % 60 )
    print(('Total time for operation:  %02d:%02d:%02d:%03d' % ( hours, minutes, seconds, elapsed.microseconds / 1000 )))


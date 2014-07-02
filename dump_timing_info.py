import os, string, shutil, sys, re
from stat import *
from .Utils import *


class TimingInfo:
    "Structure to encapsulate a piece of timing info."
    def __init__(self):
        self.Description = ''
        self.TotalCalls = 0
        self.TotalTime = float(0)
        self.AverageTime = float(0)
        
    def __eq__(self, other):
        return self.Description.lower() == other.Description.lower()

    def SetAverageTime(self, average):
        self.AverageTime = max( self.AverageTime, average )
        
    def SortDescription( self, other ):
        return CompareIgnoreCase( self.Description, other.Description )

    def SortTotalCalls( self, other ):
        return other.TotalCalls - self.TotalCalls
    
    def SortTotalTime( self, other ):
        return cmp( self.TotalTime, other.TotalTime )

    def SortAverageTime( self, other ):
        return cmp( self.AverageTime, other.AverageTime )


def SortByAverageCall( x, y ):
    if x.SortAverageTime(y) == 0:
        if x.SortTotalTime(y) == 0:
            if x.SortTotalCalls(y) == 0:
                return x.SortDescription(y)
            else:
                return x.SortTotalCalls(y)
        else:
            return x.SortTotalTime(y)
    else:
        return x.SortAverageTime(y)

    
def SortByCallCount( x, y ):
    if x.SortTotalCalls(y) == 0:
        if x.SortAverageTime(y) == 0:
            if x.SortTotalTime(y) == 0:
                return x.SortDescription(y)
            else:
                return x.SortTotalTime(y)
        else:
            return x.SortAverageTime(y)
    else:
        return x.SortTotalCalls(y)


def SortByTotalTime( x, y ):
    if x.SortTotalTime(y) == 0:
        if x.SortTotalCalls(y) == 0:
            if x.SortAverageTime(y) == 0:
                return x.SortDescription(y)
            else:
                return x.SortAverageTime(y)
        else:
            return x.SortTotalCalls(y)
    else:
        return x.SortTotalTime(y)
    

class IsDebugLog:
    def __init__(self, release, debug):
        self.mRelease = release
        self.mDebug = debug
        
    def __call__(self, file):
        return( self.mRelease and re.search( r'_release\\(?:DebugLog\.txt|SmeGuiDebug\.log)', file, re.I ) ) or \
              ( self.mDebug and re.search( r'_debug\\(?:DebugLog\.txt|SmeGuiDebug\.log)', file, re.I ) )


def GetDebugLogContents( filename ):
    file = open( filename, 'r' )
    lines = file.readlines()
    file.close()
    return lines


def OutputTimingInfo( timinginfos, output ):
    class Column:
        gap = 2

        def __init__( self, name ):
            self.name = name
            self.width = len( name )
            
        def GetWidth( self ):
            return self.width + self.gap

        def SetWidth( self, newWidth ):
            self.width = max( self.width, newWidth )
            
        def GetName( self ):
            return self.name
        
    cols = {}
    cols[1] = Column( "Description" )
    cols[2] = Column( "| Total Calls" )
    cols[3] = Column( "| Total Time" )
    cols[4] = Column( "| Average Time" )
    for timing in timinginfos:
        cols[1].SetWidth( len( timing.Description ) + 1 )
        cols[2].SetWidth( len( '%d' % timing.TotalCalls ) )
        cols[3].SetWidth( len( '%0.3f' % timing.TotalTime ) )
        cols[4].SetWidth( len( '%0.6f' % timing.AverageTime ) )
    
    file = open( output, 'w' )
    j = 0
    while j < 3 :
        
        totalWidth = cols[1].GetWidth() + cols[2].GetWidth() + cols[3].GetWidth()
        totalWidth += cols[4].GetWidth() - Column.gap - 3
        
        file.write( '\n' + totalWidth * '=' + '\n' )
        if j == 0:
            file.write( 'Timing Information - Sorted by Average Call Time\n' )
            timinginfos.sort( cmp=SortByAverageCall )
        elif j == 1:
            file.write( 'Timing Information - Sorted by Number of Calls\n' )
            timinginfos.sort( cmp=SortByCallCount )
        else:
            file.write( 'Timing Information - Sorted by Total Time\n' )
            timinginfos.sort( cmp=SortByTotalTime )
            
            
        file.write( totalWidth * '=' + '\n' )
        for i in range(1,5):
            file.write( ('%-' + str(cols[i].GetWidth() - 1) + 's') % cols[i].GetName() )
        file.write( '\n' )
        
        file.write( totalWidth * '-' + '\n' )
        grandTotalCalls = 0
        grandTotalTime = 0.00
        grandTotalAverage = 0.00
        for timing in timinginfos:
            grandTotalCalls = grandTotalCalls + timing.TotalCalls
            grandTotalTime = grandTotalTime + timing.TotalTime
            grandTotalAverage = grandTotalAverage + timing.AverageTime
            totalTime = '%0.3f' % timing.TotalTime
            averageTime = '%0.6f' % timing.AverageTime
            file.write( ('%-' + str(cols[1].GetWidth() - 1) + 's' ) % timing.Description )
            file.write( ('%' + str(cols[2].GetWidth() - 2) + 'd' ) % timing.TotalCalls )
            file.write( ' ' * (cols[3].GetWidth() - len(totalTime) - 1) + totalTime )
            file.write( ' ' * (cols[4].GetWidth() - len(averageTime) - 1) + averageTime )
            file.write( '\n' )

        file.write( totalWidth * '-' + '\n' )
        totalTime = '%0.3f' % grandTotalTime
        averageTime = '%0.6f' % grandTotalAverage
        file.write( ('%-' + str(cols[1].GetWidth() - 1) + 's') % 'Totals' )
        file.write( ('|%' + str(cols[2].GetWidth() - 3) + 'd') % grandTotalCalls )
        file.write( ' |' + (' ' * (cols[3].GetWidth() - len(totalTime) - 3)) + totalTime)
        file.write( ' |' + (' ' * (cols[4].GetWidth() - len(averageTime) - 3)) + averageTime)
        file.write( '\n' )
        file.write( '=' * totalWidth + '\n' )
        j = j + 1
        
    file.close()
    sys.stdout.write('\n')


def DumpTimingInfo( files, output ):

    print('Parsing timing information...')    
    timinginfos = []
    pattern = '^ *((?:Bitmap|Tree|Const0|Const1|RunList(?:Base|16|32|64))(?:Node)?(?:::| )?.*) *: *(\d+) *(\d+\.\d+)(?: *(\d+\.\d+))? *$'
    regex = re.compile( pattern, re.IGNORECASE )
    for file in files:
        lines = GetDebugLogContents( file )
        sys.stdout.write('.')
        
        for line in lines:
            result = regex.match( line )
            if result:
                timing = TimingInfo()
                timing.Description = result.group(1).strip()
                timing.TotalCalls = int( result.group(2) )
                timing.TotalTime = float( result.group(3) )
                if( result.group(4) ):
                    timing.AverageTime = float( result.group(4).strip() )
                
                if timing in timinginfos:
                    i = timinginfos.index( timing )
                    timinginfos[i].TotalCalls += timing.TotalCalls
                    timinginfos[i].TotalTime += timing.TotalTime
                    timinginfos[i].SetAverageTime( timing.AverageTime )
                else:
                    timinginfos.append( timing )
                    timinginfos.sort( cmp=lambda x,y: cmp(x.Description.lower(), y.Description.lower()) )
                   
    OutputTimingInfo( timinginfos, output )


if __name__ == '__main__':

    dir = os.getcwd()
    debug = False
    release = False
    count = len( sys.argv )
    i = 0
    output = 'out.txt'
    if count > 1:
        while( i < count ):
            if sys.argv[i].lower().find( 's' ) == 1 and i + 1 < count:
                i = i + 1
                dir = sys.argv[i]
            if sys.argv[i].lower().find( 'o' ) == 1 and i + 1 < count:
                i = i + 1
                output = sys.argv[i]
            if sys.argv[i].lower().find( 'c' ) == 1 and i + 1 < count:
                i = i + 1
                if sys.argv[i].lower() == 'release':
                    release = True
                elif sys.argv[i].lower() == 'debug':
                    debug = True
            i = i + 1
    
    if not debug and not release:
        debug = True
        release = True

    files = RecurseDirectory( dir, IsDebugLog(release, debug) )
    
    DumpTimingInfo( files, output )
        
        
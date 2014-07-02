import os, string, sys, re
from mx.DateTime import *
from .Utils import CHECK

# Pre - main execution to set up the environment.
#  If the script resides in the same directory as the RaptorBinConfig.txt
#  get the environment variables from that.  Since this script will see a
#  significant speed improvement if P4.exe is launched locally try to find
#  that EXE in the path. Last, if the P4PORT global variable hasn't been
#  defined from the above script then set it to the default for OREM, UT, USA.
x = [x for x in sys.path if os.path.isfile(os.path.join(x, 'RaptorBinConfig.txt'))]
if len( x ):
    RAPTOR_BIN = x[0] 
    exec(open( os.path.join( RAPTOR_BIN, 'RaptorBinConfig.txt' )).read())
x = [x for x in os.environ['PATH'].split(';') if os.path.isfile( os.path.join(x, 'p4.exe') )]
if len( x ):
    if 'P4EXE' not in vars():
        global P4EXE
    P4EXE = 'p4'
    
if 'P4PORT' not in vars():
    global P4PORT
    P4PORT = r'172.16.79.3:1666'

class Change:
    "Structure to encapsulate a perforce change."
    def __init__(self):
        self.mNumber = 0
        self.mDate = datetime.datetime.max
        self.mUser = ''
        self.mDescription = ''
        self.mFiles = []
    
    def __cmp__(self, other):
        return self.mNumber - other.mNumber

    
class Project:
    "Structure to encapsulate a raptor project."
    def __init__(self, name, category, branch, begin, end):
        self.mName = name
        self.mCategory = category
        self.mBranch = branch
        self.mBegin = begin
        self.mEnd = end
        
    def __eq__(self, other):
        return self.mName.lower() == other.mName.lower() and \
               self.mCategory.lower() == other.mCategory.lower() and \
               self.mBranch.lower() == other.mBranch.lower() and \
               self.mBegin == other.mBegin and self.mEnd == other.mEnd

    def __cmp__(self, other):
        return cmp( self.mName.lower(), other.mName.lower() )


def PrintHelp():
    print('Look up the arguments in the script.')
    sys.exit( 2 )
    
    
def ParseChange( lines, change, ignoreCmBuild, verbose, user ):
    
    insideChange = False
    insideDescription = False
    inFileList = False

    for line in lines:
        line = line.strip()
        line = line.strip( '\n' )
        
        if len( line ) == 0 and insideChange == True and insideDescription == True:
            insideChange = False
            insideDescription = False
            
        elif insideChange == False and line.startswith( 'Change ' ):
            insideChange = True
            parts = line.split()
            CHECK( len( parts ) == 7, 'Expecting a different \'Change\' line.' )
                 
            change.mNumber = int( parts[1] )
            dateParts = parts[5].split( '/' )
            timeParts = parts[6].split( ':' )
            change.mDate = datetime.datetime( int( dateParts[0] ), int( dateParts[1] ), int( dateParts[2] ), int( timeParts[0] ), int( timeParts[1] ), int( timeParts[2] ) )
            change.mUser = parts[3].split( '@' )[0]
            if user != '' and change.mUser.lower() != user.lower():
                return Change()
            elif ignoreCmBuild == True and change.mUser == 'orem_cm_build':
                return Change()
            
        elif len( line ) > 0 and insideChange == True:
            insideDescription = True
            if line != '-':
                if len( change.mDescription ) > 0:
                    change.mDescription += '\n'
                change.mDescription += line
                
        elif line.startswith( 'Affected files ...' ):
            if verbose:
                inFileList = True
            else:
                return change
        
        elif inFileList and verbose and line.startswith( '... //' ):
            change.mFiles.append( line )
            
    return change
    
    
def FindChanges( project, ignore, verbose, user ):
    command = P4EXE + ' -p ' + P4PORT + ' changes -t -s submitted "//SEABU/ProductSource/'
    command += project.mCategory + '/' + project.mName + '/' + project.mBranch
    command += '/"...@' + project.mBegin.strftime( '%Y/%m/%d:%H:%M:%S' )
    command += ',@' + project.mEnd.strftime( '%Y/%m/%d:%H:%M:%S' )
    lines = os.popen4( command, 't' )[1].readlines()
    
    changes = []
    for line in lines:
        line = line.strip()
        line = line.strip( '\n' )
        
        if line.lower().startswith( 'change ' ):
            change = Change()
            change.mNumber = int( line.split()[1] )
            changes.append( change )

    changes.sort()
    i = 0
    
    while i < len( changes ):
        command = P4EXE + ' -p ' + P4PORT + ' describe -s "' + str( changes[i].mNumber ) + '"'
        lines = os.popen4( command, 't' )[1].readlines()

        tmpChange = ParseChange( lines, changes[i], ignore, verbose, user )
        if tmpChange.mNumber != 0 and tmpChange.mDate != datetime.datetime.max and tmpChange.mUser != '':
            changes[i] = tmpChange
            i = i + 1
        else:
            changes.remove( changes[i] )
            
    return changes


def ListChanges( project, file, ignore, verbose, user ):
    beginStr = project.mBegin.strftime( '%Y/%m/%d %H:%M:%S' )
    endStr = project.mEnd.strftime( '%Y/%m/%d %H:%M:%S' )
    CHECK( project.mBegin != datetime.datetime.max, 'The begin date, %s, does not have a valid date.' % beginStr )
    CHECK( project.mEnd != datetime.datetime.max, 'The end date %s, does not have a valid date.' % endStr )
    
    file.write( '\n' + '-' * 79 )
    file.write( '\nListing changes between %s and %s for:\n' % ( beginStr, endStr ) )
    file.write( 'Category  : ' + project.mCategory + '\n' )
    file.write( 'Name      : ' + project.mName + '\n' )
    file.write( 'Branch    : ' + project.mBranch + '\n' ) # Doesn't matter which branch because they are garunteed to be the same
    file.write( 'Begin Date: ' + beginStr + '\n' )
    file.write( 'End Date  : ' + endStr + '\n' )

    changes = FindChanges( project, ignore, verbose, user )
    
    for change in changes:
        file.write( 'Change ' + str( change.mNumber ) + ' on ' + change.mDate.strftime( '%Y/%m/%d %H:%M:%S' ) + ' by ' + change.mUser + '.\n' )
        if len( change.mDescription ) > 0:
            file.write( '\n\t' + change.mDescription.replace('\n', '\n\t') + '\n\n' )
        else:
            file.write( '\n\tNo description of change.\n\n' )
        
        if len( change.mFiles ) > 0:
            file.write( 'Affected files ...\n\n' )
            
            for fileDesc in change.mFiles:
                file.write( fileDesc + '\n' )
                
            file.write( '\n\n' )
            
    if not len(changes):
        file.write( 'No changes submitted between two date/times.\n' )


def GetArgumentPairs(argv, i, count):
    switch = arg = argv[i]
    i = i + 1
    if switch.startswith('-') or switch.startswith('/'):
        switch = switch[1:]
    else:
        return None, arg, i
    
    arg = None
    index = switch.find('=')
    if index != -1:
        arg = switch[index + 1:]
    elif i < count and not ( argv[i].startswith('-') or argv[i].startswith('/') ):
        arg = argv[i]
        i = i + 1

    return switch, arg, i


def ParseDateTimeValue( arg ):
    # The date time argument can be specified using any of the following variants:
    #   2006/08/19:14:23:32 - Meaning August 19, 2006 at  2:23 PM and 32 seconds
    #   2006-08-19:14:23:32 - Meaning August 19, 2006 at  2:23 PM and 32 seconds
    #   06/8/19:14:23:32    - Meaning August 19, 2006 at  2:23 PM and 32 seconds
    #   6/08/5:14:23:32     - Meaning August  5, 2006 at  2:23 PM and 32 seconds
    #   6/08/5:14:23        - Meaning August  5, 2006 at  2:23 PM and 00 seconds
    #   6/08/5              - Meaning August  5, 2006 at 12:00 AM and 00 seconds
    #   98/8/19:6:53:01     - Meaning August 19, 1998 at  6:00 AM and 01 seconds
    # The following regex should parse all of the above variants
    match = re.match('^(?P<Year>(?:\d{1,2})|(?:\d{4,4}))[-/](?P<Month>\d\d?)[-/](?P<Day>\d\d?)(?::(?P<Hour>\d\d?):(?P<Minute>\d\d?)(?::(?P<Second>\d\d?))?)?$', arg)
    if not match:
        PrintHelp()
        
    year = int( match.group('Year') )
    month = int( match.group('Month') )
    day = int( match.group('Day') )
    hour = minute = 0
    second = 0.00
    if match.group('Hour'):
        hour = int( match.group('Hour') )
    if match.group('Minute'):
        minute = int( match.group('Minute') )
    if match.group('Second'):
        second = float( match.group('Second') )
        
    # If the user left off the '20' in '2000'
    currentYearAfterMillenium = now().year % 2000
    if year <= currentYearAfterMillenium:
        year = year + 2000
    # If the user left off the '19' in '1990'
    if year > currentYearAfterMillenium and year < 1990:
        year = year + 1900
    if year < 1990 or year > now().year:
        print('DATE ERROR: The year (%d) is out of the range from 1990 to %d.' % ( year, now().year ))
        PrintHelp()
    if month < 1 or month > 12:
        print('DATE ERROR: The month (%d) is greater than 12 (December).' % month)
        PrintHelp()
    if day < 1 or day > DateTime(year, month).days_in_month:
        print('DATE ERROR: The day (%d) is larger than the number of days in %s.' % ( day, Month[month] ))
        PrintHelp()
    if hour < 0 or hour > 23:
        print('TIME ERROR: The hour (%f) is larger than the number of hours in a day.' % hour)
        PrintHelp()
    if minute < 0 or minute > 59:
        print('TIME ERROR: The minute (%f) is larger than the number of minutes in an hour.' % minute)
        PrintHelp()
    if second < 0 or second > 59:
        print('TIME ERROR: The seconds (%f) is larger than the number of seconds in a minute.' % second)
        PrintHelp()
    
    return DateTime( year, month, day, hour, minute, second )


def ParseArgs( argv ):
    branch = 'Main'
    category = 'Components'
    name = None
    begin = None
    end = now()
    i = 1
    count = len( argv )

    while i < count:
        switch, arg, i = GetArgumentPairs(argv, i, count)
        if not arg:
            continue
        
        if not switch:
            if arg.lower() == 'today' or arg.lower() == 'now':
                begin = now() - RelativeDateTime( hour = 0, minute = 0, second = 0 )
            elif arg.lower() == 'yesterday':
                begin = now() - RelativeDateTime( days = 1, hour = 0, minute = 0, second = 0 )
            elif arg.lower() == 'thisweek':
                # From Sunday at 12:00 AM to now
                begin = now() - RelativeDateTime( days = Sunday - now().day_of_week + 1, hour = 0, minute = 0, second = 0 )
            elif arg.lower() == 'lastweek':
                # From the Sunday before last at 12:00 AM to last Sunday at 12:00 AM
                begin = now() - RelativeDateTime( days = Sunday - now().day_of_week + 8, hour = 0, minute = 0, second = 0 )
                end   = now() - RelativeDateTime( days = Sunday - now().day_of_week + 2, hour = 23, minute = 59, second = 59.00 )
            elif arg.lower() == 'thismonth':
                begin = now() - RelativeDateTime( day = 1, hour = 0, minute = 0, second = 0 )
            elif arg.lower() == 'lastmonth':
                begin = now() - RelativeDateTime( months = 1, day = 1, hour = 0, minute = 0, second = 0 )
                end   = now() - RelativeDateTime( day = 0, hour = 23, minute = 59, second = 59.00 )
            elif arg.lower() == 'thisyear':
                begin = now() - RelativeDateTime( month = 1, day = 1, hour = 0, minute = 0, second = 0 )
            elif arg.lower() == 'lastyear':
                begin = now() - RelativeDateTime( years = 1, month = 1, day = 1, hour = 0, minute = 0, second = 0 )
                end   = now() - RelativeDateTime( month = 1, day = 0, hour = 23, minute = 59, second = 59.00 )
            continue
                    
        if switch.startswith( '?' ):                                # Short for help
            PrintHelp()

        elif switch.lower().startswith( 'n' ):                      # Short for name
            name = arg

        elif switch.lower().startswith( 'c' ):                      # Short for category
            category = arg

        elif switch.lower().startswith( 'b' ):                      # Short for branch
            branch = arg

        elif switch.lower().startswith( 'w' ):                      # Short for weeks
            weeks = int(arg)
            begin = now() - RelativeDateTime( weeks = weeks, hour = 0, minute = 0, second = 0 )
            
        elif switch.lower().startswith( 'd' ):                      # Short for days
            days = int(arg)
            begin = now() - RelativeDateTime( days = days, hour = 0, minute = 0, second = 0 )

        elif switch.lower().startswith( 'h' ):                      # Short for hours
            hours = int(arg)
            if hours < 0 or hours >= 24:
                print('TIME ERROR: The hours (%d) is larger than the number of hours in a day.' % hours)
                PrintHelp()
            begin = now() - RelativeDateTime( hours = hours )
        
        elif switch.lower().startswith( 'm' ):                      # Short for minutes
            minutes = int(arg)
            if minutes < 0 or minutes > 59:
                print('TIME ERROR: The minutes (%d) is larger than the number of minutes in an hour.' % minutes)
                PrintHelp()
            begin = now() - RelativeDateTime( minutes = minutes )
            
        elif switch.lower().startswith( 's' ):                      # Short for start
            value = ParseDateTimeValue( arg )
            if not value:
                continue
            begin = value
                
        elif switch.lower().startswith( 'e' ):                      # Short for end
            value = ParseDateTimeValue( arg )
            if not value:
                continue
            end = value
            if end.hour == 0 and end.minute == 0 and end.second == 0:
                end = end - RelativeDateTime( hour = 0, minute = 0, second = 0 )

    if not name:
        print('ARGUMENT ERROR: The project name was never specified.')
        PrintHelp()
        
    if not begin:
        print('DATE/TIME ERROR: The ending date was never specified using any of the offset switches or end switch.')
        PrintHelp()
        
    if begin > end:
        print('DATE/TIME ERROR: The beginning date (%s) is later than ending date (%s).' % ( begin, end ))
        PrintHelp()
        
    return name, category, branch, begin, end


if __name__ == '__main__':
    name, category, branch, begin, end = ParseArgs( sys.argv )
    project = Project( name, category, branch, begin, end )
    ListChanges( project, sys.stdout, True, False, '' )

import os, string, shutil, sys, datetime
from stat import *

x = [x for x in sys.path if os.path.isfile(os.path.join(x, 'RaptorBinConfig.txt'))]
if len( x ):
    RAPTOR_BIN = x[0] 
    exec(compile(open( os.path.join( RAPTOR_BIN, 'RaptorBinConfig.txt' ), "rb").read(), os.path.join( RAPTOR_BIN, 'RaptorBinConfig.txt' ), 'exec'))
else:
    global P4PORT
    P4PORT = '172.16.79.3:1666'

global MAX_DATE
MAX_DATE = datetime.datetime( datetime.MAXYEAR, 12, 31, 23, 59, 59, 999999 )

def PrintHeader( file ):
    file.write( 'ListChanges.py - Version 1.04\n' )


def PrintHelp():
    print('\nList all of the changes between two labels provided. The list')
    print('of changes will also include all project dependencies.')
    print('\nUsage:')
    print('\tListChanges.py -label <beginLabel> <endLabel or \'now\'>')
    print('\t               -name <Name>')
    print('\t               [-branch branchName = \'Main\']')
    print('\t               [-category categoryName = \'Component\']')
    print('\t               [-out filename.txt]')
    print('\t               [-difference project]')
    print('\t               [ -ignore ]')
    print('\t               [ -verbose ]\n')
    
    print('\tAll switches can be used with just their first initial.\n')
    
    print('\tThe \'-label\' switch specifies the two labels to be compared.')
    print('\tThe labels must be on the same source code project along')
    print('\twith the same branch and category. Alternatively the endLabel')
    print('\tcan be specified with the keyword \'now\' which will report')
    print('\tall changes from the beginning label to the current date/time.\n')
    
    print('\tThe \'-name\' switch is the name of the project to query.\n')
        
    print('\tThe \'-branch\' switch is the branch that the project')
    print('\tbelongs to and defaults to \'Main\'\n')

    print('\tThe \'-category\' switch is the category that the project')
    print('\tbelongs to and defaults to \'Components\'.\n')
    
    print('\tThe \'-difference\' switch allows you to tell the script')
    print('\tto only show the changes which are in the specified project.\n')

    print('\tThe \'-out\' switch specifies where the output should be')
    print('\tdirected to.  If the out switch is not found then the')
    print('\toutput is directed to the screen.\n')
    
    print('\tWith the \'-ignore\' flag set it will ignore all changes by')
    print('\tuser \'orem_cm_build\'. These changes don\'t usually include')
    print('\tany file changes and if they do it is only \'BuildNumber.txt\'.\n')
    
    print('\tThe \'-verbose\' flag will include all the files included in')
    print('\teach change list.\n')
    

def Error( msg ):
    sys.stdout.write( '\nERROR: ' + msg + '\n' )
    

def Check( expression, description ):
    if not expression:
        Error('Check failed: ' + description + '\n\n')
        raise AssertionError
    
    
def FindP4():
    executable = 'P4.exe'
    for path in string.split(os.environ["PATH"], os.pathsep):
        file = os.path.join( path, executable )
        if os.path.exists( file ):
            global P4EXE
            P4EXE = executable
            break

    
class Change:
    "Structure to encapsulate a perforce change."
    def __init__(self):
        self.mNumber = 0
        self.mDate = MAX_DATE
        self.mUser = ''
        self.mDescription = ''
        self.mFiles = []
    
    def __cmp__(self, other):
        return self.mNumber - other.mNumber


class Label:
    "Structure to encapsulate a perforce label description."
    def __init__(self):
        self.mName = 0
        self.mDate = MAX_DATE
        self.mOwner = ''
        self.mDescription = ''

    def __eq__( self, other):
        return self.mName == other.mName and \
               self.mDate == self.mDate and \
               self.mOwner == self.mOwner and \
               self.mDescription == self.mDescription


class Project:
    "Structure to encapsulate a raptor project."
    def __init__(self):
        self.mName = ''
        self.mCategory = ''
        self.mOldBranch = ''
        self.mOldLabel = ''
        self.mOldLabelNum = 0
        self.mNewBranch = ''
        self.mNewLabel = ''
        self.mNewLabelNum = 0
        self.mQueried = False
        
    def Assign( self, other ):
        self.mName = other.mName
        self.mCategory = other.mCategory
        self.mOldBranch = other.mOldBranch
        self.mOldLabel = other.mOldLabel
        self.mOldLabelNum = other.mOldLabelNum
        self.mNewBranch = other.mNewBranch
        self.mNewLabel = other.mNewLabel
        self.mNewLabelNum = other.mNewLabelNum
        self.mQueried = other.mQueried
                
    def CompareToNow(self):
        return self.mNewLabel.lower() == 'now'
    
    def SetLabelNumbers(self):
        if self.mOldLabel != '':
            self.mOldLabelNum = int( self.mOldLabel[ self.mOldLabel.find( '_' ) + 1 : len( self.mOldLabel ) ] )
        if self.mNewLabel != '' and not self.CompareToNow():
            self.mNewLabelNum = int( self.mNewLabel[ self.mNewLabel.find( '_' ) + 1 : len( self.mNewLabel ) ] )
            
    def __eq__( self, other):
        return self.mName.lower() == other.mName.lower() and \
               self.mOldLabel == other.mOldLabel and \
               self.mNewLabel == other.mNewLabel

    def __cmp__(self, other):
        ret = cmp( self.mName.lower(), other.mName.lower() )
        if ret == 0:
            return self.mOldLabelNum - other.mOldLabelNum
        return ret
    
    
def FixCategory( category ):
    if category.endswith( 's' ) == False:
        category = category + 's'
    return category.capitalize()


def ParseChange( lines, change, ignoreCmBuild, verbose ):
    
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
            Check( len( parts ) == 7, 'Expecting a different \'Change\' line.' )
                 
            change.mNumber = int( parts[1] )
            dateParts = parts[5].split( '/' )
            timeParts = parts[6].split( ':' )
            change.mDate = datetime.datetime( int( dateParts[0] ), int( dateParts[1] ), int( dateParts[2] ), int( timeParts[0] ), int( timeParts[1] ), int( timeParts[2] ) )
            change.mUser = parts[3].split( '@' )[0]
            if ignoreCmBuild == True and change.mUser == 'orem_cm_build':
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
    
    
def FindChanges( project, beginLabel, endLabel ):
    command = P4EXE + ' -p ' + P4PORT + ' changes -t -s submitted "//SEABU/ProductSource/'
    command += project.mCategory + '/' + project.mName + '/' + project.mOldBranch
    command += '/"...@' + beginLabel.mDate.strftime( '%Y/%m/%d:%H:%M:%S' )
    command += ',@' + endLabel.mDate.strftime( '%Y/%m/%d:%H:%M:%S' )
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

        tmpChange = ParseChange( lines, changes[i], gIgnoreCmBuild, gVerbose )
        if tmpChange.mNumber != 0 and tmpChange.mDate != MAX_DATE and tmpChange.mUser != '':
            changes[i] = tmpChange
            i = i + 1
        else:
            changes.remove( changes[i] )
            
    return changes


def GetNameAndBranch( line, project, label, oldBranch ):
    parts = line.split()
    index = 0
    if line.startswith( 'Build of ' ):
        index = 2
    elif line.startswith( 'Internal release of ' ):
        index = 3
    else:
        return
    
    if project.mName.lower() == parts[index].lower() and project.mName != parts[index]:
        project.mName = parts[index]
    
    if oldBranch == True:
        project.mOldBranch = parts[index + 1]
    else:
        project.mNewBranch = parts[index + 1]
                
                        
def ParseLabel( lines, project, oldBranch ):
    label = Label()
    inDescription = False
    
    for line in lines:
        line = line.strip()
        line = line.strip( '\n' )
        
        if inDescription:
            if len( line ) > 0:
                # The label returns the correct case for the name and branch
                GetNameAndBranch( line, project, label, oldBranch )
                        
                # Grab the description formatting it correctly
                if len( label.mDescription ) > 0:
                    label.mDescription += '\n'
                label.mDescription += line
                
            else:
                inDescription = False
            
        elif line.startswith( 'Label:' ):
            label.mName = line.split()[1]
            
        elif line.startswith( 'Owner:' ):
            label.mOwner = line.split()[1]

        elif line.startswith( 'Update:' ):
            parts = line.split()
            pieces = parts[1].split( '/' ) + parts[2].split( ':' )
            label.mDate = datetime.datetime( int( pieces[0] ), int( pieces[1] ), int( pieces[2] ), int( pieces[3] ), int( pieces[4] ), int( pieces[5] ) )
            
        elif line.startswith( 'Description:' ):
            inDescription = True
                        
    return label


def IsLabelCorrect( labelStr, name, branch ):
    command = P4EXE + ' -p ' + P4PORT + ' label -o ' + labelStr
    lines = os.popen4( command, 't' )[1].readlines()

    for line in lines:
        line = line.strip().strip( '\n' )
        index = 0
        if line.startswith( 'Build of ' ):
            index = 2
        elif line.startswith( 'Internal release of ' ):
            index = 3
        else:
            continue
        
        parts = line.split()

        if name.lower() == parts[index].lower():
            if name != parts[index]:
                name = parts[index]
        else:
            print('ERROR: The label, ' + labelStr + ', does not belong to project ' + name + '.')
            return False, name, branch

        
        if branch == '' or branch.lower() == parts[index + 1].lower():
            if branch == '' or name != parts[index + 1]:
                branch = parts[index + 1]
            return True, name, branch
        else:
            print('ERROR: The label, ' + labelStr + ', does not belong to branch ' + branch + '.')            
            return False, name, branch
        
    print('ERROR: The label, ' + labelStr + ', does not belong to branch ' + branch + '.')
    return False, name, branch

    
def GetLabels( project ):
    command = P4EXE + ' -p ' + P4PORT + ' label -o ' + project.mOldLabel
    lines = os.popen4( command, 't' )[1].readlines()
    oldLabel = ParseLabel( lines, project, True )

    if project.CompareToNow():
        newLabel = Label()
        newLabel.mDate = datetime.datetime.now()
        newLabel.mName = 'Now'
        newLabel.mOwner = 'None'
        newLabel.mDescription = 'Comparing against the \'#head\' or latest revision'
    else:
        command = P4EXE + ' -p ' + P4PORT + ' label -o ' + project.mNewLabel
        lines = os.popen4( command, 't' )[1].readlines()
        newLabel = ParseLabel( lines, project, False )

    return oldLabel, newLabel
    
    
def ListLabelChanges( project, file ):
    beginLabel, endLabel = GetLabels( project )
        
    Check( beginLabel.mDate != MAX_DATE, 'The old label, ' + project.mOldLabel + ', did not return a valid date.' )
    Check( endLabel.mDate != MAX_DATE, 'The new label, ' + project.mNewLabel + ', did not return a valid date.' )
    
    Check( project.mOldBranch.lower() == project.mNewBranch.lower(), 'Both old branch and new branch should be identical' )
    
    file.write( '\n' + '-' * 79 )
    file.write( '\nListing changes between ' + project.mOldLabel + ' and ' + project.mNewLabel + ' for:\n' )
    file.write( 'Category: ' + project.mCategory + '\n' )
    file.write( 'Name    : ' + project.mName + '\n' )
    file.write( 'Branch  : ' + project.mOldBranch + '\n\n' ) # Doesn't matter which branch because they are garunteed to be the same

    file.write( 'Begin Label: ' + beginLabel.mName + '\n' )
    file.write( 'Date       : ' + beginLabel.mDate.strftime( '%Y/%m/%d %H:%M:%S' ) + '\n' )
    file.write( 'Owner      : ' + beginLabel.mOwner + '\n' )
    file.write( 'Description: ' + beginLabel.mDescription.replace( '\n', '\n             ' ) + '\n\n' )
    file.write( 'End Label  : ' + endLabel.mName + '\n' )
    file.write( 'Date       : ' + endLabel.mDate.strftime( '%Y/%m/%d %H:%M:%S' ) + '\n' )
    file.write( 'Owner      : ' + endLabel.mOwner + '\n' )
    file.write( 'Description: ' + endLabel.mDescription.replace( '\n', '\n             ' ) + '\n\n' )

    changes = FindChanges( project, beginLabel, endLabel )
    
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
    

def LocalWrite( file, str ):
    
    if( file != sys.stdout ):
        sys.stdout.write( str )
        
    file.write( str )


def PrintProjects( projects, file ):
    
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
    cols[1] = Column( "Item" )
    cols[2] = Column( "Old Branch" )
    cols[3] = Column( "Old Label" )
    cols[4] = Column( "New Branch" )
    cols[5] = Column( "New Label" )
    for project in projects:
        cols[1].SetWidth( len( project.mName ) + 1 )
        cols[2].SetWidth( len( project.mOldBranch ) )
        cols[3].SetWidth( len( project.mOldLabel ) )
        cols[4].SetWidth( len( project.mNewBranch ) )
        cols[5].SetWidth( len( project.mNewLabel ) )
        
    totalWidth = cols[1].GetWidth() + cols[2].GetWidth() + cols[3].GetWidth()
    totalWidth += cols[4].GetWidth() + cols[5].GetWidth() - Column.gap - 4
    
    LocalWrite( file, '\n' + totalWidth * '=' + '\n' )
    LocalWrite( file, 'Differing Components List\n' )
    LocalWrite( file, totalWidth * '=' + '\n' )
    for i in range(1,6):
        LocalWrite( file, ('%-' + str(cols[i].GetWidth() - 1) + 's') % cols[i].GetName() )
    LocalWrite( file, '\n' )
    
    hasDifferentBranches = False
    LocalWrite( file, totalWidth * '-' + '\n' )
    for project in projects:
        if project.mOldBranch != project.mNewBranch:
            LocalWrite( file, ('%-' + str(cols[1].GetWidth()-1) + 's') % ('*' + project.mName) )
            hasDifferentBranches = True
        else:
            LocalWrite( file, ('%-' + str(cols[1].GetWidth()-1) + 's') % project.mName )
        LocalWrite( file, ('%-' + str(cols[2].GetWidth()-1) + 's') % project.mOldBranch )
        LocalWrite( file, ('%-' + str(cols[3].GetWidth()-1) + 's') % project.mOldLabel )
        LocalWrite( file, ('%-' + str(cols[4].GetWidth()-1) + 's') % project.mNewBranch )
        LocalWrite( file, ('%-' + str(cols[5].GetWidth()-1) + 's') % project.mNewLabel + '\n')
    
    LocalWrite( file, '=' * totalWidth + "\n" )
    if hasDifferentBranches:
        LocalWrite( file, '* = WARNING: The old branch doesn\'t equal the new branch. Cannot\n' )
        LocalWrite( file, '    compare components where the old and new branches are different.\n\n' )
    
    
def MakeUnique( projects ):
    
    projects = RemoveAddedOrRemovedComponents( projects )
    
    projects.sort()
    count = len( projects )
    i = 0
    
    while i < count:
        
        if i + 1 >= count:
            i = i + 1
            continue
            
        if projects[i].mName.lower() == projects[i + 1].mName.lower() and \
           projects[i].mCategory.lower() == projects[i + 1].mCategory.lower():
            
            # Always grab the newest old label and newest new label -- matches how Raptor resolves identical projects
            if projects[i].mOldLabelNum < projects[i + 1].mOldLabelNum:
                projects[i].mOldBranch = projects[i + 1].mOldBranch
                projects[i].mOldLabel = projects[i + 1].mOldLabel
                projects[i].SetLabelNumbers()
                projects[i].mQueried = False
                
            if not projects[i].CompareToNow() and not projects[i + 1].CompareToNow() and \
               projects[i].mNewLabelNum < projects[i + 1].mNewLabelNum:
                projects[i].mNewBranch = projects[i + 1].mNewBranch
                projects[i].mNewLabel = projects[i + 1].mNewLabel
                projects[i].SetLabelNumbers()
                projects[i].mQueried = False
                        
            projects.remove( projects[i + 1] )
                                
        if len( projects ) != count:
            count = len( projects )
        else:
            i = i + 1
    
    return projects


def RemoveAddedOrRemovedComponents( projects ):
    count = len( projects )
    i = 0
    
    while i < count:
        ## Remove projects that don't have two labels
        if projects[i].mOldLabel == '' or projects[i].mNewLabel == '':
            projects.remove( projects[i] )
            
        if len( projects ) != count:
            count = len( projects )
        else:
            i = i + 1            

    return projects


def FindComponentsTxtDependencies( project ):
    command = P4EXE + ' -p ' + P4PORT + ' print -q "//SEABU/ProductSource/' + project.mCategory + '/' + project.mName + '/' + project.mOldBranch
    command += '/Components.txt@' + project.mOldLabel + '"'
    lines = os.popen4( command, 't' )[1].readlines()

    projects = []
    project.mQueried = True
    
    for line in lines:
        line = line.strip()
        line = line.strip( '\n' )
        line = line.replace( '=', '', 1 )
    
        parts = line.split()
        if len( parts ) != 5 or parts[0].lower() != 'dep':
            continue

        name = parts[2].strip(';');
        
        proj = Project()
        proj.mCategory = FixCategory( parts[1].strip(';') )
        proj.mName = name.capitalize()
        proj.mOldBranch = parts[3].strip(';').capitalize()
        proj.mOldLabel = parts[4].split( '-' )[0]
        projects.append( proj )

    # Now list the new components.txt and line them up with their previous projects
    command = P4EXE + ' -p ' + P4PORT + ' print -q "//SEABU/ProductSource/' + project.mCategory + '/' + project.mName + '/' + project.mNewBranch
    if project.CompareToNow():
        command += '/Components.txt#head"'
    else:
        command += '/Components.txt@' + project.mNewLabel + '"'
    lines = os.popen4( command, 't' )[1].readlines()
    
    for line in lines:
        line = line.strip()
        line = line.strip( '\n' )
        line = line.replace( '=', '', 1 )
    
        parts = line.split()
        if len( parts ) != 5 or parts[0].lower() != 'dep':
            continue

        name = parts[2].strip(';');
        count = len( projects )
        j = 0
        found = False

        # This will allow for duplicates but we remove them below            
        while j < count:
            if projects[j].mName.lower() == name.lower() and projects[j].mNewLabel == '':
                projects[j].mNewLabel = parts[4].split( '-' )[0]
                projects[j].mNewBranch = parts[3].strip(';').capitalize()
                projects[j].SetLabelNumbers()
                found = True
            j = j + 1
            
    # Update the project's to reflect the proper case of the project name and branch
    for proj in projects:
        GetLabels( proj )
        
    return projects


def RemoveIdenticalLabels( projects ):
    i = 0
    while i < len( projects ):
        ## Remove projects where the labels were the same
        if projects[i].mOldLabel.lower() == projects[i].mNewLabel.lower():
            projects.remove( projects[i] )
        else:
            i = i + 1
            
    return projects


def RemoveDifferingBranches( projects, file ):
    i = 0
    
    while i < len( projects ):
        if projects[i].mOldBranch != projects[i].mNewBranch and projects[i].mNewBranch != '':
            # If the current project has two different branches then remove them
            projects.remove( projects[i] )
        else:
            i = i + 1

    Check( len( projects ) != 0, 'The only project specified has a different old branch from new branch.' )
        
    return projects
   

def FindAllProjects( project ):
    global gQueriedProjects
    gQueriedProjects = []
    projects = []
    projects.append( project )
    
    i = 0
    count = len( projects )
    
    while i < count:
        
        if( projects[i].mQueried == False ):
            
            found = False
            for proj in gQueriedProjects:
                if proj == projects[i]:
                    found = True
            
            if found == False:
                proj = Project()
                proj.Assign( projects[i] )
                gQueriedProjects.append( proj )
                print('Querying ' + projects[i].mName) # debug_info + ', old label: ' + projects[i].mOldLabel + ', new label: ' + projects[i].mNewLabel + '.'
                projects = projects + FindComponentsTxtDependencies( projects[i] )
                if len( projects ) != count:
                    projects = MakeUnique( projects )        
                    count = len( projects )
                    i = 0
                    continue
            else:
                projects[i].mQueried == True
            
        i = i + 1
    
    gQueriedProjects = []
    return projects


def ParseArgs( argv ):
    filename = ''
    beginStr = ''
    endStr = ''
    name = ''
    branch = 'Main'
    category = 'Components'
    difference = ''
    count = len( argv )
    labels = False
    foundRequiredSwitch = False
    i = 1
    global gVerbose, gIgnoreCmBuild
    gVerbose = False
    gIgnoreCmBuild = False

    while i < count:
        if argv[i].lower().startswith( '-?' ) or argv[i].lower().startswith( '/?' ) or \
           argv[i].lower().startswith( '-h' ) or argv[i].lower().startswith( '/h' ):
            PrintHelp()
            sys.exit( 0 )        

        elif argv[i].lower().startswith( '-o' ) and i + 1 < count:
            filename = argv[i + 1]
            i = i + 2
            
        elif( argv[i].lower().startswith( '/l' ) or argv[i].lower().startswith( '-l' ) ) and i + 2 < count:
            foundRequiredSwitch = True
            beginStr = argv[ i + 1 ]
            endStr = argv[ i + 2 ]
            if( beginStr.lower() == 'now' and endStr.lower() == 'now' ):
                Check( False, 'No differences will be found if both labels are \'now\'.' )
            if beginStr.lower() == 'now':
                temp = endStr
                endStr = beginStr
                beginStr = temp
            elif beginStr.find( '_' ) != -1 and endStr.find( '_' ) != -1:
                beginInt = int( beginStr[ beginStr.find('_') + 1 : len(beginStr) ] )
                endInt = int( endStr[ endStr.find('_') + 1 : len(endStr) ] )
                if beginInt > endInt:
                    temp = endStr
                    endStr = beginStr
                    beginStr = temp
            i = i + 3
        
        #-name Sme -branch Main -category Components
        elif( argv[i].lower().startswith( '/n' ) or argv[i].lower().startswith( '-n' ) ) and i + 1 < count:
            name = argv[i + 1]
            i = i + 2
            
        elif( argv[i].lower().startswith( '/b' ) or argv[i].lower().startswith( '-b' ) ) and i + 1 < count:
            branch = argv[i + 1]
            i = i + 2

        elif( argv[i].lower().startswith( '/c' ) or argv[i].lower().startswith( '-c' ) ) and i + 1 < count:
            category = argv[i + 1]
            i = i + 2
        
        elif( argv[i].lower().startswith( '/d' ) or argv[i].lower().startswith( '-d' ) ) and i + 1 < count:
            difference = argv[i + 1]
            i = i + 2
            
        elif argv[i].lower().startswith( '/i' ) or argv[i].lower().startswith( '-i' ):
            gIgnoreCmBuild = True
            i = i + 1

        elif argv[i].lower().startswith( '/v' ) or argv[i].lower().startswith( '-v' ):
            gVerbose = True
            i = i + 1
            
        else:
            i = i + 1
        
    if foundRequiredSwitch == False or name == '':
        print('ERROR: Invalid command line. Are you specifying labels and the name?')
        PrintHelp()
        sys.exit( 1 )        

    return filename, beginStr, endStr, name, branch, category, difference


if __name__ == '__main__':

    PrintHeader( sys.stdout )
    
    proj = Project()
    filename, proj.mOldLabel, proj.mNewLabel, name, branch, category, difference = ParseArgs( sys.argv )
    
    FindP4()
    
    if filename == '':
        file = sys.stdout
    else:
        file = open( filename, 'w' )
        PrintHeader( file )

    beginTime = datetime.datetime.now()
    print('Started                 :  ' + beginTime.strftime( '%I:%M:%S %p' ))

    proj.mName = name.capitalize()
    proj.mOldBranch = branch.capitalize()
    proj.mCategory = FixCategory( category )
    
    result1, proj.mName, proj.mOldBranch = IsLabelCorrect( proj.mOldLabel, proj.mName, proj.mOldBranch )
    if proj.CompareToNow():
        result2 = True
        proj.mNewBranch = proj.mOldBranch
    else:
        result2, proj.mName, proj.mNewBranch = IsLabelCorrect( proj.mNewLabel, proj.mName, proj.mNewBranch )
        
    if result1 and result2:
        proj.SetLabelNumbers()
            
        projects = FindAllProjects( proj )
        PrintProjects( projects, file )
        projects = RemoveDifferingBranches( projects, file )
        projects = RemoveIdenticalLabels( projects )
    
        for project in projects:
            # If the user is only asking for one project changes output only that one
            if difference != '' and project.mName.lower() != difference.lower():
                continue
            if file != sys.stdout:
                sys.stdout.write( 'Dumping changes for ' + project.mName + '\n' )
            ListLabelChanges( project, file )
        
    if filename != '':
        file.close()
    
    endTime = datetime.datetime.now()
    print('Finished                :  ' + endTime.strftime( '%I:%M:%S %p' ))
    elapsed = endTime - beginTime
    hours = int( elapsed.seconds / 3600 )
    minutes = int( ( elapsed.seconds % 3600 ) / 60 )
    seconds = int( ( elapsed.seconds % 3600 ) % 60 )
    print('Total time for operation:  %02d:%02d:%02d:%03d' % ( hours, minutes, seconds, elapsed.microseconds / 1000 ))

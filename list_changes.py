import os, string, shutil, sys, datetime
from stat import *

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
    P4PORT = r'155.64.92.15:1666'


def PrintHeader( file ):
    file.write( 'List Changes Between Labels - version 1.06\n' )


def PrintHelp():
    print('\nList all of the changes between two labels provided. The list')
    print('of changes will also include all project dependencies.')
    print('\nUsage:')
    print('\tListChanges.py -label <beginLabel> <endLabel or \'now\'>')
    print('\t               -name <Name>')
    print('\t               [-branch branchName = \'Main\']')
    print('\t               [-category categoryName = \'Component\']')
    print('\t               [-out filename.txt]')
    print('\t               [-filter project]')
    print('\t               [-user Perforce Username]')
    print('\t               [-ignore]')
    print('\t               [-verbose]\n')
    
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
    
    print('\tThe \'-filter\' switch allows you to tell the script')
    print('\tto only show the changes which are in the specified project.\n')

    print('\tThe \'-user\' switch allows you to tell the script')
    print('\tto only show the changes which were made by the specified user.\n')

    print('\tThe \'-out\' switch specifies where the output should be')
    print('\tdirected to.  If the out switch is not found then the')
    print('\toutput is directed to the screen.\n')
    
    print('\tWith the \'-ignore\' flag set it will ignore all changes by')
    print('\tuser \'orem_cm_build\'. These changes don\'t usually include')
    print('\tany file changes and if they do it is only \'BuildNumber.txt\'.\n')
    
    print('\tThe \'-verbose\' flag will include all the files included in')
    print('\teach change list.\n')
    
    print('\tEXAMPLES:')
    print('\tMost common usage syntax:')
    print('\t<script>.py -n Sme -l BuildNumber_13832 BuildNumber_13974 -i\n')
    print('\tFind differences in current project between the latest build and NOW:')
    print('\t<script>.py -n Sme -l BuildNumber_13974 now -i\n')
    print('\tFind all of YOUR changes in a sub component of the build number:')
    print('\t<script>.py -n Sme -l BuildNumber_13974 BuildNumber_13974 -f base -u john_smith\n')
    print('\tQuickly find all changes in JUST main component:')
    print('\t<script>.py -n Sme -l BuildNumber_13974 BuildNumber_13974 -f sme\n')


def Error( msg ):
    sys.stdout.write('\nERROR: %s\n' % msg)
    

def Check( expression, description ):
    if not expression:
        Error('Check failed: %s\n\n' % description)
        raise AssertionError
    
    
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


class Label:
    "Structure to encapsulate a perforce label description."
    def __init__(self):
        self.mName = 0
        self.mDate = datetime.datetime.max
        self.mOwner = ''
        self.mDescription = ''

    def UpdateCreationDate(self, component):
        command = '%s -p %s fstat "%s/BuildNumber.txt@%s"' % (P4EXE, P4PORT, component, self.mName)
        lines = os.popen4( command, 't' )[1].readlines()
        for line in lines:
            trimmedLine = line.lstrip(' .')
            index = trimmedLine.find(' ')
            if index != -1:
                name = trimmedLine[:index]
                value = trimmedLine[index + 1:]
                if name.lower() == 'headtime':
                    self.mDate = datetime.datetime.fromtimestamp(int(value))
                    break

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

    def GetRepositoryPath(self, old):
        path = '//SEABU/ProductSource/%s/%s/' % (self.mCategory, self.mName)
        if old:
            return path + self.mOldBranch
        else:
            return path + self.mNewBranch

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
    if category.lower().startswith('cached'): # cached component
        category = category[ len('cached'): ]
    if not category.endswith( 's' ):
        category = category + 's'
    return category.capitalize()


def FixName( name ):
    # always get to sandbox (cache)
    if name.lower().startswith('export'): 
        name = name[ len('export'): ]
    # never get unless main component -- fix_jasoni not currently supported in this logic
    if name.lower().startswith('local') and name.lower() != 'local':  
        name = name[ len('local'): ]
    return name.capitalize()


def FixBranch( branch ):
    # force using this branch
    if branch.lower().startswith('forced'): 
        branch = branch[ len('forced'): ]
    return branch.capitalize()


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
            
        elif not insideChange and line.startswith( 'Change ' ):
            insideChange = True
            parts = line.split()
            Check( len( parts ) == 7, 'Expecting a different \'Change\' line.' )
                 
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
    
    
def FindChanges( project, beginLabel, endLabel ):
    command = '%s -p %s changes -t -s submitted "%s/"...@%s,@%s' % (P4EXE, P4PORT, project.GetRepositoryPath(True), \
               beginLabel.mDate.strftime( '%Y/%m/%d:%H:%M:%S' ), endLabel.mDate.strftime( '%Y/%m/%d:%H:%M:%S' ))
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
        command = '%s -p %s describe -s "%d"' % (P4EXE, P4PORT, changes[i].mNumber)
        lines = os.popen4( command, 't' )[1].readlines()

        tmpChange = ParseChange( lines, changes[i], gIgnoreCmBuild, gVerbose, gUser )
        if tmpChange.mNumber != 0 and tmpChange.mDate != datetime.datetime.max and tmpChange.mUser != '':
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

    label.UpdateCreationDate(project.GetRepositoryPath(oldBranch))
    return label


def IsLabelCorrect( labelStr, name, branch ):
    command = '%s -p %s label -o %s' % (P4EXE, P4PORT, labelStr)
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
            print('ERROR: The label, %s, does not belong to project %s.' % (labelStr, name))
            return False, name, branch

        
        if branch == '' or branch.lower() == parts[index + 1].lower():
            if branch == '' or name != parts[index + 1]:
                branch = parts[index + 1]
            return True, name, branch
        else:
            print('ERROR: The label, %s, does not belong to branch %s.' % (labelStr, branch))
            return False, name, branch
        
    print('ERROR: The label, %s, does not belong to branch %s.' % (labelStr, branch))
    return False, name, branch

    
def GetLabels( project ):
    command = '%s -p %s label -o %s' % (P4EXE, P4PORT, project.mOldLabel)
    lines = os.popen4( command, 't' )[1].readlines()
    oldLabel = ParseLabel( lines, project, True )

    if project.CompareToNow():
        newLabel = Label()
        newLabel.mDate = datetime.datetime.now()
        newLabel.mName = 'Now'
        newLabel.mOwner = 'None'
        newLabel.mDescription = 'Comparing against the \'#head\' or latest revision'
    else:
        command = '%s -p %s label -o %s' % (P4EXE, P4PORT, project.mNewLabel)
        lines = os.popen4( command, 't' )[1].readlines()
        newLabel = ParseLabel( lines, project, False )

    return oldLabel, newLabel
    
    
def ListLabelChanges( project, file ):
    beginLabel, endLabel = GetLabels( project )
        
    Check( beginLabel.mDate != datetime.datetime.max, 'The old label, %s , did not return a valid date.' % project.mOldLabel )
    Check( endLabel.mDate != datetime.datetime.max, 'The new label, %s, did not return a valid date.' % project.mNewLabel )
    
    Check( project.mOldBranch.lower() == project.mNewBranch.lower(), 'Both old branch and new branch should be identical' )
    
    file.write( '\n' + '-' * 79 )
    file.write( '\nListing changes between %s and %s for:\n' % (project.mOldLabel, project.mNewLabel) )
    file.write( 'Category: %s\n' % project.mCategory )
    file.write( 'Name    : %s\n' % project.mName )
    file.write( 'Branch  : %s\n\n' % project.mOldBranch ) # Doesn't matter which branch because they are garunteed to be the same

    file.write( 'Begin Label: %s\n' % beginLabel.mName )
    file.write( 'Date       : %s\n' % beginLabel.mDate.strftime( '%Y/%m/%d %H:%M:%S' ) )
    file.write( 'Owner      : %s\n' % beginLabel.mOwner )
    file.write( 'Description: %s\n\n' % beginLabel.mDescription.replace( '\n', '\n             ' ) )
    file.write( 'End Label  : %s\n' % endLabel.mName )
    file.write( 'Date       : %s\n' % endLabel.mDate.strftime( '%Y/%m/%d %H:%M:%S' )  )
    file.write( 'Owner      : %s\n' % endLabel.mOwner )
    file.write( 'Description: %s\n\n' % endLabel.mDescription.replace( '\n', '\n             ' ) )

    changes = FindChanges( project, beginLabel, endLabel )
    
    for change in changes:
        file.write( 'Change %d on %s by %s.\n' % (change.mNumber, change.mDate.strftime( '%Y/%m/%d %H:%M:%S' ), change.mUser) )
        if len( change.mDescription ) > 0:
            file.write( '\n\t%s\n\n' % change.mDescription.replace('\n', '\n\t') )
        else:
            file.write( '\n\tNo description of change.\n\n' )
        
        if len( change.mFiles ) > 0:
            file.write( 'Affected files ...\n\n' )
            
            for fileDesc in change.mFiles:
                file.write( '%s\n' % fileDesc )
                
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
    command = '%s -p %s print -q "%s/Components.txt@%s"' % (P4EXE, P4PORT, project.GetRepositoryPath(True), project.mOldLabel)
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

        proj = Project()
        proj.mCategory = FixCategory( parts[1].strip(';') )
        proj.mName = FixName( parts[2].strip(';') )
        proj.mOldBranch = FixBranch( parts[3].strip(';') )
        proj.mOldLabel = parts[4].split( '-' )[0]
        projects.append( proj )

    # Now list the new components.txt and line them up with their previous projects
    command = '%s -p %s print -q "%s/Components.txt' % (P4EXE, P4PORT, project.GetRepositoryPath(False))
    if project.CompareToNow():
        command += '#head"'
    else:
        command += '@%s"' % project.mNewLabel
    lines = os.popen4( command, 't' )[1].readlines()
    
    for line in lines:
        line = line.strip()
        line = line.strip( '\n' )
        line = line.replace( '=', '', 1 )
    
        parts = line.split()
        if len( parts ) != 5 or parts[0].lower() != 'dep':
            continue

        name = FixName( parts[2].strip(';') )
        count = len( projects )
        j = 0
        found = False

        # This will allow for duplicates but we remove them below            
        while j < count:
            if projects[j].mName.lower() == name.lower() and projects[j].mNewLabel == '':
                projects[j].mNewLabel = parts[4].split( '-' )[0]
                projects[j].mNewBranch = FixBranch( parts[3].strip(';') )
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
        
        if not projects[i].mQueried:
            found = False
            for proj in gQueriedProjects:
                if proj == projects[i]:
                    found = True
            
            if not found:
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
    filter = ''
    count = len( argv )
    foundLabels = False
    i = 1
    global gVerbose, gIgnoreCmBuild, gUser
    gVerbose = False
    gIgnoreCmBuild = False
    gUser = ''

    while i < count:
        if argv[i].lower().startswith( '-?' ) or argv[i].lower().startswith( '/?' ) or \
           argv[i].lower().startswith( '-h' ) or argv[i].lower().startswith( '/h' ):
            PrintHelp()
            sys.exit( 0 )        

        elif argv[i].lower().startswith( '-o' ) and i + 1 < count:
            filename = argv[i + 1]
            i = i + 2
            
        elif( argv[i].lower().startswith( '/l' ) or argv[i].lower().startswith( '-l' ) ) and i + 2 < count:
            foundLabels = True
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
        
        elif( argv[i].lower().startswith( '/f' ) or argv[i].lower().startswith( '-f' ) ) and i + 1 < count:
            filter = argv[i + 1]
            i = i + 2
            
        elif( argv[i].lower().startswith( '/u' ) or argv[i].lower().startswith( '-u' ) ) and i + 1 < count:
            gUser = argv[i + 1]
            i = i + 2

        elif argv[i].lower().startswith( '/i' ) or argv[i].lower().startswith( '-i' ):
            gIgnoreCmBuild = True
            i = i + 1

        elif argv[i].lower().startswith( '/v' ) or argv[i].lower().startswith( '-v' ):
            gVerbose = True
            i = i + 1
            
        else:
            i = i + 1
        
    if not foundLabels or name == '':
        print('ERROR: Invalid command line. Are you specifying labels and the name?')
        PrintHelp()
        sys.exit( 1 )        

    return filename, beginStr, endStr, name, branch, category, filter


if __name__ == '__main__':

    PrintHeader( sys.stdout )

    # Ensure that we can actually make the calls to the Perforce repository
    Check( 'P4EXE' in vars() and P4EXE != '', 'Cannot find the p4.exe binary in the path or on the network.' )
    Check( 'P4PORT' in vars() and P4PORT != '', 'The port number was not set correctly for perforce.' )
    
    proj = Project()
    filename, proj.mOldLabel, proj.mNewLabel, name, branch, category, filter = ParseArgs( sys.argv )
        
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
        projects = []
        
        if filter != '' and proj.mName.lower() == filter.lower():
            projects.append( proj )
        else:
            projects = FindAllProjects( proj )
            PrintProjects( projects, file )
            projects = RemoveDifferingBranches( projects, file )
            projects = RemoveIdenticalLabels( projects )
    
        for project in projects:
            # If the user is only asking for one project changes output only that one
            if filter != '' and project.mName.lower() != filter.lower():
                continue
            if file != sys.stdout:
                sys.stdout.write( 'Dumping changes for %s\n' % project.mName )
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

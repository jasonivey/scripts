import os, sys, win32net, re, time, mx.DateTime
from xml.dom.minidom import Document
from xml.dom.minidom import parse

class File:
    "Structure to encapsulate a network file."
    def __init__(self, name, date):
        self.mName = name
        self.mDate = date

    def __str__(self):
        return '%s,%s' % (self.mName, self.mDate) 
        
    def __eq__(self, other):
        return self.mName.lower() == other.mName.lower()
    
    def __cmp__(self, other):
        if self.mDate == other.mDate:
            return cmp(self.mName.lower(), other.mName.lower())
        else:
            return cmp(self.mDate, other.mDate)

    
class Session:
    "Structure to encapsulate a network share session."
    def __init__(self, user, host):
        self.mUser = user
        self.mHost = host
        self.mFiles = []

    def add_file(self, name, date):
        MAX_FILES = 30
        
        file = File( name, date )
        
        if file in self.mFiles:
            index = self.mFiles.index(file)
            self.mFiles[index].mDate = date
        else:
            if len( self.mFiles ) + 1 == MAX_FILES:
                self.mFiles.pop()
                print('Maximum files hit for %s\\%s' % ( self.mHost, self.mUser ))
                
            before = len( self.mFiles )
            self.mFiles.insert(0, file)
            after = len( self.mFiles )
            assert( before < after )

    def add_files(self, files, date):
        for file in files:
            self.add_file(file, date)

    def __str__(self):
        prefix = '%s,%s' % (self.mUser, self.mHost)
        str = ''
        for file in self.mFiles:
            str += '%s,%s\n' % (prefix, file)
        if not str:
            str = '%s,,\n' % prefix
        return str
    
    def __eq__(self, other):
        return self.mUser.lower() == other.mUser.lower() and \
               self.mHost.lower() == other.mHost.lower()
            
    def __cmp__(self, other):
        if self.mUser.lower() == other.mUser.lower():
            return cmp( self.mHost.lower(), other.mHost.lower() )
        else:
            return cmp( self.mUser.lower(), other.mUser.lower() )
    
    def sort(self):
        self.mFiles.sort()


def SortSessions(sessions):
    sessions.sort()
    for session in sessions:
        session.sort()
    return sessions


def ImportLog( filename ):
    sessions = []
    if not os.path.exists( filename ):
        return sessions
    
    doc = parse( filename )
    for sessionDoc in doc.getElementsByTagName("Session"):
        user = sessionDoc.attributes['User'].value
        host = sessionDoc.attributes['Host'].value
        session = Session( user, host )
        
        if session in sessions:
            index = sessions.index(session)
        else:
            index = len( sessions )
            sessions.append( session )
            
        for fileDoc in sessionDoc.getElementsByTagName("File"):
            if fileDoc.hasAttributes():
                date = str( fileDoc.attributes['Date'].value )
                name = fileDoc.firstChild.data.strip()
                sessions[index].add_file( name, mx.DateTime.DateTimeFrom(date) )

    doc.unlink()

    return SortSessions(sessions)
    
    
def ExportLog( filename, sessions ):
    doc = Document()
    docSessions = doc.createElement( "NetworkSessions" )
    for session in sessions:
        docSession = doc.createElement("Session")
        docSession.setAttribute( "User", session.mUser )
        docSession.setAttribute( "Host", session.mHost )
        
        docFiles = doc.createElement("Files")
        for file in session.mFiles:
            docFile = doc.createElement("File")
            docFile.setAttribute( "Date", str(file.mDate) )
            docFileName = doc.createTextNode( file.mName )
            docFile.appendChild( docFileName )
            docSession.appendChild( docFile )
            
        docSessions.appendChild( docSession )

    doc.appendChild( docSessions )
        
    file = open( filename, 'w' )
    file.write( doc.toprettyxml() )
    doc.unlink()
    file.close()


def UpdateSessions( host, sessions ):
    for iter in win32net.NetSessionEnum( 10, host, None, None ):
        session = Session( iter['user_name'], iter['client_name'] )
        
        files = []
        for file in win32net.NetFileEnum( 3, host, None, session.mUser ):
            files.append( file['path_name'] )
            
        if session in sessions:
            index = sessions.index(session)
        else:
            index = len( sessions )
            sessions.append( session )
            
        sessions[index].add_files( files, mx.DateTime.now() )
        
    return SortSessions(sessions)


if __name__ == '__main__':
    
    if len( sys.argv ) != 3:
        print('netshare.py <hostname> <logfile>')
        sys.exit(2)
        
    host = '\\\\%s' % sys.argv[1]
    logfile = os.path.abspath( sys.argv[2] )

    while( True ):
        sessions = ImportLog( logfile )
        UpdateSessions( host, sessions )
        ExportLog( logfile, sessions )
    
        for session in sessions:
            print(session.mHost + '\\' + session.mUser)
            for file in session.mFiles:
                print('\t%s - %s' % ( file.mDate, file.mName ))
            print('')
            
        print('Waiting for 1 minute to check again.')
        time.sleep(60)

    sys.exit(0)
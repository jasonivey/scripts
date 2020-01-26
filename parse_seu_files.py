import os, string, shutil, sys, re

pattern = '(?P<platform>[^\t]*?)\t(?P<company>[^\t]*?)\t(?P<program>[^\t]*?)\t(?P<version>[^\t]*?)\t(?P<reginfo>[^\t]*)(?:\t(?P<url>.*))?'
regex = re.compile( pattern )

class RegInfo:
    "Structure to encapsulate a Version."
    def __init__(self, info):
        self.Info = info

    def __str__(self):
        return 'RegInfo : %s\n' % self.Info.replace('<br>', ' ').replace('\n', '')

    def __cmp__(self, other):
        return cmp( self.Info, other.Info )

    
class Version:
    "Structure to encapsulate a Version."
    def __init__(self, name, reginfo):
        self.Name = name
        self.RegInfos = []
        self.Add( reginfo )
        
    def Add( self, reginfo ):
        global gDuplicates
        found = False
        for r in self.RegInfos:
            if r.Info.lower() == reginfo.lower():
                gDuplicates = gDuplicates + 1
                found = True
                break
        if not found:
            self.RegInfos.append( RegInfo( reginfo ) )

    def Sort(self):
        self.RegInfos.sort()

    def Count(self):
        return len( self.RegInfos )
    
    def __str__(self):
        str = 'Version : %s\n' % self.Name
        for r in self.RegInfos:
            str += '%s' % r
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )


class Program:
    "Structure to encapsulate a Program."
    def __init__(self, name, version, reginfo ):
        self.Name = name
        self.Versions = []
        self.Add( version, reginfo )
        
    def Add(self, version, reginfo):
        found = False
        for v in self.Versions:
            if v.Name.lower() == version.lower():
                v.Add( reginfo )
                found = True
                break
        if not found:
            self.Versions.append( Version( version, reginfo ) )

    def Sort(self):
        self.Versions.sort()
        for v in self.Versions:
            v.Sort()

    def Count(self):
        count = 0
        for v in self.Versions:
            count = count + v.Count()
        return count

    def __str__(self):
        str = 'Program : %s\n' % self.Name
        for v in self.Versions:
            str += '%s' % v
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )


class Company:
    "Structure to encapsulate a Company."
    def __init__(self, name, program, version, reginfo, url ):
        self.Name = name
        self.Programs = []
        self.URLs = []
        self.Add( program, version, reginfo, url )
        
    def Add(self, program, version, reginfo, url):
        found = False
        for u in self.URLs:
            if u.lower() == url:
                found = True
                break
        if not found and url != '':
            self.URLs.append( url )
            
        found = False
        for p in self.Programs:
            if p.Name.lower() == program.lower():
                p.Add( version, reginfo )
                found = True
                break
        if not found:
            self.Programs.append( Program( program, version, reginfo ) )

    def Sort(self):
        self.Programs.sort()
        self.URLs.sort()
        for p in self.Programs:
            p.Sort()
            
    def Count(self):
        count = 0
        for p in self.Programs:
            count = count + p.Count()
        return count
        
    def __str__(self):
        str = 'Company : %s\n' % self.Name
        for url in self.URLs:
            str += 'URL     : %s\n' % url
        for p in self.Programs:
            str += '%s' % p
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )
    

class Platform:
    "Structure to encapsulate a Platform."
    def __init__(self, name, company, program, version, reginfo, url):
        self.Name = name
        self.Companies = []
        self.Add( company, program, version, reginfo, url )
        
    def Add(self, company, program, version, reginfo, url):
        found = False
        for c in self.Companies:
            if c.Name.lower() == company.lower():
                c.Add( program, version, reginfo, url )
                found = True
                break
        if not found:
            self.Companies.append( Company( company, program, version, reginfo, url ) )

    def Sort(self):
        self.Companies.sort()
        for c in self.Companies:
            c.Sort()

    def Count(self):
        count = 0
        for c in self.Companies:
            count = count + c.Count()
        return count

    def __str__(self):
        str = 'Paltform: %s\n' % self.Name
        for c in self.Companies:
            str += '%s' % c
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )


class Serials:
    "Structure to encapsulate a database of serial numbers."
    def __init__(self):
        self.Platforms = []
        
    def Reassemble(self, parts):
        str = ''
        for part in parts:
            if part:
                if str != '':
                    str += '\t'
                str += part
            else:
                str += '\t'
        return str
    
    def IsMatching(self, str1, parts):
        str2 = self.Reassemble( parts )
        if len( str2 ) != len( str1 ):
            print('len(line) == %d, len(parts) == %d' % (len( str2 ), len( str1 )))
            return False
        else:
            i = 0
            count = len(str1)
            while i < count:
                if str1[i].lower() != str2[i].lower():
                    print('Doesn\'t match at char(%d)')
                    return False
                i = i + 1
            return True
        
    def Parse(self, line):
        match = regex.match( line )

        if not match or line.strip() != self.Reassemble( match.groups() ).strip():
            raise RuntimeWarning( 'Error parsing line: %s' % line )
        else:
            platform = ''
            company = ''
            program = ''
            version = ''
            reginfo = ''
            url = ''
            if match.group('platform'):
                platform = match.group('platform').strip()
            if match.group('company'):
                company = match.group('company').strip()
            if match.group('program'):
                program = match.group('program').strip()
            if match.group('version'):
                version = match.group('version').strip()
            if match.group('reginfo'):
                reginfo = match.group('reginfo').strip()
            if match.group('url'):
                url = match.group('url').strip()
            
            self.Add(platform, company, program, version, reginfo, url)


    def Add(self, platform, company, program, version, reginfo, url):
        found = False
        for p in self.Platforms:
            if p.Name.lower() == platform.lower():
                p.Add( company, program, version, reginfo, url )
                found = True
                break
        if not found:
            self.Platforms.append( Platform( platform, company, program, version, reginfo, url ) )

    def Sort(self):
        self.Platforms.sort()
        for p in self.Platforms:
            p.Sort()

    def Count(self):
        count = 0
        for p in self.Platforms:
            count = count + p.Count()
        return count
        
    def __str__(self):
        str = ''
        for p in self.Platforms:
            str += '%s' % p
        return str
    

def RecurseDirectory( dir ):
    print('Finding various SEU files...')    
    textFiles = []
    
    for root, dirs, files in os.walk( dir ):
        for file in files:
            if file.lower().endswith('.txt'):
                textFiles.append( os.path.join( root, file ) )

    textFiles.sort( cmp=lambda x,y: cmp(os.path.basename(x).lower(), os.path.basename(y).lower()) )
    return textFiles


def ParseSeuTextFiles(dir):
    global gErrors
    files = RecurseDirectory(dir)
    serials = Serials()
    count = 0
    
    for name in files:
        print('Parsing file \'%s\'' % os.path.basename(name))
        file = open( name, 'r' )
        lines = file.readlines()
        file.close()
        count = count + len( lines )
        for line in lines:
            try:
                serials.Parse(line)
            except RuntimeWarning as w:
                gErrors = gErrors + 1
    
    serials.Sort()
    return serials, count


if __name__ == '__main__':
    
    global gErrors, gDuplicates
    gErrors = 0
    gDuplicates = 0

    path = os.getcwd()
    serials, lines = ParseSeuTextFiles( path )
    count = serials.Count()
    print('Serial Numbers Count: %d' % count)
    print('Total Errors        : %d' % gErrors)
    print('Total Duplicates    : %d' % gDuplicates)
    print('Unaccounted Input   : %d' % (lines - count - gDuplicates - gErrors))


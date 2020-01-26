import os
import sys
import re
import glob
import pickle

import hash_utils
import custom_utils

gFilePattern = r'[12]\d{3}-\d[1-9]-\d[1-9].*\.txt$'

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
        self.RegInfos = {}
        self.Duplicates = 0
        self.Add( reginfo )
        
    def Add( self, reginfo ):
        chksum = hash_utils.md5sum(reginfo.lower())
        if chksum in list(self.RegInfos.keys()):
            self.Duplicates += 1
        else:
            self.RegInfos[chksum] = RegInfo( reginfo )

    def Count(self):
        return len( list(self.RegInfos.keys()) )
    
    def GetDuplicatesCount(self):
        return self.Duplicates
    
    def __str__(self):
        str = 'Version : %s\n' % self.Name
        reginfos = list(self.RegInfos.values())
        reginfos.sort()
        for reginfo in reginfos:
            str += '%s' % reginfo
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )

class Program:
    "Structure to encapsulate a Program."
    def __init__(self, name, version, reginfo ):
        self.Name = name
        self.Versions = {}
        self.Add( version, reginfo )
        
    def Add(self, version, reginfo):
        chksum = hash_utils.md5sum(version.lower())
        if chksum in list(self.Versions.keys()):
            self.Versions[chksum].Add( reginfo )
        else:
            self.Versions[chksum] = Version( version, reginfo )

    def Count(self):
        count = 0
        for v in list(self.Versions.values()):
            count += v.Count()
        return count

    def GetDuplicatesCount(self):
        count = 0
        for v in list(self.Versions.values()):
            count += v.GetDuplicatesCount()
        return count

    def Find(self, regex):
        str = ''
        if regex.search(self.Name):
            str += '%s\n' % self
        return str

    def __str__(self):
        str = 'Program : %s\n' % self.Name
        versions = list(self.Versions.values())
        versions.sort()
        for version in versions:
            str += '%s' % version
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )

class Company:
    "Structure to encapsulate a Company."
    def __init__(self, name, program, version, reginfo, url ):
        self.Name = name
        self.Programs = {}
        self.URLs = {}
        self.Add( program, version, reginfo, url )
        
    def Add(self, program, version, reginfo, url):
        # Add the URL to the list of URLs if we haven't seen it already
        chksum = hash_utils.md5sum(url.lower())
        if chksum not in list(self.URLs.keys()):
            self.URLs[chksum] = url
        
        # Add the software program serial information
        chksum = hash_utils.md5sum(program.lower())
        if chksum in list(self.Programs.keys()):
            self.Programs[chksum].Add( version, reginfo )
        else:
            self.Programs[chksum] = Program( program, version, reginfo )
            
    def Count(self):
        count = 0
        for p in list(self.Programs.values()):
            count += p.Count()
        return count
        
    def GetDuplicatesCount(self):
        count = 0
        for p in list(self.Programs.values()):
            count += p.GetDuplicatesCount()
        return count

    def Find(self, regex):
        str = ''
        for program in list(self.Programs.values()):
            str += program.Find(regex)
        return str

    def __str__(self):
        str = 'Company : %s\n' % self.Name
        urls = list(self.URLs.values())
        urls.sort()
        for url in urls:
            str += 'URL     : %s\n' % url
        programs = list(self.Programs.values())
        programs.sort()
        for program in programs:
            str += '%s' % program
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )
    

class Platform:
    "Structure to encapsulate a Platform."
    def __init__(self, name, company, program, version, reginfo, url):
        self.Name = name
        self.Companies = {}
        self.Add( company, program, version, reginfo, url )
        
    def Add(self, company, program, version, reginfo, url):
        chksum = hash_utils.md5sum(company.lower())
        if chksum in list(self.Companies.keys()):
            self.Companies[chksum].Add( program, version, reginfo, url )
        else:
            self.Companies[chksum] = Company( company, program, version, reginfo, url )

    def Count(self):
        count = 0
        for c in list(self.Companies.values()):
            count += c.Count()
        return count

    def GetDuplicatesCount(self):
        count = 0
        for c in list(self.Companies.values()):
            count += c.GetDuplicatesCount()
        return count

    def Find(self, regex):
        str = ''
        for company in list(self.Companies.values()):
            str += company.Find(regex)
        return str

    def __str__(self):
        str = 'Paltform: %s\n' % self.Name
        companies = list(self.Companies.values())
        companies.sort()
        for company in companies:
            str += '%s' % company
        return str

    def __cmp__(self, other):
        return cmp( self.Name, other.Name )

class Serials:
    "Structure to encapsulate a database of serial numbers."
    def __init__(self):
        self.Platforms = {}
        
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
    
    def ParseData(self, data):
        pattern = r'''
                    (?P<platform>[^\t]*?)   # Platform
                    \t                      # Tab
                    (?P<company>[^\t]*?)    # Company
                    \t                      # Tab
                    (?P<program>[^\t]*?)    # Program Name
                    \t                      # Tab
                    (?P<version>[^\t]*?)    # Version Number/Name
                    \t                      # Tab
                    (?P<reginfo>[^\t\n]*)   # Serial Number/Registration Information
                    (?:\t(?P<url>[^\n]*))?  # Optionally another tab followed by a URL
                    \n                      # Ending with a newline character
                  '''
    
        regex = re.compile( pattern, re.VERBOSE )
        str = ''
        errors = 0
        for match in regex.finditer(data):
            line = data[match.start() : match.end()]
            if line.strip() != self.Reassemble( match.groups() ).strip():
                str += 'Error parsing line: %s.\n' % line
                errors += 1
            else:
                platform = company = program = version = reginfo = url = ''
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
        return str, errors

    def Add(self, platform, company, program, version, reginfo, url):
        chksum = hash_utils.md5sum(platform.lower())
        if chksum in list(self.Platforms.keys()):
            self.Platforms[chksum].Add( company, program, version, reginfo, url )
        else:
            self.Platforms[chksum] = Platform( platform, company, program, version, reginfo, url )

    def Count(self):
        count = 0
        for p in list(self.Platforms.values()):
            count += p.Count()
        return count
        
    def GetDuplicatesCount(self):
        count = 0
        for p in list(self.Platforms.values()):
            count += p.GetDuplicatesCount()
        return count

    def Find(self, expr, platform = None):
        regex = re.compile(expr, re.I)
        str = ''
        if platform:
            chksum = hash_utils.md5sum(platform.lower())
            if chksum in list(self.Platforms.keys()):
                str += self.Platforms[chksum].Find(regex)
        else:
            for platform in list(self.Platforms.values()):
                str += platform.Find(regex)
        return str

    def __str__(self):
        str = ''
        platforms = list(self.Platforms.values())
        platforms.sort()
        for platform in platforms:
            str += '%s' % platform
        return str
    
def IsSEUTextFile(file):
    return re.search(gFilePattern, file)

def ParseSeuTextFiles(dir):
    serials = Serials()
    lines = 0
    errors = 0
    for name in custom_utils.get_files_in_directory(dir, predicate=IsSEUTextFile):
        print(('Parsing file \'%s\'' % os.path.basename(name)))
        with open(name) as file:
            data = file.read()
            lines += data.count('\n')
            str, e = serials.ParseData(data)
            errors += e
    return serials, lines, errors

def SearchPath(dir):
    if not os.path.isdir(dir):
        return False
    
    for file in os.listdir(dir):
        if re.search(gFilePattern, file):
            return True
    return False

def FindSerialsPath():
    serialsdir = r'Download\Utils\Serials\Serials 2000\Text'
    path = os.getcwd()
    if SearchPath(path):
        return path
    
    import win32file, win32con, win32api
    drives = win32api.GetLogicalDriveStrings().split('\x00')
    for drive in drives:
        if not drive or win32file.GetDriveType(drive) != win32con.DRIVE_FIXED:
            continue
        path = os.path.join(drive, serialsdir)
        if SearchPath(path):
            return path
        
    assert False, 'Unable to find the serials path'
    return path

def GetFileList(path):
    files = glob.glob(os.path.join(path, '*.txt'))
    new_files = []
    for file in files:
        new_files.append('%s - %s\n' % (os.path.basename(file), hash_utils.md5sum(file)))
    new_files.sort()
    return new_files

def CanUseParsedSerials(path):
    useParsedSerials = False
    savedSerials = os.path.join(path, 'serials.dat')
    dirlist = os.path.join(path, 'dir.lst')
    
    if os.path.isfile(dirlist):
        new_files = GetFileList(path)
        file = open(dirlist, 'r')
        old_files = file.readlines()
        file.close()
        if len(new_files) != len(old_files):
            os.remove(dirlist)
        elif new_files != old_files:
            for i in range(len(new_files)):
                if new_files[i] != old_files[i]:
                    print(('%s != %s' % (new_files[i], old_files[i])))
            os.remove(dirlist)
        elif not os.path.isfile(savedSerials):
            os.remove(dirlist)
        else:
            useParsedSerials = True
    return useParsedSerials

def SaveSerials(path):
    new_files = GetFileList(path)
    with open(os.path.join(path, 'dir.lst'), 'w') as file:
        file.write(''.join(new_files))

    with open(os.path.join(path, 'serials.dat'), 'wb') as file:
        try:
            pickle.dump(serials, file, pickle.HIGHEST_PROTOCOL)
        except:
            print('ERROR: Saving parsed serial structure to file.')

if __name__ == '__main__':
    path = FindSerialsPath()
    print(('Using serial directory found in \'%s\'' % path))
    saveSerials = True
    
    if CanUseParsedSerials(path):
        file = open(os.path.join(path, 'serials.dat'), 'rb')
        serials = pickle.load(file)
        file.close()
        print('Loaded Parsed Serials  : serials.dat')
        print(('Serial Numbers Count   : %d' % serials.Count()))
        saveSerials = False
    else:
        serials, lines, errors = ParseSeuTextFiles( path )
        count = serials.Count()
        duplicates = serials.GetDuplicatesCount()
        print(('Serial Numbers Count   : %d' % count))
        print(('Total Errors           : %d' % errors))
        print(('Total Duplicates       : %d' % duplicates))
        print(('Unaccounted Input      : %d' % (lines - count - duplicates - errors)))

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(('\nSearching for string   : %s' % arg))
            print((serials.Find(arg)))

    if saveSerials:
        SaveSerials(path)

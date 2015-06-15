#!/usr/bin/env python
import os
import re
import codecs
#import exceptions


def GetFileEncoding(path):
    with open(path) as input_file:
        bytes = input_file.read(3)
    if bytes[:len(codecs.BOM_UTF8)] == codecs.BOM_UTF8:
        return 'utf-8'
    elif bytes[:len(codecs.BOM_UTF16)] == codecs.BOM_UTF16:
        return 'utf-16'
    else:
        return 'latin_1'

    
def ReadFileLines(path):
    file_encoding = GetFileEncoding(path)
    with codecs.open(path, 'r', file_encoding) as file:
        if file_encoding == 'utf-8':
            file.seek(3)
        lines = file.readlines()
    return [line.encode() for line in lines]


def ReadFileData(path):
    file_encoding = GetFileEncoding(path)
    with codecs.open(path, 'r', file_encoding) as file:
        if file_encoding == 'utf-8':
            file.seek(3)
        data = file.read()
    return data.encode()


def FindFileInHeirarchy(dir, filename):
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if os.path.exists(os.path.join(dir, filename)):
            return os.path.abspath(dir)
        else:
            dir = parent
            parent = os.path.abspath(os.path.join(dir, '..' ))
    return None


def FindBuildRoot(dir):
    steer_cmake_dir = FindFileInHeirarchy(dir, 'steer.cmake')
    if not steer_cmake_dir:
        return None
    if os.path.isdir(os.path.join(steer_cmake_dir, 'build')) and os.path.isdir(os.path.join(steer_cmake_dir, 'code')):
        return os.path.join(steer_cmake_dir, 'build')
    else:
        return None


class CompilerVersion:
    def __init__(self, environ_key, release_version, project_extension):
        self.EnvironKey = environ_key
        self.ReleaseVersion = release_version
        self.ProjectExtension = project_extension
        self.BuildTypeX86 = True

    def _GetVcBinPath(self):
        common_tools = os.environ[self.EnvironKey]
        if self.BuildTypeX86:
            return os.path.normpath(os.path.join(common_tools, '..', '..', 'vc', 'bin'))
        else:
            return os.path.normpath(os.path.join(common_tools, '..', '..', 'vc', 'bin', 'x86_amd64'))

    def GetVcVarsPath(self):
        common_tools = os.environ[self.EnvironKey]
        if self.BuildTypeX86:
            return os.path.normpath(os.path.join(common_tools, 'vsvars32.bat'))
        else:
            return os.path.normpath(os.path.join(self._GetVcBinPath(), 'vcvarsx86_amd64.bat'))

    def GetLogFileName(self, project_filename):
        if self.ReleaseVersion < 2010:
            return 'BuildLog.htm'
        else:
            return os.path.splitext(os.path.basename(project_filename))[0] + '.log'

    def _ParseNewStyleLogFile(self, logfile_path):
        lines = ReadFileLines(logfile_path)

        # Set the compiler type (x86 or x64) should be done somewhere else!
        self.BuildTypeX86 = re.search(r'VC\\bin\\(?:x86_)?amd64\\CL\.exe', ''.join(lines), re.I) == None

        cl = os.path.join(self._GetVcBinPath(), 'CL.exe')
        raw_switches = None
        for line in lines:
            if line.lower().strip().startswith(cl.lower()):
                raw_switches = line.strip()[len(cl):].strip()
                break
        assert(raw_switches)

        return raw_switches

    def _ParseOldStyleLogFile(self, logfile_path):
        data = ReadFileData(logfile_path)

        # Set the compiler type (x86 or x64) should be done somewhere else!
        self.BuildTypeX86 = re.search(r'Configuration:[^|]+|x64', data, re.I) == None

        pattern = r'Creating command line "cl.exe[^"]*"\s*Creating temporary file "[^"]*" with contents\s*\[(?P<switches>.*?)\]'
        match = re.search(pattern, data, re.S)
        if not match:
            raise exceptions.RuntimeError('Unable to find a compile line in %s' % logfile_path)

        raw_switches = match.group('switches').replace('&quot;', '"').replace('\r', '').replace('\n', ' ')

        return raw_switches

    def ParseLogFile(self, filename):
        raw_switches = self._ParseOldStyleLogFile(filename) if self.ReleaseVersion < 2010 else self._ParseNewStyleLogFile(filename)

        # First assume that each forward slash if not preceeded by whitespace must be a directory seperator.
        #  Since we are going to split on forward slashes this will end up messing the split up.
        #  this is a window-ism!
        raw_switches = re.sub('([^ ])/', r'\1\\', raw_switches)
        
        # Remove all of the source files from the line
        raw_switches = re.sub(' "?[^ ]+.cpp"?', '', raw_switches)

        unwanted_switches = ['FA', 'Fa', 'Fd', 'Fe', 'Fm', 'Fo', 'Fp', 'FR', 'Fr', 'Fx']
        switches = []
        for switch in raw_switches.split('/'):
            switch = switch.strip()
            if len(switch) == 0 or switch[:2] in unwanted_switches:
                continue
            switches.append('/' + switch)

        return switches

class CompilerSelector:
    def __init__(self):
        self.CompilerVersions = \
        [
            CompilerVersion('VS100COMNTOOLS', 2010, '.vcxproj'),
            CompilerVersion('VS90COMNTOOLS', 2008, '.vcproj'),
            CompilerVersion('VS80COMNTOOLS', 2005, '.vcproj'),
            CompilerVersion('VS71COMNTOOLS', 2003, '.vcproj')
        ]

    def GetInstalledCompilerVersion(self):
        versions = [version for version in self.CompilerVersions if version.EnvironKey in os.environ]
        if len(versions) == 0:
            raise exceptions.RuntimeError('Visual Studio is not installed!')
        
        versions.sort(lambda x, y: x.ReleaseVersion > y.ReleaseVersion)
        return versions[0]


class CompilerCommand:
    def __init__(self, source_path, preprocess_file):
        self.SourcePath = source_path
        self.ProjectDirectory = self._GetProjectDirectory()
        self.PreprocessSourceFile = preprocess_file
        self.CompilerVersion = CompilerSelector().GetInstalledCompilerVersion()
        self.CompilerSwitches = self._GatherCompilerSwitches()

    def _GetProjectDirectory(self):
        build_root = FindBuildRoot(os.path.dirname(self.SourcePath))
        if not build_root:
            return os.path.dirname(self.SourcePath)
        else:
            assert(len(os.path.dirname(self.SourcePath)) > len(build_root))
            proj_root = os.path.join(build_root, os.path.dirname(self.SourcePath)[len(build_root):])
            return proj_root

    def _FindProjectFile(self):
        project_file = None
        project_directory = os.path.basename(self.ProjectDirectory).lower()
        for filename in os.listdir(self.ProjectDirectory):
            filename_base, extension = os.path.splitext(filename.lower())
            if extension == self.CompilerVersion.ProjectExtension and filename_base == project_directory:
                return os.path.join(self.ProjectDirectory, filename)

        raise exceptions.RuntimeError('Unable to find the project to compile %s' % self.SourcePath)

    def _FindLogFile(self):
        paths = []
        log_filename = self.CompilerVersion.GetLogFileName(self._FindProjectFile())
        for root, dirs, files in os.walk(self.ProjectDirectory):
            for file in files:
                if file.lower() == log_filename.lower():
                    return os.path.join(root, file)

        raise exceptions.RuntimeError('Unable to find the log file to compile %s' % self.SourcePath)

    def _GatherCompilerSwitches(self):
        switches = None
        try:
            switches = self.CompilerVersion.ParseLogFile(self._FindLogFile())
        except:
            switches = ['/c', '/Od', '/D "WIN32"', '/D "_DEBUG"', '/EHa', '/RTC1', '/MTd', '/W4', '/WX', '/TP', '/wd4290', '/wd4127', '/wd4702', '/wd4189', '/wd4063']

        if self.PreprocessSourceFile:
            switches.insert(1, '/C')
            switches.insert(1, '/P')
        return switches
    
    def AddIncludePath(self, path):
        include_switch = '/I"%s"' % path if path.find(' ') != -1 else '/I%s' % path
        self.CompilerSwitches.append(include_switch)

    def __str__(self):
        source_path = '"%s"' % self.SourcePath if self.SourcePath.find(' ') != -1 else '%s' % self.SourcePath
        compiler_command = 'cl.exe %s %s' % (' '.join(self.CompilerSwitches), source_path)
        command = '"%s" && %s' % (self.CompilerVersion.GetVcVarsPath(), compiler_command)
        return command
 

if __name__ == '__main__':
    lines = ReadFileLines(r'D:\code\trunk\ediscovery\Connectors\EnterpriseVaultIntegration\eDiscovery.EvIntegration.NsfBuilder\obj\Debug\eDiscovery.EvIntegration.NsfBuilder.log')
    data = ReadEntireFile(r'D:\code\trunk\ediscovery\Connectors\NotesCollector\ADLNCollect\obj\Debug\BuildLog.htm')
    data = ReadEntireFile(r'D:\out.txt')

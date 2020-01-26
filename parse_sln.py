import os, re, sys

class Project:
    def __init__(self, name, path, type, id):
        self.mName = name
        self.mPath = path
        self.mType = type
        self.mId = id
        self.mDependencies = []
        self.mConfigurations = []

    def AddDependency(self, id):
        assert( id not in self.mDependencies )
        self.mDependencies.append(id)
    
    def AddConfig(self, config):
        assert( config not in self.mConfigurations )
        self.mConfigurations.append(config)
        
    def DependenciesEqual(self, other):
        if len(self.mDependencies) != len(other.mDependencies):
            print(('INFO: Project %s has a different number of project dependencies.' % self.mName))
            return False

        self.mDependencies.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        other.mDependencies.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        count = len( self.mDependencies )
        i = 0
        while i < count:
            if self.mDependencies[i].lower() != other.mDependencies[i].lower():
                print(('INFO: In project %s the dependency %s is not equal to %s' % ( self.mName, self.mDependencies[i], other.mDependencies[i] )))
                return False
            i += 1
            
        return True
    
    def ConfigurationsEqual(self, other):
        if len(self.mConfigurations) != len(other.mConfigurations):
            print(('INFO: Project %s has a different number of project configurations.' % self.mName))
            return False

        self.mConfigurations.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        other.mConfigurations.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        count = len( self.mConfigurations )
        i = 0
        while i < count:
            if self.mConfigurations[i].lower() != other.mConfigurations[i].lower():
                print(('INFO: In project %s the configuration %s is not equal to %s' % ( self.mName, self.mConfigurations[i], other.mConfigurations[i] )))
                return False
            i += 1
            
        return True
    
    def __ne__(self, other):
        return not ( self == other )
    
    def __eq__(self, other):
        if self.mName.lower() != other.mName.lower():
            print(('INFO: Project name %s is not equal to %s' % ( self.mName, other.mName )))
            return False
        elif self.mPath.lower() != other.mPath.lower():
            print(('INFO: In project %s the path %s is not equal to %s' % ( self.mName, self.mPath, other.mPath )))
            return False
        elif self.mType.lower() != other.mType.lower():
            print(('INFO: Project type %s is not equal to %s' % ( self.mName, self.mType, other.mType )))
            return False
        elif self.mId.lower() != other.mId.lower():
            print(('INFO: Project id %s is not equal to %s' % ( self.mName, self.mId, other.mId )))
            return False
        return self.DependenciesEqual(other) and self.ConfigurationsEqual(other)
        #return self.mName.lower() == other.mName.lower() and \
        #       self.mPath.lower() == other.mPath.lower() and \
        #       self.mType.lower() == other.mType.lower() and \
        #       self.mId.lower() == other.mId.lower() and \
        #       self.DependenciesEqual(other) and \
        #       self.ConfigurationsEqual(other)

class Solution:
    def __init__(self, data):
        self.mProjects = {}
        self.mSlnConfigs = []
        self.mGuidPattern = '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
        header = 'Microsoft Visual Studio Solution File, Format Version 9.00'
        assert( re.search(header, data, re.I).start() == 0 )
        
        self.ParseProjects(data)
        self.ParseSlnConfigs(data)
        self.ParseProjectConfigs(data)
        
    def ParseProjectConfigs(self, data):
        pattern = r'GlobalSection\(ProjectConfigurationPlatforms\) = postSolution.*?EndGlobalSection'
        match = re.search(pattern, data, re.I |re.S)
        if not match:
            return
        
        pattern = r'\{(?P<guid>' + self.mGuidPattern + r')\}(?P<config>\.[^\n]*?)\n'
        for i in re.finditer(pattern, data[ match.start() : match.end() ]):
            id = i.group('guid').strip()
            config = i.group('config').strip()
            assert( id.lower() in self.mProjects )
            self.mProjects[id.lower()].AddConfig(config)

    def ParseSlnConfigs(self, data):
        pattern = r'GlobalSection\(SolutionConfigurationPlatforms\) = preSolution\n.*?EndGlobalSection'
        match = re.search(pattern, data, re.I |re.S)
        if not match:
            return
        pattern = r'\t\t(?P<config>[^\n]*?)\n'
        for i in re.finditer(pattern, data[ match.start() : match.end() ]):
            self.mSlnConfigs.append( i.group('config').strip() )
            
    def ParseProjects(self, data):
        projPattern = r'Project\("\{(?P<typeguid>' + self.mGuidPattern + r')\}"\) = "(?P<project>[^"]*?)", "(?P<path>[^"]*?)", "\{(?P<guid>' + self.mGuidPattern + r')\}".*?EndProject'
        dependPattern = r'\{(?P<guid>' + self.mGuidPattern + r')\} = \{\1\}'
        regexDepend = re.compile( dependPattern, re.I | re.S )
        regexProj = re.compile( projPattern, re.I | re.S )
        
        for i in regexProj.finditer(data):
            id = i.group('guid').strip()
            project = Project( i.group('project').strip(), i.group('path').strip(), i.group('typeguid').strip(), id )
            for j in regexDepend.finditer( data[ i.start() : i.end() ] ):
                project.AddDependency( j.group('guid').strip() )

            assert( id.lower() not in self.mProjects )
            self.mProjects[id.lower()] = project

    def ConfigsEqual(self, other):
        if len(self.mSlnConfigs) != len(other.mSlnConfigs):
            print('INFO: The number of solution configurations are not the same.')
            return False

        self.mSlnConfigs.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        other.mSlnConfigs.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        count = len(self.mSlnConfigs)
        i = 0
        while i < count:
            if self.mSlnConfigs[i].lower() != other.mSlnConfigs[i].lower():
                print(('INFO: Solution configuration %s is not equal to %s' % ( self.mSlnConfigs[i], other.mSlnConfigs[i] )))
                return False
            i += 1
        return True

    def ProjectsEqual(self, other):
        if len(list(self.mProjects.keys())) != len(list(other.mProjects.keys())):
            print('INFO: There are a different number of projects.')
            return False
        
        keys1 = list(self.mProjects.keys())
        keys2 = list(other.mProjects.keys())
        keys1.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        keys2.sort( cmp=lambda x,y: cmp(x.lower(), y.lower()) )
        count = len(keys1)
        i = 0
        
        while i < count:
            key1 = keys1[i].lower()
            key2 = keys2[i].lower()
            if key1 != key2:
                print(('INFO: Solution dependency %s is not equal to %s' % ( keys1[i], keys2[i] )))
                return False
            elif self.mProjects[key1] != other.mProjects[key2]:
                return False
            i += 1
            
        return True
        
    def __eq__(self, other):
        return self.ConfigsEqual(other) and self.ProjectsEqual(other)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('ERROR: Invalid command line. Usage: ParseSln.py <solution file> <solution file>')
        sys.exit(2)
    
    file = open( sys.argv[1], 'r' )
    data = file.read()
    file.close()
    sln1 = Solution( data )
    
    file = open( sys.argv[2], 'r' )
    data = file.read()
    file.close()
    sln2 = Solution( data )
    
    if sln1 == sln2:
        print('SUCCESS: The solutions contents match')
        sys.exit(0)
    else:
        print('FAILED: The solutions do not match')
        sys.exit(1)

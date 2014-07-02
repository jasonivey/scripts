import os, sys, re, Utils

class IsPerforceSource:
    def __init__(self):
        self.mRegex = re.compile( '^.*\.(?:h|hpp|c|cpp|inl)$', re.IGNORECASE )
    
    def __call__(self, file):
        return self.mRegex.match(file)

def ReadFile( filename ):
    file = open( filename, 'r' )
    data = file.read()
    file.close()
    return data

def GetIncludes():
    dirs = []
    if 'VS80COMNTOOLS' in os.environ:
        dirs.append( os.path.abspath( os.path.join( os.environ['VS80COMNTOOLS'], '..', '..', 'vc', 'include' ) ) )
    
    sandbox = Utils.FindSandbox( os.getcwd() )
    workspace = os.path.join( sandbox, 'ws' )
    dirs.append(sandbox)
    dirs.append(workspace)
    
    dirs.append( os.path.join( sandbox, 'boost' ) )
    dirs.append( os.path.join( sandbox, 'cache' ) )
    dirs.append( os.path.join( sandbox, 'vs.net', 'PqPatches' ) )
    dirs.append( os.path.join( sandbox, 'MsSdk', 'Include' ) )
    dirs.append( os.path.join( sandbox, 'MSVC', 'VC98' ) )
    dirs.append( os.path.join( sandbox, 'MSVC', 'VC98', 'Include' ) )
    dirs.append( os.path.join( sandbox, 'MSVC', 'VC98', 'ATL', 'Include' ) )
    dirs.append( os.path.join( sandbox, 'MSVC', 'VC98', 'MFC', 'Include' ) )
    
    for d in os.listdir(workspace):
        path = os.path.join(workspace, d)
        if os.path.isdir(path) and not path.lower().endswith('wsfiles') and not path.lower().endswith('extensions'):
            dirs.append(path)
    
    return dirs

def FindPath( current, partial, dirs ):
    path = os.path.normpath( os.path.join( current, partial ) )
    if os.path.isfile(path):
        return path
    
    for dir in dirs:
        path = os.path.normpath( os.path.join( dir, partial ) )
        if os.path.isfile(path):
            return path
    return None
    
if __name__ == '__main__':
    sandbox = Utils.FindSandbox(os.getcwd())
    sme_dir = os.path.join(sandbox, 'ws', 'Sme', 'Dev')
    disk_layout = os.path.join(sme_dir, 'DiskLayout')
    volume_management = os.path.join(sme_dir, 'VolumeManagement')
    assert( os.path.isdir(sme_dir) )
    assert( os.path.isdir(disk_layout) )
    assert( os.path.isdir(volume_management) )
    
    dirs = GetIncludes()
    pattern = r'^\s*#include\s+["<](?P<include>[^">]+)[">]'
    regex = re.compile(pattern, re.M)
    
    for name in Utils.RecurseDirectory( disk_layout, IsPerforceSource(), False ):
        data = ReadFile(name)
        
        for i  in regex.finditer(data):
            include = FindPath( os.path.dirname(name), i.group('include').strip(), dirs )
            if include and re.search('VolumeManagement', include, re.I):
                if os.path.dirname(include) != volume_management:
                    print(include)
                    print(name)
                    print('ERROR: The disk layout module is referring to an implementation ' \
                    'of the volume management module.\n\tThe base classes may refer to each '\
                    'other but none of the derived classes should ever point to one another.')
                    
                    
    for name in Utils.RecurseDirectory( volume_management, IsPerforceSource(), False ):
        data = ReadFile(name)
        
        for i  in regex.finditer(data):
            include = FindPath( os.path.dirname(name), i.group('include').strip(), dirs )
            if include and re.search('DiskLayout', include, re.I):
                if os.path.dirname(include) != disk_layout:
                    print(include)
                    print(name)
                    print('ERROR: The disk layout module is referring to an implementation ' \
                    'of the volume management module.\n\tThe base classes may refer to each '\
                    'other but none of the derived classes should ever point to one another.')
    
    print('Done')
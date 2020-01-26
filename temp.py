import sys
import os
import re
import zipfile
import shutil
import string
import stat
import time

def GetUniqueFileName( name ):
    name = re.sub( ' *([\(\[].*?[\)\]]) *\.', '.', name )

    i = 1
    while os.path.exists( name ):
        base, ext = os.path.splitext( name )
        name = base + ' ' + str(i) + ext
        i = i + 1

    return name


def MoveFromSubDirs():
    src = 'G:\\Nintendo'
    dst = 'g:\\nes-roms'
    
    #deltree( dst )
    #os.mkdir( dst )
    
    for root, dirs, files in os.walk( src ):
        for f in files:
            
            if root.lower() == src.lower():
                continue
            
            if not f.lower().endswith( '.nes' ):
                continue
            
            file = os.path.join( root, f )
            
            name = GetUniqueFileName( os.path.join(dst, f) )
            print(('Moving %s to %s' % ( f, os.path.basename(file) )))
            shutil.move( file, name )
            
            
def ExtractFromZipFiles():
    dst = 'g:\\roms'
    src = 'g:\\snes'
    deltree( dst )
    os.mkdir( dst )
        
    for root, dirs, files in os.walk( src ):
        for f in files:
            file = os.path.join( root, f )
            if file.lower().endswith( '.zip' ):
                zfobj = zipfile.ZipFile(file)
                for name in zfobj.namelist():
                    dstFile = GetUniqueFileName( os.path.join(dst, name) )
                    print(('Copying %s from archive %s' % ( os.path.basename(dstFile), f )))
                    outfile = open( dstFile, 'wb')
                    outfile.write(zfobj.read(name))
                    outfile.close()

    
def deltree( dir ):
    if os.path.exists( dir ):
        for root, dirs, files in os.walk( dst ):
            for file in files:
                os.remove( os.path.join( root, file ) )
        os.removedirs( dir )
    

def ContainsProjectFile(name, dir):
    basename = os.path.splitext(name)[0]
    return os.path.isfile(os.path.join(dir, basename, '.vcproj')) or os.path.isfile(os.path.join(dir, basename, '.csproj'))


def GetPotentialDirParts(basename, platform, config):
    dirs = []
    managed_dirname = os.path.join(basename, 'bin', '%s' % config).lower()
    dirs.append(managed_dirname)
    if platform == 'x64':
        native_dirname = os.path.join(basename, '%s.%s' % (config, platform)).lower()
        dirs.append(native_dirname)
        ftk_build_dirname = os.path.join('FTK-2', 'bin', '%s.%s' % (config, platform)).lower()
        dirs.append(ftk_build_dirname)
    else:
        native_dirname = os.path.join(basename, '%s' % config).lower()
        dirs.append(native_dirname)
        ftk_build_dirname = os.path.join('FTK-2', 'bin', '%s' % config).lower()
        dirs.append(ftk_build_dirname)
    ftk_built_dirname = 'FTKBuiltDlls'.lower()
    dirs.append(ftk_built_dirname)
    return dirs

    
def SelectCorrectPath(paths, platform, config):
    correct_paths = []
    potential_dir_parts = GetPotentialDirParts(os.path.splitext(os.path.basename(paths[0]))[0], platform, config)
    for path in paths:
        dirname = os.path.dirname(path).lower()
        result = [part for part in potential_dir_parts if dirname.find(part) != -1]
        if len(result) > 0:
            correct_paths.append(path)
    
    if len(correct_paths) == 0:
        correct_paths = paths
    
    if len(correct_paths) == 1:
        return correct_paths[0]

    print(('INFO: found multiple paths for %s' % os.path.basename(correct_paths[0])))
    for index, path in enumerate(correct_paths):
        print((' %d. %s %s' % (index + 1, time.ctime(os.stat(path)[stat.ST_MTIME]), os.path.dirname(path))))
    selection = int(eval(input('Select correct: '))) - 1
    if selection < 0 or selection >= len(correct_paths):
        print('ERROR: selected an invalid option')
        return None
    else:
        return correct_paths[selection]


if __name__ == '__main__':
    import files
    
    orig_array = files.debug_files
    dbg_files = []
    for file in files.debug_files:
        dbg_files.append([file[0].lower(), file[1].lower()])
    
    new_dbg_files = []
    checked = [] 
    for i, e in enumerate(dbg_files): 
        if e not in checked: 
            checked.append(e)
            new_dbg_files.append(orig_array[i])
    
    with open(r'd:\full-file-paths-mod-new.txt', 'w') as output_file:
        for new_dbg_file in new_dbg_files:
            output_file.write('[r\'%s\', r\'%s\'], \\\n' % (new_dbg_file[0], new_dbg_file[1]))
    
    #for root, dirs, files in os.walk( 'G:\\nes-roms' ):
    #    for file in files:
    #        #name = re.sub( '(\w)(\()', '\\1 \\2', file )
    #        #name = re.sub( '^[a-z]', '\\1 \\2', file )
    #        name = re.sub( '(\w)([A-Z0-9])', '\\1 \\2', file )
    #
    #        for match in re.finditer( ' [a-z]', name ):
    #            name = name[0 : match.start() + 1] + \
    #                   name[match.start() + 1].upper() + \
    #                   name[match.start() + 2:]
    #
    #        #name = file[0].upper() + file[ 1: ]
    #        #name = re.sub( '_', ' ', file )
    #        src = os.path.join(root, file)
    #        dst = os.path.join(root, name)
    #                             
    #        if name != file:
    #            if name.lower() != file.lower() and os.path.exists(dst):
    #                dst = GetUniqueFileName(dst)
    #            print(src + ' to ' + dst)
    #            os.rename( src, dst )
    
    #start_dir = r'C:\Users\jivey\Pictures'
    #for root, dirs, files in os.walk(start_dir):
    #    for dir in dirs:
    #        path = os.path.join(root, dir)
    #        parentDir = os.path.dirname(path)
    #        if parentDir.lower() != start_dir.lower():
    #            continue
    #        picasa_ini = os.path.join(path, '.picasa.ini')
    #        if re.search(r'\d{4}-\d{2}-\d{2}$', dir) and len(os.listdir(path)) == 1 and os.path.isfile(picasa_ini):
    #            print('Removing %s' % dir)
    #            os.remove(picasa_ini)
    #            os.rmdir(path)


    #for file in files:
    #    parentDir = os.path.dirname(root)
    #    if parentDir.lower() != start_dir.lower():
    #        continue
    #    src = os.path.join(root, file)
    #    dst = os.path.join(start_dir, 'Moved', file)
    #    if re.search(r'\d{4}-\d{2}-\d{2}$', root) and not file.startswith('.'):
    #        print('Moving %s' % file)
    #        if not '-s' in sys.argv[1:]:
    #            shutil.move(src, dst)
    
    settings =  { \
                '$(ConfigurationName)' : 'Debug',
                '$(PlatformName)' : 'x64',
                '$(ProjectName)' : None,
                }

    binary_files = []
    with open(r'd:\files.txt') as input_file:
        # read lines into array, strip empty chars and lower each char on each index, and delete empty indexes
        binary_files = [value for value in map(string.lower, list(map(string.strip, input_file.readlines()))) if len(value) != 0]
    
    print('Collecting paths for all binaries...')
    all_binary_files = {}
    start_dir = r'd:\code\branch'
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.lower() not in binary_files:
                continue
            full_path = os.path.join(root, file)
            if file.lower() in list(all_binary_files.keys()):
                all_binary_files[file.lower()].append(full_path)
            else:
                all_binary_files[file.lower()] = [full_path]


    #start_dir = r'd:\code\branch'
    #project_files = {}
    #for root, dirs, files in os.walk(start_dir):
    #    for file in files:
    #        basename, extension = map(string.lower, os.path.splitext(file))
    #        if extension == '.vcproj' or extension == '.csproj':
    #            project_path = root
    #            if basename in project_files.keys():
    #                project_files[basename].append(project_path)
    #                #print('ERROR: found duplicate project files for project %s' % basename)
    #                #print(' 1. %s' % project_files[basename])
    #                #print(' 2. %s' % project_path)
    #                #answer = int(input('Which is correct: '))
    #                #if answer == 2:
    #                #    project_files[basename] = project_path
    #            else:
    #                project_files[basename] = [project_path]

    print('Selecting the correct source path for all binaries...')
    correct_paths = []
    for binary_file in binary_files:
        if binary_file not in list(all_binary_files.keys()):
            print(('ERROR: binary %s was never found' % binary_file))
            source_path = eval(input('Enter source path: '))
            all_binary_files[binary_file] = [source_path]
        
        source_path = SelectCorrectPath(all_binary_files[binary_file], 'x64', 'Debug')
        correct_paths.append(source_path)
            
    with open(r'd:\full-file-paths.txt', 'w') as output_file:
        output_file.write('\n'.join(correct_paths))

            #basename, extension = binary_file.splitext(binary_file)
            #source_path = None
            #if basename not in project_files.keys():
            #    while not source_path:
            #        print('ERROR: project for binary %s was never found' % binary_file)
            #        source_path = input('Enter source path: ')
            #        if source_path.lower() == 'quit' or source_path.lower() == 'continue':
            #            source_path = None
            #            break
            #        elif not os.path.isfile(os.path.join(source_path, binary_file)):
            #            print('ERROR: %s is an invalid path' % os.path.join(source_path, binary_file))
            #            source_path = None
            #elif len(project_files[basename]) > 1:
            #    print('INFO: found more than one binary directory')
            #    for index, project_path in enumerate(project_files[basename]):
            #        print(' %d. %s' % (index + 1, project_path))
            #    selection = int(input('Which is correct: '))
            #    
            #if source_path and os.path.isfile(os.path.join(source_path, binary_file)):
            #    output_file.writeline(os.path.join(source_path, binary_file))


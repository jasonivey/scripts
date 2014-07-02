import os
import sys
import re
import subprocess
import uuid
import exceptions
import CompilerCommand
import exceptions

   
def IsSourceFile(filename):
    extension = os.path.splitext(filename)[1].lower()
    return extension == '.cpp' or extension == '.h' or extension == '.inl'


def GetLogfileName(temp_dir):
    return os.path.normpath(os.path.join(temp_dir, 'buildlog.txt'))


def CompileCpp(compiler_command, temp_dir, verbose):
    if verbose:
        print(str(compiler_command))
        
    with open(GetLogfileName(temp_dir), 'w+') as logfile:
        return subprocess.Popen(str(compiler_command), stderr = logfile, stdout = logfile).wait() == 0

    
def CompileHeader(compiler_command, temp_dir, verbose):
    compiler_command.AddIncludePath(os.path.dirname(compiler_command.SourcePath))
    header_file = os.path.basename(compiler_command.SourcePath)
    compiler_command.SourcePath = os.path.join(temp_dir, os.path.splitext(header_file)[0] + '.cpp')
    
    with open(compiler_command.SourcePath, 'w') as file:
        file.write('#include "%s"\n' % header_file)

    status = CompileCpp(compiler_command, temp_dir, verbose)
    os.remove(compiler_command.SourcePath)
    return status


def CompileFiles(sources, verbose, preprocessor):
    if len(sources) == 0:
        return

    temp_dir = os.path.join( os.environ['TEMP'], 'VerifySource-%s' % uuid.uuid1() )
    os.mkdir(temp_dir)

    for path in sources:
        compiler_command = CompilerCommand.CompilerCommand(path, preprocessor)
        if path.lower().endswith('.h'):
            retval = CompileHeader(compiler_command, temp_dir, verbose)
        else:
            retval = CompileCpp(compiler_command, temp_dir, verbose)

        print('Compile: %s %s' % (path, 'succeeded' if retval else 'failed'))
        if not retval and verbose:
            with open(GetLogfileName(temp_dir)) as logfile:
                print(''.join(logfile.readlines()))

    os.remove(os.path.join(temp_dir, 'buildlog.txt'))
    os.rmdir(temp_dir)
    
    
def CompileDirectory(dir, verbose, preprocessor):
    sources = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if IsSourceFile(os.path.join(root, file)):
                sources.append(os.path.join(root, file))
                
    CompileFiles(sources, verbose, preprocessor)
    
    
def ParseArgs(args):
    dirs = []
    files = []
    verbose = False
    preprocessor = False
    for arg in args:
        if (arg.startswith('-') or arg.startswith('/')) and arg.lower()[1:].startswith('v'):
            verbose = True
        elif (arg.startswith('-') or arg.startswith('/')) and arg.lower()[1:].startswith('p'):
            preprocessor = True
        elif (arg.startswith('-') or arg.startswith('/')) and arg.lower()[1:].startswith('p'):
            preprocessor = True
        elif os.path.isdir(arg):
            dirs.append(os.path.abspath(arg))
        elif os.path.isfile(arg):
            files.append(os.path.abspath(arg))
    
    if len(files) == 0 and len(dirs) == 0:
        dirs.append(os.getcwd())
        
    return dirs, files, verbose, preprocessor


if __name__ == '__main__':
    dirs, files, verbose, preprocessor = ParseArgs(sys.argv[1:])

    if len(dirs) > 0:
        for dir in dirs:
            CompileDirectory(dir, verbose, preprocessor)
    elif len(files) > 0:
        CompileFiles(files, verbose, preprocessor)

 
import os, sys, re
from stat import *
from Utils import RecurseDirectory, FindSandbox


class IsPreBuildAll:
    def __init__(self):
        self.mRegex = re.compile('^.*prebuildall\.py$', re.I)
        
    def __call__(self, file):
        return self.mRegex.match(file)


def FindPlatforms(args):
    #platforms = [args[i + 1] for i in range(len(args)) if args[i].lower() == '-platform' and i + 1 < len(args)]

    platforms = []
    newargs = []
    i = 0
    while i < len(args):
        if args[i].lower() == '-platform' and i + 1 < len(args):
            platforms.append(args[i + 1])
            i += 2
        else:
            newargs.append(args[i])
            i += 1
    
    if len(platforms) == 0:
        platforms = ['-win32']
        
    return platforms, newargs


def ReadArgs(dir):
    args = []
    if not os.path.isfile(os.path.join(dir, 'g.bat')) and not os.path.isfile(os.path.join(dir, 'i.bat')):
        return args
    
    if os.path.isfile(os.path.join(dir, 'g.bat')):
        filename = os.path.join(dir, 'g.bat')
    elif os.path.isfile(os.path.join(dir, 'i.bat')):
        filename = os.path.join(dir, 'i.bat')
        
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()
    
    assert( len(lines) == 1 )
    rawargs = lines[0].split()
    
    for i in range(len(rawargs)):
        if (rawargs[i].lower() == '-cfg' or rawargs[i].lower() == '-platform' or rawargs[i].lower() == '-sandbox') and i + 1 < len(rawargs):
            args.append(rawargs[i])
            args.append(rawargs[i + 1])
        elif rawargs[i].lower() == '-verbose':
            args.append(rawargs[i])
            
    return args



if __name__ == '__main__':

    dir = os.path.join(FindSandbox( os.getcwd() ), 'ws')
    orig_args = sys.argv[1:] if len(sys.argv) > 1 else ReadArgs(dir)
    curDir = os.getcwd()
    os.chdir( dir )
    
    lines = []
    platforms, args = FindPlatforms(orig_args)
    files = RecurseDirectory(dir, IsPreBuildAll())
    
    for platform in platforms:
        for file in files:
            command = '%s %s %s -platform %s' % (os.path.join(dir, 'pyrun'), file, ' '.join(args), platform)
            print(('Running %s %s -platform %s' % (file, ' '.join(args), platform)))
            for line in os.popen4( command, 't' )[1].readlines():
                sys.stdout.write( line )
            print('')

    command = '%s %s %s' % (os.path.join(dir, 'pyrun'), r'Raptor\Dev\Rebrand.py', ' '.join(orig_args))
    print((r'Running Raptor\Dev\Rebrand.py %s' % ' '.join(orig_args)))
    for line in os.popen4( command, 't' )[1].readlines():
        sys.stdout.write( line )

    os.chdir( curDir )

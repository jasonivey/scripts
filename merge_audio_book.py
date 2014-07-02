import os, sys, shutil
from . import Utils

def ParseArgs(args):
    verbose = False
    simulated = False
    dir = os.getcwd()
    
    for arg in args:
        if Utils.IsSwitch(arg) and arg[1].lower() == 'v':
            verbose = True
        elif Utils.IsSwitch(arg) and arg[1].lower() == 's':
            simulated = True
        elif os.path.isdir(arg):
            dir = arg
            
    return verbose, simulated, dir


if __name__ == '__main__':
    verbose, simulated, dir = ParseArgs(sys.argv)
    
    paths = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith('.mp3'):
                paths.append( os.path.join(root, file) )
                
    paths.sort()
    dstDir = ''
    if len(paths):
        dstDir = paths[0][:os.path.dirname(paths[0]).rfind(' - ')]
        if verbose:
            print('Using %s as destination.' % dstDir)
        if not os.path.isdir(dstDir):
            if not simulated:
                os.mkdir(dstDir)
            if verbose:
                print('Creating directory %s.' % dstDir)

    for i, src in enumerate(paths):
        dst = '%03d%s' % (i + 1, src[ src.rfind(os.path.sep) + 3 : ])
        dst = os.path.join(dstDir, dst)
        if not simulated:
            shutil.copyfile(src, dst)
        if verbose:
            print('Copied %s to %s.' % (src, dst))

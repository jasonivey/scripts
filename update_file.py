import sys
import os
import pysvn
import stat
import shutil
import datetime

import hash_utils

def GetSvnStatus(client, path):
    try:
        statuss = client.status(path)
        for status in statuss:
            if status.path == path:
                return status
    except pysvn.ClientError as e:
        return None
    assert False, 'Unknown SVN status'

def DoesExistInSvn(client, path):
    status = GetSvnStatus(client, path)
    return status and \
        status.text_status is not pysvn.wc_status_kind.unversioned and \
        status.text_status is not pysvn.wc_status_kind.ignored

def FindBuildRoot(dir):
    if os.path.isfile(os.path.join(dir, 'config.h')) and hash_utils.md5sum(os.path.join(dir, 'config.h')) == '9be4cb7407a148db2bec34f03ba83e6d' and \
       os.path.isfile(os.path.join(dir, 'stdafx.h')) and hash_utils.md5sum(os.path.join(dir, 'stdafx.h')) == '056492cf438c354554d18215b33519cb' and \
       os.path.isdir(os.path.join(dir, '3rdparty')):
        return dir
    else:
        new_dir = os.path.normpath(os.path.join(dir, '..',))
        if os.path.splitdrive(new_dir)[1] == os.path.sep:
            raise RuntimeError('Unable to find build root')
        else:
            return FindBuildRoot(new_dir)

def IsSameFile(src, dst):
    return os.path.basename(src).lower() == os.path.basename(dst).lower()

def IsSamePath(src, dst):
    return os.path.dirname(src).lower() == os.path.dirname(dst).lower()

def IsModifiedDateNewerOrSame(src, dst):
    return os.path.isfile(src) and os.path.isfile(dst) and os.stat(src)[stat.ST_MTIME] > os.stat(dst)[stat.ST_MTIME]

def CopySourceAndSymbols(srcFile, dstFile):
    shutil.copy2(srcFile, dstFile)
    pdbSrcFile = os.path.splitext(srcFile)[0] + '.pdb'
    pdbDstFile = os.path.splitext(dstFile)[0] + '.pdb'
    if os.path.isfile(pdbSrcFile):
        shutil.copy2(pdbSrcFile, pdbDstFile)

def main(args):
    if len(args) <= 1 or not os.path.isfile(args[1]):
        print('ERROR: Must specify the fully qualified path to the file which must be updated!')
        sys.exit(1)
    
    srcFile = os.path.normpath(args[1])
    try:
        rootDir = FindBuildRoot(os.path.dirname(srcFile))
    except RuntimeError:
        rootDir = FindBuildRoot(os.getcwd())

    client = pysvn.Client(rootDir)
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            dstFile = os.path.join(root, file)
            if IsSameFile(srcFile, dstFile) and not IsSamePath(srcFile, dstFile):
                if DoesExistInSvn(client, dstFile):
                    print(('Skipping %s because its part of source control!' % dstFile))
                elif not IsModifiedDateNewerOrSame(srcFile, dstFile):
                    srcFileModifcationDate = datetime.datetime.fromtimestamp(os.stat(srcFile)[stat.ST_MTIME]).strftime('%b %d, %Y  %I:%M:%S %p')
                    dstFileModifcationDate = datetime.datetime.fromtimestamp(os.stat(dstFile)[stat.ST_MTIME]).strftime('%b %d, %Y  %I:%M:%S %p')
                    print(('Not copying to %s because of modification dates\n\tSrc: %s\n\tDst: %s' % (dstFile, srcFileModifcationDate, dstFileModifcationDate)))
                else:
                    print(('Copying to %s' % root))
                    CopySourceAndSymbols(srcFile, dstFile)
    return 0

if __name__ == '__main__':
    sys.exit( main(sys.argv) )

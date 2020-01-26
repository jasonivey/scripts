import os, sys, shutil, codecs
import win32api, win32file

def IsReadOnly(path):
    return win32api.GetFileAttributes(path) & win32file.FILE_ATTRIBUTE_READONLY != 0
    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('ERROR: Please use \'FixDiffs file1 file2\'')
        
    filename1, filename2 = sys.argv[1], sys.argv[2]
    file1 = open(filename1, 'r')
    file2 = open(filename2, 'r')
    #file1 = codecs.open(filename1, 'r', 'utf-8')
    #file2 = codecs.open(filename2, 'r', 'utf-8')
    
    lines1 = file1.readlines();
    lines2 = file2.readlines();
    file1.close();
    file2.close()
    
    if len(lines1) != len(lines2):
        print('ERROR: The two files are not the same length.')
        
    for i in range(len(lines1)):
        line1, line2 = lines1[i], lines2[i]
        chksum1, chksum2 = line1[:line1.find(' ')], line2[:line2.find(' ')]

        if chksum1 != chksum2:
            src = 'd:' + line1[line2.find('*') + 1:].strip()
            dst = 'k:' + line2[line2.find('*') + 1:].strip()
            assert( src[1:] == dst[1:] )
            if os.path.isfile(dst) and IsReadOnly(dst):
                win32api.SetFileAttributes(dst, win32file.FILE_ATTRIBUTE_NORMAL)
            shutil.copyfile(src, dst)
            print(('Copied %s to K:\\music' % src))
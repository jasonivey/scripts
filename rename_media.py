import argparse
import os
import sys


def is_mp3_file(filename):
    return filename.lower().endswith('.mp3')

def _get_new_name(name, name_pattern, dest_dir, index, files_count):
    new_name = None
    name_index = name.rfind(' - ')
    if name_index != -1:
        new_name = name[name_index + len(' - ') : name.rfind('.')]
    file_pattern = '{0:0' + str(len(str(files_count))) + 'd} - '
    if new_name:
        file_pattern += '{0} - {1}.mp3'.format(name_pattern, new_name)
    else:
        file_pattern += name_pattern + '.mp3'
    return os.path.join(dest_dir, file_pattern.format(index))

def rename_files(files, dest_dir, name_pattern, execute):
    for i, filename in enumerate(files, 1):
        dir, oldname = os.path.split(filename)
        newpath = _get_new_name(oldname, name_pattern, dest_dir, i, len(files))
        index = len(os.path.dirname(dest_dir)) + 1
        print(('mv "{0}" "{1}"'.format(filename[index:], newpath[index:])))
        if execute:
            os.rename(filename, newpath)

def _directory_exists(dir):
    if not os.path.isdir(dir):
        msg = "{0} is not a valid directory".format(dir)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(dir))
    
def _parse_args():
    description = 'Rename mp3 files in a hierarchical order to a flat directory'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--source', metavar='<directory>', required=True, type=_directory_exists, help='source directory')
    parser.add_argument('-d', '--destination', metavar='<directory>', required=True, type=_directory_exists, help='destination directory')
    parser.add_argument('-f', '--filename', metavar='<new_file_name>', required=False, default=None, help='the name of all the renamed files')
    parser.add_argument('-e', '--execute', default=False, action='store_true', help='do not simulate the rename -- execute the operation')
    args = parser.parse_args()
    return os.path.normpath(os.path.abspath(args.source)), os.path.normpath(os.path.abspath(args.destination)), args.filename, args.execute
    
def main():
    src, dst, name_pattern, execute = _parse_args()
    #print('src: ', src, 'dst: ', dst, 'name_pattern: ', name_pattern, 'execute: ', execute)

    mp3_files = []
    for root, dirs, files in os.walk(src):
        for file in files:
            if is_mp3_file(os.path.join(root, file)):
                mp3_files.append(os.path.join(root, file))
    mp3_files.sort(key=str.lower)
    
    rename_files(mp3_files, dst, name_pattern, execute)
    return 0
    
if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from ansimarkup import AnsiMarkup, parse
#from app_settings import app_settings
import argparse
#import datetime
import os
from pathlib import Path
#import platform
#import pprint
#import psutil
#from psutil._common import bytes2human
#import random
#import re
#import shlex
#import subprocess
import sys
import tarfile
import traceback

user_tags = {
    'unknown_device'   : parse('<red>'),
    'regular_file'     : parse('<green>'),
    'directory'        : parse('<yellow>'),
    'symbolic_link'    : parse('<blue>'),
    'hard_link'        : parse('<magenta>'),
    'generic_device'   : parse('<cyan>'),
    'character_device' : parse('<bold><green>'),
    'block_device'     : parse('<bold><yellow>'),
    'fifo_device'      : parse('<bold><blue>'),

    'file_size'        : parse('<red>'),
    #'regular_file'   : parse('<green>'),
    #'directory'      : parse('<yellow>'),
    #'symbolic_link'  : parse('<blue>'),
    #'hard_link'      : parse('<magenta>'),
    #'generic_device' : parse('<cyan>'),
    #: parse('<white>'),
    #: parse('<bold><red>'),
    #'character_device' : parse('<bold><green>'),
    #'block_device'     : parse('<bold><yellow>'),
    #'fifo_device'      : parse('<bold><blue>'),
    #: parse('<bold><magenta>'),
    'file_details'     : parse('<bold><cyan>'),
    'filename'         : parse('<bold><white>'),
}

#random.seed()

am = AnsiMarkup(tags=user_tags)

def _is_valid_source(src):
    if src.find('*') != -1:
        index = src.rfind('/', 0, src.find('*'))
        root = Path(src[:index])
        pattern = src[index + 1:]
        if len([filename for filename in root.glob(pattern)]) == 0:
            msg = f'source parameter {src} does not specify a valid file/directory/file-pattern'
            raise argparse.ArgumentTypeError(msg)
        else:
            return Path(src).resolve()
    else:
        path = Path(src)
        if not path.is_file() and not path.is_dir():
            msg = f'source parameter {src} does not specify a valid file/directory/file-pattern'
            raise argparse.ArgumentTypeError(msg)
        else:
            return path.resolve(strict=True)

def _is_valid_create_dest(dst):
    path = Path(dst)
    if not path.parent.is_dir():
        msg = f'destination parameter {dst} resides in a directory which does not exist'
        raise argparse.ArgumentTypeError(msg)
    return path.resolve()

def _is_valid_tar_file(filename):
    file_path = Path(filename)
    if not file_path.is_file():
        msg = f'filename parameter {filename} does not exist'
        raise argparse.ArgumentTypeError(msg)
    return file_path.resolve(strict=True)

def _is_valid_extract_dest(dst):
    dest_path = Path(dst)
    if not dest_path.is_dir():
        msg = f'destination parameter {dst} is not a valid directory'
        raise argparse.ArgumentTypeError(msg)
    return dest_path.resolve(strict=True)

_COMPRESSION = ['none', 'gzip', 'bzip2', 'xz']
_COMPRESSION_EXTENSIONS = {'none': '.tar', 'gzip': '.tar.gz', 'bzip2': '.tar.bz2', 'xz': '.tar.xz'}
_COMPRESSION_WRITEMODES = {'none': 'x:', 'gzip': 'x:gz', 'bzip2': 'x:bz2', 'xz': 'x:xz'}

def _create_extension(path, compression):
    assert compression in _COMPRESSION, f'unknown compression type {compression}'
    path_no_extension = str(path).replace(''.join(path.suffixes), '', 1)
    compression_extension = _COMPRESSION_EXTENSIONS[compression]
    return Path(path_no_extension + compression_extension).resolve()

def _add_extension(path, compression):
    assert compression in _COMPRESSION, f'unknown compression type {compression}'
    suffixes = path.suffixes
    extension = ''.join(suffixes)
    if compression in _COMPRESSION and _COMPRESSION_EXTENSIONS[compression] == extension:
        return path
    else:
        return _create_extension(path, compression)

def _get_source_generator(path):
    if path.is_dir() or path.is_file():
        yield path
    else:
        assert str(path).find('*') != -1, f'source {path} file/directory/file-path does not specify a valid location'
        src = str(path)
        index = src.rfind('/', 0, src.find('*'))
        root = Path(src[:index])
        pattern = src[index + 1:]
        for name in root.glob(pattern):
            yield Path(name).resolve(strict=True)

def _clear_user_info(tarinfo):
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = 'root'
    return tarinfo

def _get_tarinfo_filetype(tarinfo):
    if tarinfo.isfifo():
        return am.ansistring('<fifo_device>FIFO</fifo_device>')
    elif tarinfo.isblk():
        return am.ansistring('<block_device>block device</block_device>')
    elif tarinfo.ischr():
        return am.ansistring('<character_device>character device</character_device>')
    elif tarinfo.isdev():
        return am.ansistring('<generic_device>one of character device, block device or FIFO</generic_device>')
    elif tarinfo.islnk():
        return am.ansistring('<hard_link>hard link</hard_link>')
    elif tarinfo.issym():
        return am.ansistring('<symbolic_link>symbolic link</symbolic_link>')
    elif tarinfo.isreg():
        return am.ansistring('<regular_file>regular file</regular_file>')
    elif tarinfo.isdir():
        return am.ansistring('<directory>directory</directory>')
    else:
        return am.ansistring(f'<unknown_device>unknown type {tarinfo.type} (ohh, spooky)<unknown_device>')

KIBI_BYTE = 1024 # KB
MEBI_BYTE = 1048576 # MB
GIBI_BYTE = 1073741824 # GB
TEBI_BYTE = 1099511627776 # TB
PEBI_BYTE = 1125899906842624 # PB
EXBI_BYTE = 1152921504606846976 # EB
ZEBI_BYTE = 1180591620717411303424 # ZB
YOBI_BYTE = 1208925819614629174706176 # YB
_BYTE_SIZES = {YOBI_BYTE : 'YB', ZEBI_BYTE : 'ZB', EXBI_BYTE : 'EB', PEBI_BYTE : 'PB', TEBI_BYTE : 'TB', GIBI_BYTE : 'GB', MEBI_BYTE : 'MB', KIBI_BYTE : 'KB'}

def _get_human_readable_size(input_size):
    for size, suffix in _BYTE_SIZES.items():
        if input_size > size:
            return am.ansistring(f'<file_size>{(input_size / size):.2f} {suffix}</file_size>')
    return am.ansistring(f'<file_size>{input_size} bytes</file_size>')

def _get_tarinfo_description(tarinfo):
    name = am.ansistring(f'<filename>{tarinfo.name}</filename>')
    is_s = am.ansistring('<file_details>is</file_details>')
    size = _get_human_readable_size(tarinfo.size)
    in_size_and_is_a = am.ansistring('<file_details>in size and is a</file_details>')
    file_type = _get_tarinfo_filetype(tarinfo)
    period = am.ansistring('<file_details>.</file_details>')
    return f'{name} {is_s} {size} {in_size_and_is_a} {file_type}{period}'

def create_tar(args):
    compression = args.compression
    assert compression in _COMPRESSION, f'unknown compression type {compression}'
    write_mode = _COMPRESSION_WRITEMODES[compression]
    dst_path = _add_extension(args.destination, compression)
    src_path = args.source
    with tarfile.open(dst_path, write_mode) as tar:
        for name in _get_source_generator(args.source):
            tar.add(name, filter=_clear_user_info)

def list_tar(args):
    with tarfile.open(args.filename, 'r:*') as tar:
        for tarinfo in tar:
            print(_get_tarinfo_description(tarinfo))

def extract_tar(args):
    with tarfile.open(args.filename, 'r:*') as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path=args.destination, numeric_owner="True")

def _parse_args():
    parser = argparse.ArgumentParser(description='Create, list and extract tape archive (tar) files')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    subparsers = parser.add_subparsers()
    parser_create = subparsers.add_parser('create')
    parser_create.add_argument('-s', '--source', required=True, type=_is_valid_source, help='the directory or file-pattern list to add to the tar file')
    parser_create.add_argument('-d', '--destination', required=True, type=_is_valid_create_dest, help='the directory or file-pattern list to add to the tar file')
    parser_create.add_argument('-c', '--compression', choices=_COMPRESSION, default='bzip2', help='the compression to use if any')
    parser_create.set_defaults(func=create_tar)
    parser_list = subparsers.add_parser('list')
    parser_list.add_argument('-f', '--filename', required=True, type=_is_valid_tar_file, help='the input tar file to have its contents listed')
    parser_list.set_defaults(func=list_tar)
    parser_extract = subparsers.add_parser('extract')
    parser_extract.add_argument('-f', '--filename', required=True, type=_is_valid_tar_file, help='the input tar file to have its contents extracted')
    parser_extract.add_argument('-d', '--destination', required=True, type=_is_valid_extract_dest, help='the directory or file-pattern list to add to the tar file')
    parser_extract.set_defaults(func=extract_tar)
    args = parser.parse_args()
    return args
    #app_settings.update(vars(args))
    #app_settings.print_settings(print_always=False)

def main():
    args = _parse_args()
    try:
        args.func(args)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

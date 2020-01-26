#!/usr/bin/env python

from datetime import datetime
import os
import sys
import argparse
import re
import string
import threading
import traceback
import time
import queue

import custom_utils
import hash_utils

def _internal_get_chksum(filename, crc_chk=False, md5_chk=True):
    assert (crc_chk or md5_chk) and not (crc_chk and md5_chk)
    if crc_chk:
        return hash_utils.crc32(filename)
    else:
        return hash_utils.md5sum(filename)

def _external_get_chksum(filename, crc_chk=False, md5_chk=False):
    assert (crc_chk or md5_chk) and not (crc_chk and md5_chk)
    if crc_chk:
        return hash_utils.crc32_shell(filename)
    else:
        return hash_utils.md5sum_shell(filename)

def _dump_file_in_proc(dirname, filename, show_last_modified, crc_chk, md5_chk):
    fullpath = os.path.join(dirname, filename)
    output = ''
    if show_last_modified:
        output += '{0:%m/%d/%Y %I:%M:%S %p} '.format(datetime.fromtimestamp(os.path.getmtime(fullpath)))
    if crc_chk or md5_chk:
        output += _internal_get_chksum(fullpath, crc_chk, md5_chk) + ' *'
    return output + filename

def _dump_file_out_of_proc(dirname, filename, show_last_modified, crc_chk, md5_chk):
    fullpath = os.path.join(dirname, filename)
    output = ''
    if show_last_modified:
        output += '{0:%m/%d/%Y %I:%M:%S %p} '.format(datetime.fromtimestamp(os.path.getmtime(fullpath)))
    if crc_chk or md5_chk:
        output += _external_get_chksum(fullpath, crc_chk, md5_chk) + ' *'
    return output + filename
    
#class FileDumperThread(threading.Thread):
#    def __init__(self, files, output_queue, chksum):
#        threading.Thread.__init__(self)
#        self.files = files
#        self.output_queue = output_queue
#        self.chksum = chksum
#
#    def run(self):
#        while True:
#            filename = self.files.get()
#            self.output_queue.put(self._dump_file(filename))
#            self.files.task_done()
#
#    def _dump_file(self, filename):
#        filepath = os.path.splitdrive(filename)[1]
#        if self.chksum:
#            output = '{0} *{1}'.format(hash_utils.md5sum(filename), filepath)
#        else:
#            output = filepath
#        return output

class FileDumperThread(threading.Thread):
    def __init__(self, dir, files, output, timestamp, quick, do_chksum):
        threading.Thread.__init__(self)
        self.dir_length = len(os.path.splitdrive(dir)[1]) + 1
        self.files = files
        self.output = output
        self.timestamp = timestamp
        self.quick = quick
        self.do_chksum = do_chksum
        self.file_lock = threading.Lock()
        self.output_lock = threading.Lock()

    def run(self):
        while True:
            with self.file_lock:
                if len(self.files) == 0:
                    return
                else:
                    filename = self.files.pop()
            with self.output_lock:
                self.output[filename] = self._dump_file(filename)

    def _dump_file(self, filename):
        filepath = os.path.splitdrive(filename)[1][self.dir_length:]
        output = ''
        if self.timestamp:
            output += '{0:%m/%d/%Y %I:%M:%S %p} '.format(datetime.fromtimestamp(os.path.getmtime(filename)))
        if self.do_chksum:
            if self.quick:
                output += hash_utils.crc32(filename) + ' *'
            else:
                output += hash_utils.md5sum(filename) + ' *'
        return output + filepath

def _directory_exists(dir):
    if not os.path.isdir(dir):
        msg = "{0} is not a valid directory".format(dir)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(dir))

def _parse_command_line():
    parser = argparse.ArgumentParser(description='Enumerates all files in a directory (with MD5\'s).')
    parser.add_argument('-n', '--norecurse', dest='norecurse', action='store_true', help='turns off directory recursion')
    parser.add_argument('-c', '--chksum', dest='chksum', action='store_true', help='enables md5 chksum')
    parser.add_argument('-s', '--no-timestamp', dest='no_timestamp', action='store_true', help='disable timestamp output')
    parser.add_argument('-q', '--quick', dest='quick', action='store_true', help='use crc32 instead of md5sum')
    parser.add_argument('-t', '--thread', dest='thread_count', required=False, type=int, default=1, help='thread count for chksum')
    parser.add_argument('-d', '--directory', dest='directory', required=False, type=_directory_exists, help='destination directory')
    parser.add_argument('output_file', type=argparse.FileType('w'), metavar='<output file>', help='file to output results')
    args = parser.parse_args()

    norecurse = args.norecurse
    do_chksum = args.chksum
    timestamp = not args.no_timestamp
    thread_count = args.thread_count if args.thread_count > 0 else 1
    output_file = args.output_file
    directory = os.path.abspath(args.directory) if args.directory else os.getcwd()
    return norecurse, do_chksum, timestamp, args.quick, thread_count, output_file, directory

def is_not_system_file(filename):
    return not filename.lower().endswith('.ds_store')

def dump_dir(directory, output_file, recurse=True, crc32=False, md5=False, timestamp=False, verbose=False):
    for fullname in custom_utils.get_files_in_directory(directory, predicate=is_not_system_file, sort=True, recurse=recurse):
        dirname = fullname[:len(directory)]
        filename = fullname[len(dirname) + 1:]
        output = _dump_file_out_of_proc(dirname, filename, timestamp, crc32, md5)
        if verbose:
            print(output)
        print(output, file=output_file)

def main():
    norecurse, do_chksum, timestamp, quick, thread_count, output_file, directory = _parse_command_line()

    try:
        start = time.time()
        crc_chk = do_chksum and quick
        md5_chk = do_chksum and not quick
        dump_dir(directory, output_file, recurse=not norecurse, md5=md5_chk, crc32=crc_chk, timestamp=timestamp, verbose=True)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    finally:
        print("Elapsed Time: {0}".format(time.time() - start))
        return 0

def main1():
    start = time.time()
    norecurse, do_chksum, timestamp, quick, thread_count, output_file, directory = parse_command_line()

    files = custom_utils.get_files_in_directory(directory, predicate=is_not_system_file, sort=True, recurse=not norecurse)
    #files.sort(key=str.lower)

    #file_queue = Queue.Queue()
    #for file in files:
    #    file_queue.put(file)

    #output_queue = Queue.Queue()
    threads = []
    output = {}
    for i in range(thread_count):
        thread = FileDumperThread(directory, files, output, timestamp, quick, do_chksum)
        thread.setDaemon(True)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    #file_queue.join()
    
    filenames = list(output.keys())
    filenames.sort(key=str.lower)
    for filename in filenames:
        print(output[filename])
        print(output[filename], file=output_file)
    #assert len(files) == output_queue.qsize()
    #for i in range(len(files)):
    #    file_str = file_str_queue.get_nowait()
    #    print(file_str)
    #    print(file_str, file=output_file)

    print("Elapsed Time: {0}".format(time.time() - start))
    return 0

if __name__ == '__main__':
    sys.exit(main())

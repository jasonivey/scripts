#!/usr/bin/env python
from __future__ import print_function
import datetime
import os
import sys
import argparse
import re
import collections
import traceback

# Represents the entire four files: 5E9D4B9AA75D42718C5B15E73A5992ED_00000000DF.ts
#                                   5E9D4B9AA75D42718C5B15E73A5992ED_01000000DF.ts
#                                   5E9D4B9AA75D42718C5B15E73A5992ED_02000000DF.ts
#                                   5E9D4B9AA75D42718C5B15E73A5992ED_03000000DF.ts
class TsFileSet:
    def __init__(self, filename, stream_uuid, number):
        self.name = filename
        self.stream_uuid = stream_uuid
        self.number = number
        self.timestamp = {}

    def add_profile(self, profile, timestamp):
        assert not self.timestamp.has_key(profile)
        self.timestamp[profile] = timestamp

    def _calc_drift(self):
        if len(self.timestamp.keys()) <= 1:
            return 0
        diffs = [0]
        for index, timestamp in enumerate(self.timestamp.itervalues()):
            for other_index, other_timestamp in enumerate(self.timestamp.itervalues()):
                if index == other_index or timestamp == other_timestamp:
                    continue
                diff = timestamp - other_timestamp if timestamp >= other_timestamp else other_timestamp - timestamp
                diffs.append(diff.total_seconds())
        return max(diffs)
    
    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __str__(self):
        str = '{0} - max drift {1} seconds'.format(self.name, self._calc_drift())
        return str
    

class TsFiles:
    _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    def __init__(self, drift_sort, filename_sort):
        self.files = {}
        self.drift_sort = drift_sort
        self.filename_sort = filename_sort

    def _parse_filename(self, filename):
        if filename.rfind('/') != -1:
            filename = filename[filename.rfind('/') + 1:]
        if filename.find('_') == -1:
            return None, None, None, None
        stream_uuid = filename[:filename.find('_')]
        profile_and_ts_number_str = filename[filename.find('_') + 1:filename.find('.')]
        profile_and_ts_number = int(profile_and_ts_number_str, 16)
        ts_number = 0xFFFFFFFF & profile_and_ts_number
        profile = (0xFF00000000 & profile_and_ts_number) >> 32
        return filename, stream_uuid, ts_number, profile

    def _parse_date(self, parts):
        _months = {'Jan' : 1, 'Feb' : 2, 'Mar' : 3, 'Apr' : 4, 'May' : 5, 'Jun' : 6, 'Jul' : 7, 'Aug' : 8, 'Sep' : 9, 'Oct' : 10, 'Nov' : 11, 'Dec' : 12}
        assert len(parts) == 11
        year = int(parts[-2])
        day = int(parts[-4])
        if parts[-5] not in _months:
            return None
        month = _months[parts[-5]]
        time_parts = parts[-3].split(':')
        if len(time_parts) != 3:
            return None
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])
        return datetime.datetime(year, month, day, hour, minute, second)

    def _parse_entry(self, entry):
        parts = entry.split()
        if len(parts) != 11:
            return None, None, None, None, None
        filename, stream_uuid, ts_number, profile = self._parse_filename(parts[-1])
        if not filename:
            return None, None, None, None, None
        timestamp = self._parse_date(parts)
        if not timestamp:
            return None, None, None, None, None
        size = int(parts[4])
        if size == 0:
            print('Found zero length file {0}'.format(filename))
        return filename, stream_uuid, ts_number, profile, timestamp

    def parse_input_file(self, input_file):
        for line in input_file.readlines():
            filename, stream_uuid, ts_number, profile, timestamp = self._parse_entry(line)
            if not filename:
                continue
            unique_name = '{0}_{1:08X}.ts'.format(stream_uuid, ts_number)
            if not self.files.has_key(unique_name):
                self.files[unique_name] = TsFileSet(unique_name, stream_uuid, ts_number)
            self.files[unique_name].add_profile(profile, timestamp)

    def analyze(self):
        files = self.files.values()
        if self.filename_sort:
            files.sort()
        elif self.drift_sort:
            files.sort(key=TsFileSet._calc_drift)
        for f in files:
            print(str(f))

def _parse_command_line():
    parser = argparse.ArgumentParser(description='Parses the output from running a recursive ls command')
    parser.add_argument('-d', '--drift-sort', dest='driftsort', action='store_true', help='sort the results by maximum drift')
    parser.add_argument('-f', '--file-sort', dest='filenamesort', action='store_true', help='sort the results by file name')
    parser.add_argument('input_file', type=argparse.FileType('r'), metavar='<input file>', help='file containing <ls> results')
    args = parser.parse_args()

    assert not args.driftsort or not args.filenamesort, 'cannot set both drift-sort and filename-sort'

    return args.input_file, args.driftsort, args.filenamesort;

def main():
    input_file, drift_sort, filename_sort = _parse_command_line()

    try:
        ts_files = TsFiles(drift_sort, filename_sort)
        ts_files.parse_input_file(input_file)
        ts_files.analyze()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    finally:
        return 0

if __name__ == '__main__':
    sys.exit(main())


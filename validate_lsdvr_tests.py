from __future__ import print_function
import argparse
import datetime
from contextlib import closing
import gzip
import json
import os
import sys
import socket
import traceback
import urllib2

import lsdvr_http_api

_VERBOSE_OUTPUT = False

_DATE_TIME_CONVERSION_FMT = '%Y-%m-%d %H:%M:%S'

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _from_time_t(value):
    return datetime.datetime.fromtimestamp(value)

def _to_datetime(value):
    return datetime.datetime.strptime(value, _DATE_TIME_CONVERSION_FMT)

def _from_datetime(value):
    fmt_str = '{0:' + _DATE_TIME_CONVERSION_FMT + '}'
    return fmt_str.format(value)

def _is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return ip
    except:
        msg = "{0} is not a valid ip address".format(ip)
        raise argparse.ArgumentTypeError(msg)

def _directory_exists(dir):
    if not os.path.isdir(dir):
        msg = "{0} is not a valid directory".format(dir)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(dir))

def _parse_args():
    description = 'Validate tests run on the LSDVR. It will retrieve asset information for all assets and store them'
    description += ' locally to be used when the script is run again. If neither \'--find-xxxx\' switch is specified'
    description += ' the asset information will be retrieved and then saved to the local directory.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--ipaddr', metavar='<ip address>', required=True, nargs='+', type=_is_valid_ip, help='ip address of LSDVR')
    parser.add_argument('-d', '--directory', required=False, type=_directory_exists, help='local directory where data resides')
    #parser.add_argument('-t', '--type', required=True, choices=['chop', 'rolling_chop', 'stream'], help='the type of test to validate')
    parser.add_argument('-e', '--find-empty', default=False, action='store_true', help='find empty streams (i.e. recordings which didn\'t start')
    parser.add_argument('-b', '--find-glitch', default=False, action='store_true', help='find glitch streams (i.e. recordings which didn\'t start/stop on time')
    parser.add_argument('-f', '--force', default=False, action='store_true', help='force the script to re-fetch data from source test machine')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='output verbose debugging information')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = args.verbose
    return args.ipaddr, args.directory, args.find_empty, args.find_glitch, args.force

class RecordingsSerializer(object):
    def __init__(self, directory, ip_addr, force):
        self._filename = os.path.join(directory, '{0}.json.gz'.format(ip_addr))
        self._force = force
        self._flush = False
        self._recordings = []
        self._deserialize()
        if len(self._recordings) == 0:
            self._recordings = _get_recordings(ip_addr)
            self._flush = True
        self._recordings = sorted(self._recordings, cmp=Recording.sort_compare)

    def _deserialize(self):
        if not os.path.isfile(self._filename):
            return
        with gzip.open(self._filename, 'rb') as restore_file:
            if _is_verbose_output_enabled():
                print('reading backup data from {0}'.format(self._filename))
            restore_data = restore_file.read()
            restore_objs = json.loads(restore_data)
            for restore_obj in restore_objs:
                self.recordings.append(Recording.deserialize(restore_obj))

    def _serialize(self):
        backup_data = []
        for recording in self.recordings:
            backup_data.append(recording.serialize())
        with gzip.open(self._filename, 'wb') as backup_file:
            if _is_verbose_output_enabled():
                print('writing backup data to {0}'.format(self._filename))
            backup_file.write(json.dumps(backup_data))

    def serialize(self):
        if self._flush:
            self._serialize()

    @classmethod
    def deserialize(cls, directory, filename, force):
        return cls(directory, filename, force)

    @property
    def recordings(self):
        return self._recordings

class StreamFile(object):
    def __init__(self, name, stream, number, profile, partition):
        self._name = name
        self._stream = stream
        self._number = number
        self._profile = profile
        self._partition = partition

    def serialize(self):
        obj = {}
        obj['name'] = self._name
        obj['stream'] = self._stream
        obj['number'] = self._number
        obj['profile'] = self._profile
        obj['partition'] = self._partition
        return obj

    @classmethod
    def deserialize(cls, obj):
        return cls(obj['name'], obj['stream'], obj['number'], obj['profile'], obj['partition'])

    @property
    def name(self):
        return name

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __str__(self):
        return self.name

class Stream(object):
    def __init__(self, stream_id, start, stop):
        self._stream_id = stream_id
        self._start_time = start
        self._stop_time = stop
        self._stream_files = []

    def serialize(self):
        obj = {}
        obj['stream_id'] = self._stream_id
        obj['start_time'] = _from_datetime(self._start_time)
        obj['stop_time'] = _from_datetime(self._stop_time)
        obj['stream_files'] = []
        for s_file in self._stream_files:
            obj['stream_files'].append(s_file.serialize())
        return obj

    @classmethod
    def deserialize(cls, obj):
        c = cls(obj['stream_id'], _to_datetime(obj['start_time']), _to_datetime(obj['stop_time']))
        for obj_stream_file in obj['stream_files']:
            c.stream_files.append(StreamFile.deserialize(obj_stream_file))
        return c

    @property
    def stream_id(self):
        return self._stream_id

    @property
    def start_time(self):
        return self._start_time

    #@start_time.setter
    #def start_time(self, value):
    #    self._start_time = value

    @property
    def stop_time(self):
        return self._stop_time

    #@stop_time.setter
    #def stop_time(self, value):
    #    self._stop_time = value

    @property
    def stream_files(self):
        return self._stream_files

    @stream_files.setter
    def stream_files(self, value):
        self._stream_files = value

    def __cmp__(self, other):
        return cmp(self.stream_id, other.stream_id)

    def __str__(self):
        return '{0}'.format(self._stream_id)

class Recording(object):
    def __init__(self, asset_id, channel_guid, callsign, channel_rf, major, minor, start, stop):
        self._asset_id = asset_id
        self._channel_guid = channel_guid
        self._callsign = callsign
        self._channel_rf = channel_rf
        self._channel_major = major
        self._channel_minor = minor
        self._start_time = start
        self._stop_time = stop
        self._streams = []

    def serialize(self):
        obj = {}
        obj['asset_id'] = self._asset_id
        obj['channel_guid'] = self._channel_guid
        obj['callsign'] = self._callsign
        obj['channel_rf'] = self._channel_rf
        obj['channel_major'] = self._channel_major
        obj['channel_minor'] = self._channel_minor
        obj['start_time'] = _from_datetime(self._start_time)
        obj['stop_time'] = _from_datetime(self._stop_time)
        obj['streams'] = []
        for s in self._streams:
            obj['streams'].append(s.serialize())
        return obj

    @classmethod
    def deserialize(cls, obj):
        c = cls(obj['asset_id'],
                obj['channel_guid'],
                obj['callsign'],
                obj['channel_rf'],
                obj['channel_major'],
                obj['channel_minor'],
                _to_datetime(obj['start_time']),
                _to_datetime(obj['stop_time']))
        for obj_stream in obj['streams']:
            c.streams.append(Stream.deserialize(obj_stream))
        return c

    @property
    def asset_id(self):
        return self._asset_id

    @property
    def start(self):
        return self._start_time

    @property
    def stop(self):
        return self._stop_time

    @property
    def streams(self):
        return self._streams

    def sort_compare(self, other):
        if self._start_time != other._start_time:
            return cmp(self._start_time, other._start_time)
        if self._channel_rf != other._channel_rf:
            return cmp(self._channel_rf, other._channel_rf)
        if self._channel_major != other._channel_major:
            return cmp(self._channel_major, other._channel_major)
        if self._channel_minor != other._channel_minor:
            return cmp(self._channel_major, other._channel_major)
        return 0

    def compare_key(self):
        return self._start_time

    def __cmp__(self, other):
        return cmp(self.asset_id, other.asset_id)

    def __str__(self):
        str = ''
        str += '{0}\n'.format(self._asset_id)
        str += '{0}\n'.format(self._channel_guid)
        str += '{0}\n'.format(self._callsign)
        str += '{0}\n'.format(self._channel_rf)
        str += '{0}\n'.format(self._channel_major)
        str += '{0}\n'.format(self._channel_minor)
        str += '{0}\n'.format(_from_datetime(self._start_time))
        str += '{0}\n'.format(_from_datetime(self._stop_time))
        for stream in self.streams:
            str += '  {0}\n'.format(stream)
        return str

MAX_CHUNK_SIZE = 50

def _create_get_clips_list_params_chunk(asset_ids):
    params = []
    begin = 0
    while begin != len(asset_ids):
        end = begin + min(MAX_CHUNK_SIZE, len(asset_ids[begin:]))
        params_dict = {}
        params_dict['message_type'] = 'get_clips_list'
        params_dict['assets'] = asset_ids[begin:end]
        begin = end
        params.append(json.dumps(params_dict))
    #if _is_verbose_output_enabled():
    #    print(params)
    return params

def _print_timing_info(elapsed):
    #start_time = datetime.datetime.now()
    #end_time = datetime.datetime.now()
    #_print_timing_info(end_time - start_time)
    total_hours = int(elapsed.seconds / 3600)
    total_minutes = int((elapsed.seconds % 3600) / 60)
    total_seconds = int((elapsed.seconds % 3600) % 60)
    op_hours = int((elapsed.seconds / MAX_CHUNK_SIZE ) / 3600)
    op_minutes = int(((elapsed.seconds / MAX_CHUNK_SIZE ) % 3600) / 60)
    op_seconds = int(((elapsed.seconds / MAX_CHUNK_SIZE ) % 3600) % 60)
    print('Timing for request:    {0:02d}:{1:02d}:{2:02d}:{3:03d}'.format(total_hours, total_minutes, total_seconds, elapsed.microseconds / 1000))
    print('Timing for recording:  {0:02d}:{1:02d}:{2:02d}:{3:03d}'.format(op_hours, op_minutes, op_seconds, elapsed.microseconds / MAX_CHUNK_SIZE / 1000))

def _parse_stream_range_start(range_str):
    i = range_str.find(',')
    return int(float(range_str[:i])) if i != -1 else 0

def _parse_stream_range_stop(range_str):
    i = range_str.find(',')
    return int(float(range_str[i + 1:])) if i != -1 and i + 1 < len(range_str) else 0

def _get_stream_files(ip_addr, stream_id):
    stream_files = []
    partitions = lsdvr_http_api.get_stream_partitions(ip_addr, stream_id, _is_verbose_output_enabled())
    for partition in partitions:
        details = lsdvr_http_api.get_stream_files(ip_addr, stream_id, partition, _is_verbose_output_enabled())
        for name, number, profile in details:
            stream_file = StreamFile(name, stream_id, number, profile, int(partition, 16))
            stream_files.append(stream_file)
    return stream_files

def _parse_asset_json(values):
    if not values.has_key('assets'): return []
    recordings = []
    for asset in values['assets']:
        recording = Recording(asset['asset_id'],
                              asset['channel_guid'],
                              asset['callsign'],
                              asset['channel_rf'],
                              asset['channel_major'],
                              asset['channel_minor'],
                              _from_time_t(asset['start_time']),
                              _from_time_t(asset['stop_time']))
        if asset.has_key('clips'):
            for clip in asset['clips']:
                if clip['type'] == 'content':
                    start = asset['start_time'] + _parse_stream_range_start(clip['range']);
                    stop = asset['start_time'] + _parse_stream_range_stop(clip['range']);
                    stream = Stream(clip['stream_id'], _from_time_t(start), _from_time_t(stop))
                    recording.streams.append(stream)
        recordings.append(recording)
    return recordings

def _get_recordings_chunk(ip_addr, params):
    url = 'http://{0}/api/'.format(ip_addr)
    with closing(urllib2.urlopen(url, data=params)) as site:
        values = json.loads(site.read())
        return _parse_asset_json(values)

def _get_asset_ids(ip_addr):
    url = 'http://{0}/api/'.format(ip_addr)
    params = '{"message_type": "get_asset_ids"}'
    assets = []
    with closing(urllib2.urlopen(url, data=params)) as site:
        values = json.loads(site.read())
        if values.has_key('assets'):
            for asset in values['assets']:
                assets.append(str(asset))
    if _is_verbose_output_enabled():
        print('Total assets retrieved: {0}'.format(len(assets)))
    return assets

def _get_recordings(ip_addr):
    recordings = []
    try:
        asset_ids = _get_asset_ids(ip_addr)
        clips_list_params_chunks = _create_get_clips_list_params_chunk(asset_ids)
        for clips_list_params_chunk in clips_list_params_chunks:
            recordings += _get_recordings_chunk(ip_addr, clips_list_params_chunk)
        for recording in recordings:
            for stream in recording.streams:
                stream.stream_files = _get_stream_files(ip_addr, stream.stream_id)
    except urllib2.HTTPError, err:
        print('EXCEPTION: while getting recordings for {0}. {1}'.format(ip_addr, err))
    return recordings

def _validate_recording(ip_addr, recording):
    SECONDS_PER_FILE = 2
    TOTAL_PROFILE_COUNT = 4

    if recording.start == recording.stop:
        return

    if len(recording.streams) > 1:
        print('ERROR: recording {0} has more than one stream ({1})'.format(recording.asset_id, len(recording.streams)))
        return

    if len(recording.streams) == 0:
        return
    
    stream = recording.streams[0]
    stream_id = stream.stream_id
    stream_file_count = len(stream.stream_files)
    if stream_file_count == 0:
        print('ERROR: recording {0} does not have any files'.format(recording.asset_id))

    recording_duration = recording.stop - recording.start
    if _is_verbose_output_enabled():
        print('recording {0} duration is {1}'.format(recording.asset_id, recording_duration))

    calculated_file_count = (recording_duration.total_seconds() / SECONDS_PER_FILE) * TOTAL_PROFILE_COUNT
    buffer_file_count = ((60 * 2) / SECONDS_PER_FILE) * TOTAL_PROFILE_COUNT
    if _is_verbose_output_enabled():
        print('recording {0} file count is {1}'.format(recording.asset_id, calculated_file_count))

    if _is_verbose_output_enabled():
        print('recording {0} actual file count is {1}'.format(recording.asset_id, stream_file_count))

    calc_start_time = recording.start
    calc_stop_time = recording.start + datetime.timedelta(seconds=(stream_file_count / TOTAL_PROFILE_COUNT) * SECONDS_PER_FILE)
    calc_stream_file_duration = calc_stop_time - calc_start_time

    if stream_file_count < calculated_file_count:
        #print('ERROR: recording {0} has stream {1} which contains {2} files when there should be at least {3} files'.
        #      format(recording.asset_id, stream_id, stream_file_count, calculated_file_count))
        print('TRUNCATED RECORDING ERROR: recording {0} has stream {1} which recorded for {2} when it should have recorded for {3}'.
              format(recording.asset_id, stream_id, calc_stream_file_duration, recording_duration))

    # we start the recording a minute early and end a minute late (buffer_file_count == 2 minutes)
    if stream_file_count > calculated_file_count + buffer_file_count:
        #print('ERROR: recording {0} has stream {1} which contains {2} files when there should be no more than {3} files'.
        #      format(recording.asset_id, stream_id, stream_file_count, calculated_file_count))
        print('RECORDING STOP ERROR: recording {0} has stream {1} which recorded for {2} when it should have recorded for {3}'.
              format(recording.asset_id, stream_id, calc_stream_file_duration, recording_duration))

def _validate_recorsings_gitch(ip_addr, recordings):
    [_validate_recording(ip_addr, recording) for recording in recordings if len(recording.streams) != 0]
    
def _validate_recordings_started(recordings):
    empty_stream_recordings = [recording for recording in recordings if len(recording.streams) == 0]
    if len(empty_stream_recordings) != 0:
        print('Recordings which did not start:')
    for recording in empty_stream_recordings:
        print('  {0} starting {1} and ending {2}'.
              format(recording.asset_id, _from_datetime(recording.start), _from_datetime(recording.stop)))

def validate_test_machine(recordings, ip_addr, find_empty, find_glitch):
    if _is_verbose_output_enabled():
        [print('{0}'.format(recording)) for recording in recordings]
    if find_glitch:
        _validate_recorsings_gitch(ip_addr, recordings)
    if find_empty:
        _validate_recordings_started(recordings)

def main():
    ip_addrs, directory, find_empty, find_glitch, force = _parse_args()
    print('ip address: {0}, directory: {1}, find empty: {2}, find glitch: {3} force: {4}'.
          format(ip_addrs, directory, find_empty, find_glitch, force))

    try:
        for ip_addr in ip_addrs:
            print('\nValidation for {0}'.format(ip_addr))
            serializer = RecordingsSerializer.deserialize(directory, ip_addr, force)
            validate_test_machine(serializer.recordings, ip_addr, find_empty, find_glitch)
            serializer.serialize()
        print()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

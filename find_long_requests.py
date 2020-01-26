#!/usr/bin/env python

from datetime import datetime
from datetime import timedelta
import exceptions
import glob
import os
import re
import sys
import traceback
import uuid

BEGIN_REGEX = r'\n(?P<datetime>[^\s]*\s[^\s]*)\s\[[^\]]*\]\s(?P<thread_id>\d*)\s\[DEBUG\]\srequesting url http.*(?P<key_id>[a-fA-F0-9]{32})\n'
END_REGEX = r'\n(?P<datetime>[^\s]*\s[^\s]*)\s\[[^\]]*\]\s%s\s\[DEBUG\]\sreturning key info for key\s%s\n'

def _find_long_requests(data):
    requests = []
    index = 0
    while True:
        #print('index: %d' % index)
        begin_match = re.search(BEGIN_REGEX, data[index:])
        if not begin_match:
            break
        index += begin_match.end()
        #print('index: %d' % index)
        end_match = re.search(END_REGEX % (begin_match.group('thread_id'), uuid.UUID(begin_match.group('key_id'))), data[index:])
        if not end_match:
            raise exceptions.RuntimeError('unable to find ending key info request to match beginning request')
        index += end_match.end()
        start = datetime.strptime(begin_match.group('datetime'), '%Y-%m-%d %H:%M:%S,%f')
        end = datetime.strptime(end_match.group('datetime'), '%Y-%m-%d %H:%M:%S,%f')
        if end - start > timedelta(seconds=1):
            requests.append('Key-Id %s took %s in thread %s to return' % (begin_match.group('key_id'), (end - start), begin_match.group('thread_id')))
    return requests

def _get_log_files():
    if not os.path.isdir('/var/log/key-providers'):
        raise exceptions.RuntimeError('/var/log/key-providers directory does not exist')
    return glob.glob('/var/log/key-providers/key-providers.log*')

def main():
    try:
        for filename in _get_log_files():
            #print('%s:' % filename)
            with open(filename, 'r') as logfile:
                requests = _find_long_requests(logfile.read())
                if len(requests) > 0:
                    print('%s:' % filename)
                    for request in requests:
                        print('  %s' % request)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

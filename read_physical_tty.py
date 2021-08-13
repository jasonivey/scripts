#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from pathlib import Path
import os
import re
import sys
import pprint
import psutil
import datetime
import time
import traceback
import fileinput

#from ansimarkup import AnsiMarkup, parse
'''
user_tags = {
    'info': parse('<bold><green>'),
    'error': parse('<bold><red>'),
    'text': parse('<bold><white>'),
    'output': parse('<bold><cyan>'),
    'arg': parse('<bold><yellow>'),}
'''
#am = AnsiMarkup(tags=user_tags)

_SIGNATURE = [0x30, 0xAA, 0x00]
_SIGNATURE_SIZE = 3
_VERBOSE = True

def _print_info(msg):
    if _VERBOSE:
        #am.ansiprint(f'<info>INFO:</info> <text>{msg}</text>')
        print(f'INFO: {msg}')


def _print_error(msg):
    #am.ansiprint(f'<error>ERROR:</error> <text>{msg}</text>')
    print(f'ERROR: {msg}')


def _get_signature(data):
    sig = []
    for i in data[:_SIGNATURE_SIZE]:
        sig.append(int(i))
    return sig


def _has_tty_signature(data):
    print(f'signature validation')
    print(f'expected signature: {pprint.pformat(_SIGNATURE)}')
    print(f'data size:          {len(data)}')
    if len(data) < _SIGNATURE_SIZE:
        _print_error('data is {len(data)} bytes and should be at least {_SIGNATURE_SIZE} bytes')
        return False
    signature = _get_signature(data)
    print(f'data:               {pprint.pformat(signature)}')
    return signature[0] == _SIGNATURE[0] and signature[1] == _SIGNATURE[1] and signature[2] == _SIGNATURE[2]


def _get_adjusted_time_stamp(adjustment):
    return datetime.datetime.fromtimestamp(psutil.boot_time() + adjustment);


def timestamp_replacement(match_obj):
    timestamp_match = match_obj.group(0)[1:-1]
    print('replacing {timestamp_match}')
    timestamp = _get_adjusted_time_stamp(float(timestamp_match))
    return f'[{timestamp}]'


def _convert_bytes_to_string(data):
    text = ''
    for b in data:
        ch = chr(b)
        if ch.isprintable():
            text += ch
    new_text = re.sub(r'\s{4,}', '\n', text)
    return re.sub(r'\[\s*\d+\.\d+\]', timestamp_replacement, new_text)


def read_physical_tty(name='/dev/vcsa'):
    with fileinput.input(mode='rb') as input_data:
        for data in input_data:
            if input_data.isfirstline():
                if _has_tty_signature(data):
                    data = data[4:]
                else:
                    _print_error(f'signature not found at the beginning of the buffer')
                    return
            text = _convert_bytes_to_string(data)
            print(text)


def main():
    try:
        read_physical_tty()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

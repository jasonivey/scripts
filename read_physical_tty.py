#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from pathlib import Path
import os
import sys
import pprint
import traceback
#from ansimarkup import AnsiMarkup, parse
'''
user_tags = {
    'info': parse('<bold><green>'),
    'error': parse('<bold><red>'),
    'text': parse('<bold><white>'),
    'output': parse('<bold><cyan>'),
    'arg': parse('<bold><yellow>'),}
'''

_SIGNATURE = [0x30, 0xAA, 0x00, 0x05]
_VERBOSE = True
#am = AnsiMarkup(tags=user_tags)


def _print_info(msg):
    if _VERBOSE:
        #am.ansiprint(f'<info>INFO:</info> <text>{msg}</text>')
        print(f'INFO: {msg}')


def _print_error(msg):
    #am.ansiprint(f'<error>ERROR:</error> <text>{msg}</text>')
    print(f'ERROR: {msg}')


def _get_signature(data):
    sig = []
    for i in data[:len(_SIGNATURE)]:
        sig.append(int(i))
    return sig


def _has_tty_signature(data):
    #print(f'data len:  {len(data)}')
    #print(f'signature: {pprint.pformat(_SIGNATURE)}')
    if len(data) < 4: return False
    signature = _get_signature(data)
    #print(f'data:      {pprint.pformat(signature)}')
    return signature == _SIGNATURE


def _convert_bytes_to_string(data):
    data_str = ''
    for b in data:
        ch = chr(b)
        if ch.isprintable():
            data_str += ch
    return data_str


def _add_newlines(data_str):
    i = 0
    substr = ''
    lines = []
    while i < len(data_str):
        if data_str[i].isprintable() and not data_str[i].isspace():
            substr += data_str[i]
            #print(f'adding {data_str[i]} character to {substr}')
            i += 1
        elif len(substr) > 0 and i + 3 <= len(data_str) and data_str[i : i + 3].isspace():
            #print(f'adding {substr} to the list of {len(lines)} string(data_str)')
            lines.append(substr)
            substr = ''
            i += 3
        elif len(substr) > 0 and data_str[i].isspace():
            #print(f'adding a whitespace character to {substr}')
            substr += data_str[i]
            i += 1
        else:
            #print(f'not doing anything except incrementing i from {i} to {i + 1}')
            i += 1
    return '\n'.join(lines)


def read_physical_tty(name='/dev/vcsa'):
    tty_path = Path(name).resolve()
    if not tty_path.exists():
        _print_error(f'file {tty_path} does not exist')
        return
    elif not tty_path.is_char_device():
        _print_error(f'file {tty_path} is not a character device')
        return
    data = tty_path.read_bytes()
    if not _has_tty_signature(data):
        _print_error(f'the first 4 bytes of {tty_path} is not {pprint.pformat(_SIGNATURE)}')
        return
    data_str = _convert_bytes_to_string(data[len(_SIGNATURE):])
    return _add_newlines(data_str)


def main():
    #_parse_args()
    try:
        print(read_physical_tty())
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

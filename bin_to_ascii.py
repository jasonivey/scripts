#!/usr/bin/python

import argparse
import base64
import binascii
import os
import sys
import traceback

def is_printable(s):
    return ord(s) >= 0x21 and ord(s) <= 0x7E

class BinaryToAscii:
    def __init__(self, buf, column_width=16):
        self.buf = buf
        self.column_width = column_width

    def _convert_buffer(self):
        pass

    def __str__(self):
        s = ''
        index = 0
        while index < len(self.buf):
            length = min(self.column_width, len(self.buf) - index)
            if len(s) > 0 and len(self.buf) > index:
                s += '\n'
            s += '{:04X} : '.format(index)
            for i in range(index, index + length):
                s += '{:02X} '.format(ord(self.buf[i]))
            if length < self.column_width:
                s += '   ' * (self.column_width - length)
            s += ' '
            for i in range(index, index + length):
                if is_printable(self.buf[i]):
                    s += self.buf[i]
                else:
                    s += '.'
            index += length
        return s

def _parse_args():
    parser = argparse.ArgumentParser(description='Convert binary data to ascii')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-b', '--base64', metavar='<buffer>', type=str, help='base64 buffer')
    group.add_argument('-x', '--hex', metavar='<buffer>', type=str, help='hex buffer')
    args = parser.parse_args()
    if args.base64:
        return base64.standard_b64decode(args.base64)
    else:
        return binascii.unhexlify(args.hex)

def main():
    buf = _parse_args()
    try:
        print(BinaryToAscii(buf))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

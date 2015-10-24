#!/usr/bin/python
from __future__ import print_function
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
            for i in range(index, index + length):
                s += '{:02X} '.format(ord(self.buf[i]))
            s += ' '
            for i in range(index, index + length):
                if is_printable(self.buf[i]):
                    s += self.buf[i]
                else:
                    s += '.'
            index += length
        return s

def main():
    try:
        for arg in sys.argv[1:]:
            print(BinaryToAscii(arg))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

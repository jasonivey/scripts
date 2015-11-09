#!/usr/bin/python

import argparse
import exceptions
import base64
import binascii
import sys
import traceback
import uuid

def parse_proto_buffer(buf):
    if ord(buf[0]) != 0x08:
        raise exceptions.RuntimeError('unknown proto buffer')

    field = 1
    index = 2
    while index < len(buf):
        index += 1
        length = ord(buf[index])
        index += 1
        s = buf[index:index + length]
        print("field {0}: '{1}'".format(field, s))
        index += length
        field += 1

def is_printable(s):
    return ord(s) >= 0x21 and ord(s) <= 0x7E

def is_duplicate(s, strs):
    if s in strs:
        return True
    for str1 in strs:
        if s in str1:
            return True 
    return False 

def find_printable_strs(buf):
    strs = []
    index = 0
    while index < len(buf):
        if not is_printable(buf[index]):
            index += 1
            continue
        length = 1
        while index + length < len(buf) and is_printable(buf[index + length]):
            length += 1
        s = buf[index : index + length]
        if not is_duplicate(s, strs):
            strs.append(s)
        index += 1
    return strs

def find_length_and_strs(buf):
    strs = []
    index = 0
    while index < len(buf):
        length = ord(buf[index])
        index += 1
        if index + length > len(buf) or length == 0:
            continue
        s = buf[index:index + length]
        if all(is_printable(c) for c in s):
            strs.append(s)
    return strs

PROVIDER = "slingtv"

def _FindProviderInRequestBody(buf):
    if len(PROVIDER) > len(buf):
        return -1 
    index = 3
    while index < len(buf) - len(PROVIDER):
        if ord(buf[index]) == len(PROVIDER) and \
           PROVIDER == buf[index + 1 : index + 1 + len(PROVIDER)] and \
           index > 1:
                print('found everything returning %d' % index)
                return index - 1
        index += 1
    return -1

def _ParseRequestBody1(buf):
    index = _FindProviderInRequestBody(buf)
    if index == -1:
        print('Did not find the provider in the request buffer')
        return None, None
    if index < 0x20:
        print('damn1')
        return None, None
    if index + 2 + len(PROVIDER) + 2 + 0x2C >= len(buf):
        print('damn2')
        return None, None
    key_id_size = 0x20
    key_id_index = index - key_id_size
    key_id = uuid.UUID(buf[key_id_index : key_id_index + key_id_size])
    content_id_size = 0x2C
    content_id_index = index + 2 + len(PROVIDER) + 2
    content_id = base64.standard_b64decode(buf[content_id_index : content_id_index + content_id_size])
    content_id = uuid.UUID(content_id)
    return key_id, content_id

def _FindProviderInRequestBody(buf):
    #buf = self.request.body
    if len(PROVIDER) > len(buf):
        return -1
    index = 3
    while index < len(buf) - len(PROVIDER):
        if ord(buf[index]) == len(PROVIDER) and \
           PROVIDER == buf[index + 1 : index + 1 + len(PROVIDER)] and \
           index > 1:
            #print('found everything returning %d' % index)
            return index - 1
        index += 1
    return -1

def _ParseKeyId(buf, index):
    #buf = self.request.body
    if index < 0x20:
        return None
    key_id_size = 0x20
    key_id_index = index - key_id_size
    return uuid.UUID(buf[key_id_index : key_id_index + key_id_size])

def _ParseContentId(buf, index):
    #buf = self.request.body
    if index + 2 + len(PROVIDER) + 1 >= len(buf):
        return None
    content_id_size = ord(buf[index + 2 + len(PROVIDER) + 1])
    content_id_index = index + 2 + len(PROVIDER) + 2
    if content_id_index + content_id_size > len(buf):
        return None
    return buf[content_id_index : content_id_index + content_id_size]

def _ParseRequestBody(buf):
    #buf = self.request.body
    index = _FindProviderInRequestBody(buf)
    if index == -1:
        return
    key_id = _ParseKeyId(buf, index)
    content_id = _ParseContentId(buf, index)
    return key_id, content_id

def main():
    #key_id, pssh = parse_args()
    try:
        buf = base64.standard_b64decode(sys.argv[1])
        #parse_proto_buffer(buf)
        #for s in find_length_and_strs(buf):
        #    print(s)
        for s in _ParseRequestBody(buf):
            print(s)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


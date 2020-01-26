
import argparse
import os
import re
import sys
import socket

import lsdvr_http_api

def _is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return ip
    except:
        msg = "{0} is not a valid ip address".format(ip)
        raise argparse.ArgumentTypeError(msg)

def _parse_args():
    description = 'Get the LSDVR average file sizes for a stream'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--ipaddr', metavar='<ip address>', required=True, type=_is_valid_ip, help='ip address of LSDVR')
    parser.add_argument('-l', '--liststreams', default=False, action='store_true', help='whether to query the LSDVR for a list of valid streams')
    parser.add_argument('-s', '--stream', metavar='<stream>', required=False, default=None, help='which stream to average all of the files')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='output verbose debugging information')
    args = parser.parse_args()
    return args.ipaddr, args.liststreams, args.stream, args.verbose

def _get_streams(ipaddr, stream, verbose):
    streams = []
    for partition in lsdvr_http_api.get_stream_partitions(ipaddr, stream, verbose):
        for id, stream_size in lsdvr_http_api.get_stream_files_sizes(ipaddr, stream, partition, verbose).items():
            stream_size.process()
            print(stream_size)

def _get_averages(ipaddr, stream, verbose):
    for stream in _get_streams(ipaddr, stream, verbose):
        pass

def main():
    ipaddr, liststreams, stream, verbose = _parse_args()
    print('ipaddr: {0}, list streams: {1}, stream id: {2}, verbose: {3}\n'.format(ipaddr, liststreams, stream, verbose))

    if liststreams:
        lsdvr_http_api.list_streams(ipaddr, verbose)
    if stream:
        _get_averages(ipaddr, stream, verbose)

    return 0

if __name__ == '__main__':
    main()

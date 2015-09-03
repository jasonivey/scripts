#!/usr/bin/python
from __future__ import print_function
import argparse
import os
import re
import subprocess
import sys
import traceback


class NetworkInfo:
    def __init__(self, buf):
        self.name = None
        self.ip = None
        self.mac = None
        self.active = False
        self._parse(buf)

    def _parse_mac(self, buf):
        match = re.match(r'(?P<name>[^:]+):\s*flags=', buf[0])
        if match:
            self.name = match.group('name')
        for i in buf[1:]:
            match = re.match(r'ether\s*(?P<ether>[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2})', i.strip())
            if match:
                self.mac = match.group('ether')
                continue
            match = re.match(r'inet\s+(?P<ipaddr>[^\s]+)\s+netmask', i.strip())
            if match:
                self.ip = match.group('ipaddr')
                continue
            match = re.match(r'status:\s+(?P<status>(in)?active)', i.strip())
            if match:
                self.active = match.group('status') == 'active'

    def _parse_linux(self, buf):
        print(buf[0])
        match = re.match(r'(?P<name>[^\s]+)\s+Link encap:', buf[0])
        if match:
            self.name = match.group('name')
        for i in buf:
            match = re.search(r'HWaddr\s+(?P<ether>[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2}:[\da-fA-F]{2})', i.strip())
            if match:
                self.mac = match.group('ether')
                continue
            match = re.match(r'inet addr:\s*(?P<ipaddr>[^\s]+)\s+Bcast', i.strip())
            if match:
                self.ip = match.group('ipaddr')
                continue
            self.active = True

    def _parse(self, buf):
        if len(buf) == 0:
            return
        if sys.platform.startswith('darwin'):
            self._parse_mac(buf)
        else:
            self._parse_linux(buf)

    @property
    def valid(self):
        return self.active and self.name != None and self.ip != None and self.mac != None

    def __str__(self):
        s = ''
        s += '%-17s %s\n' % ('IP Address {0}:'.format(self.name), self.ip)
        s += '%-17s %s' % ('MAC Address {0}:'.format(self.name), self.mac)
        return s

def network_info():
    command = 'ifconfig'
    process = subprocess.Popen(command, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        raise exceptions.RuntimeError('error while running ifconfig')
    device = []
    devices = []
    for line in stdoutdata.decode('ascii').split('\n'):
        inside_device = re.match(r'^\s.*$', line)
        if not inside_device:
            network_info = NetworkInfo(device)
            if network_info.valid:
                devices.append(network_info)
            device = []
        device.append(line.strip())
    return devices

def main():
    try:
        for device in network_info():
            print(device)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

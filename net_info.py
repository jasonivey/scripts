#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from enum import IntEnum
import ipaddress
import netifaces
import os
import re
import string
import sys
import traceback

class NetworkInterfaces(IntEnum):
    AF_APPLETALK = netifaces.AF_APPLETALK
    AF_ASH = netifaces.AF_ASH
    AF_ATMPVC= netifaces.AF_ATMPVC
    AF_ATMSVC = netifaces.AF_ATMSVC
    AF_AX25 = netifaces.AF_AX25
    AF_BLUETOOTH = netifaces.AF_BLUETOOTH
    AF_BRIDGE = netifaces.AF_BRIDGE
    AF_DECnet = netifaces.AF_DECnet
    AF_ECONET = netifaces.AF_ECONET
    AF_FILE = netifaces.AF_FILE
    AF_INET = netifaces.AF_INET
    AF_INET6 = netifaces.AF_INET6
    AF_IPX = netifaces.AF_IPX
    AF_IRDA = netifaces.AF_IRDA
    AF_ISDN = netifaces.AF_ISDN
    AF_KEY = netifaces.AF_KEY
    AF_LINK = netifaces.AF_LINK
    AF_NETBEUI = netifaces.AF_NETBEUI
    AF_NETLINK = netifaces.AF_NETLINK
    AF_NETROM = netifaces.AF_NETROM
    AF_PACKET = netifaces.AF_PACKET
    AF_PPPOX = netifaces.AF_PPPOX
    AF_ROSE = netifaces.AF_ROSE
    AF_ROUTE = netifaces.AF_ROUTE
    AF_SECURITY = netifaces.AF_SECURITY
    AF_SNA = netifaces.AF_SNA
    AF_UNIX = netifaces.AF_UNIX
    AF_UNSPEC = netifaces.AF_UNSPEC
    AF_WANPIPE = netifaces.AF_WANPIPE
    AF_X25 = netifaces.AF_X25

def get_variable_name(**var):
    return list(var.keys())

def _parse_args():
    parser = argparse.ArgumentParser(description='Test out netifaces package for timing')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    #args = parser.parse_args()
    #app_settings.update(vars(args))
    #app_settings.print_settings(print_always=False)

class IpAddressV6:
    #IP_ADDRESS_REGEX_V6 = re.compile(r'^(?:([A-Fa-f0-9]{1,4}):){7}([A-Fa-f0-9]{1,4})$')
    IP_ADDRESS_REGEX_V6 = re.compile(r'^([a-fA-F0-9]{1,4}):([a-fA-F0-9]{1,4}):([a-fA-F0-9]{1,4}):([a-fA-F0-9]{1,4}):' \
                                      r'([a-fA-F0-9]{1,4}):([a-fA-F0-9]{1,4}):([a-fA-F0-9]{1,4}):([a-fA-F0-9]{1,4})$')

    def __init__(self, input):
        ip_address = None
        if isinstance(input, str):
            ip_address = IpAddressV6.parse(input)
        elif isinstance(input, list) and len(input) == 8 and all(ch in string.hexdigits for ch in ''.join(input)):
            ip_address = input
        if ip_address is None:
            raise TypeError(f'Attempting to construct an IpAddressV6 with an invalid input ({input})')
        self._ip_address_words = ip_address

    @property
    def ip_address(self):
        if self.is_loopback:
            return '::1'
        return ':'.join(self._ip_address_words)

    @property
    def is_loopback(self):
        return len([i for i, j in zip(self._ip_address_words, [1, 0, 0, 0, 0, 0, 0, 0]) if i == j]) == len(self._ip_address_words)

    @staticmethod
    def parse(input):
        if input == '::1':
            return [1, 0, 0, 0, 0, 0, 0, 0]
        if not (match := IpAddressV6.IP_ADDRESS_REGEX_V6.match(input.strip())):
            return None
        print(match.groups())
        return [match.group(1), match.group(2), \
                match.group(3), match.group(4), \
                match.group(5), match.group(6), \
                match.group(7), match.group(8)]

    def __str__(self):
        return self.ip_address

class IpAddressV4:
    #MAC_ADDRESS = re.compile('r\d{2}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}')
    IP_ADDRESS_REGEX_V4 = re.compile(r'^(?P<octet1>25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                                      r'(?P<octet2>25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                                      r'(?P<octet3>25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                                      r'(?P<octet4>25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    def __init__(self, input):
        ip_address = None
        if isinstance(input, str):
            ip_address = IpAddressV4.parse(input)
        elif isinstance(input, list):
            ip_address = input
        if ip_address is None:
            raise TypeError(f'Attempting to construct an IpAddressV4 with an invalid input ({input})')
        self._ip_address_octets = ip_address

    @property
    def ip_address(self):
        return '.'.join([str(octet) for octet in self._ip_address_octets])

    @property
    def is_loopback(self):
        return len([i for i, j in zip(self._ip_address_octets, [127, 0, 0, 1]) if i == j]) == len(self._ip_address_octets)

    @staticmethod
    def parse(input):
        if not (match := IpAddressV4.IP_ADDRESS_REGEX_V4.match(input.strip())):
            return None
        return [int(match.group('octet1')), int(match.group('octet2')), int(match.group('octet3')), int(match.group('octet4'))]

    def __str__(self):
        return self.ip_address

class NetworkDevice:
    def __init__(self, name, mac_address, ip_address, ip_address_v6):
        self._name = name
        self._mac_address = mac_address
        self._ip_address = ip_address
        self._ip_address = ip_address_v6

# ec:f4:bb:78:3f:57: 6 double bytes, 5 colons
def get_network_devices():
    for interface in netifaces.interfaces():
        print(f'looking at {interface}')
        mac_address = ip_address = ip_address_v6 = None
        ifaddresses = netifaces.ifaddresses(interface)
        for interface_type, ifaddress in ifaddresses.items():
            print(f'{interface_type}: {ifaddress}\n\n')
            if interface_type == NetworkInterfaces.AF_LINK:
                print(f'{interface}: AF_LINK: {ifaddress}')
            elif interface_type == netifaces.AF_INET6:
                for subaddr in ifaddress:
                    print(f'IPv6: {subaddr}')
                    if 'addr' in subaddr:
                        ip_address = IpAddressV6(subaddr['addr'])
                        print(f'IPv6: {ip_address}')
            elif interface_type == netifaces.AF_INET:
                for subaddr in ifaddress:
                    print(f'IPv4: {subaddr}')
                    if 'addr' in subaddr:
                        ip_address = IpAddressV4(subaddr['addr'])
                        print(f'IPv4: {ip_address}')
            else:
                print(f'some other type {interface_type}: {subaddr}')
        print('')
    return None, None

def main():
    assert False, "ipaddress.IPv4Address ipaddress.IPv6Address"
    #_parse_args()
    try:
        device, ip_address = get_network_devices()
        #print(f'{device}: {ip_address}')
        pass
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

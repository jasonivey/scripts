#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
import copy
import ipaddress
import os
import re
import shlex
import socket
import subprocess
import sys
import traceback

import psutil
import location_info

_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE:
        print(s, file=sys.stdout)

class NameAndMac:
    def __init__(self, name=None, mac=None):
        self._name = name
        self._mac = mac

    def __copy__(self):
        return NameAndMac(copy.copy(self.name), copy.copy(self.mac))

    def clear(self):
        self._name = None
        self._mac = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def mac(self):
        return self._mac

    @mac.setter
    def mac (self, value):
        self._mac = value

    @property
    def is_valid(self):
        return self._name and self._mac

    def __str__(self):
        return '{}: {}'.format(self._name, self._mac)


class NetworkInfo:
    def __init__(self, name=None, ip=None, mac=None):
        self._name = name
        self._ip = ip
        self._mac = mac

    def __copy__(self):
        return NetworkInfo(copy.copy(self.name), copy.copy(self.ip), copy.copy(self.mac))

    def clear(self):
        self._name = None
        self._ip = None
        self._mac = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, value):
        self._ip = value

    @property
    def mac(self):
        return self._mac

    @mac.setter
    def mac (self, value):
        self._mac = value

    @property
    def is_valid(self):
        return self._name and self._ip and self._mac

    def __str__(self):
        return '{}: {}, {}'.format(self._name, self._ip, self._mac)


class SystemInfo:
    def __init__(self, hostname=None, public_ip=None, network_infos=None):
        self._hostname = hostname
        self._public_ip = public_ip
        self._network_infos = network_infos

    def __copy__(self):
        return SystemInfo(copy.copy(self.hostname), copy.copy(self.public_ip), copy.copy(self.network_infos))

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        self._hostname = value

    @property
    def computer_name(self):
        return self._hostname[:self.hostname.find('.')] if self.hostname.find('.') != -1 else None

    @property
    def public_ip(self):
        return self._public_ip

    @public_ip.setter
    def public_ip(self, value):
        self._public_ip = value

    @property
    def network_infos(self):
        return self._network_infos

    @network_infos.setter
    def network_infos(self, value):
        self._network_infos = value

    def __str__(self):
        s = ''
        return s

def _call_external_command(command):
    _verbose_print('INFO: command: %s' % command)
    args = shlex.split(command)
    process = subprocess.Popen(args, encoding='utf-8', universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.wait() != 0:
        excusable_error = 'is not a recognized network service'
        if command.find('-getinfo') != -1 and (error.find(excusable_error) != -1 or output.find(excusable_error) != -1):
            return []
        print('ERROR:  {}'.format(command), file=sys.stderr)
        print('stderr: {}'.format(error), file=sys.stderr)
        print('stdout: {}'.format(output), file=sys.stderr)
        return []
    return output.split('\n')

def _list_all_hardware_ports_darwin():
    output = _call_external_command('networksetup -listallhardwareports')
    hardware_ports = []
    name_and_mac = NameAndMac()
    for line in output:
        port_match = re.search(r'^Hardware Port:\s*(?P<port>.*)', line.strip())
        if port_match:
            name_and_mac.name = port_match.group('port').strip()
        mac_match = re.search(r'^Ethernet Address:\s*(?P<mac>.*)', line.strip())
        if mac_match:
            name_and_mac.mac = mac_match.group('mac').strip()
        if name_and_mac.is_valid:
            hardware_ports.append(copy.copy(name_and_mac))
            name_and_mac.clear()
    return hardware_ports

def _get_ip_info_darwin(service, mac):
    command = 'networksetup -getinfo \"{}\"'.format(service)
    output = _call_external_command(command)
    for line in output:
        match = re.search(r'^IP address:\s*(?P<ip>.*)', line.strip())
        if match:
            ip = match.group('ip').strip()
            return ipaddress.ip_address(ip)
    return None

def _get_network_infos_darwin():
    networking_infos = []
    hardware_ports = _list_all_hardware_ports_darwin()
    for hardware_port in hardware_ports:
        ip = _get_ip_info_darwin(hardware_port.name, hardware_port)
        if not ip:
            continue
        networking_infos.append(NetworkInfo(hardware_port.name, ip, hardware_port.mac))
    return networking_infos

def _get_network_infos():
    networking_infos = []
    nics = psutil.net_if_addrs()
    for name, addresses in nics.items():
        _verbose_print('name: %s' % name)
        network_info = NetworkInfo(name=name)
        for address in addresses:
            _verbose_print('address: {}'.format(address))
            if address.family == socket.AF_INET:
                try:
                    address_str = address.address if '%' not in address.address else address.address[:address.address.find('%')]
                    ip = ipaddress.ip_address(address_str) if not address_str.startswith('127.') else None
                    network_info.ip = ip
                except ValueError as e:
                    ip = None
                    print('ERROR: {} is not a valid IPv4 address'.format(address.address), file=sys.stderr)
            if address.family == socket.AF_INET6 and not ip:
                try:
                    address_str = address.address
                    if '%' in address.address:
                        address_str = address.address[:address.address.find('%')]
                    ip = ipaddress.ip_address(address_str) if not address_str.startswith('::1') else None
                    network_info.ip = ip
                except ValueError as e:
                    ip = None
                    print('ERROR: {} is not a valid IPv6 address'.format(address.address), file=sys.stderr)
            elif address.family == psutil.AF_LINK:
                mac = address.address
                network_info.mac = mac
            if network_info.is_valid:
                networking_infos.append(copy.copy(network_info))
                network_info.clear()
                network_info.name = name
                break
        _verbose_print('')
    return networking_infos

def get_networking_infos():
    net_infos = _get_network_infos() if sys.platform != 'darwin' else _get_network_infos_darwin()
    return net_infos

def _get_displayable_networking_infos():
    network_infos = get_networking_infos()
    infos = []
    for network_info in network_infos:
        infos.append(('IP Address {}'.format(network_info.name), network_info.ip))
        infos.append(('Mac Address {}'.format(network_info.name), network_info.mac))
    return infos

def get_public_ip_address():
    public_ip = location_info.get_ip_address()
    return [('Public IP', ipaddress.ip_address(public_ip))] if public_ip else []

def get_hostname_info():
    hostnames = []
    hostname = socket.gethostname()
    if hostname and len(hostname) > 0:
        hostnames.append(('Hostname', hostname))
        index = hostname.find('.')
        if index != -1:
            hostnames.append(('Computer Name', hostname[:index]))
    return hostnames

def get_system_info():
    hostnames = get_hostname_info()
    public_ip = get_public_ip_address()
    networking_infos = _get_displayable_networking_infos()
    return hostnames + public_ip + networking_infos

def _parse_args():
    parser = argparse.ArgumentParser(description='Output or return various IP and Mac address info on the current system')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

def main():
    _parse_args()
    try:
        infos = get_system_info()
        name_width = max([len(label) for (label, value) in infos])
        for (label, value) in infos:
            print(('%-' + str(name_width) + 's : %s') % (label, value))
    except:
        print('ERROR: network_info failed -- uncomment traceback info to fix', file=sys.stderr)
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

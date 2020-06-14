#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
import ipaddress
import os
import psutil
import re
import shlex
import socket
import subprocess
import sys
import traceback

import location_info

user_tags = {
    'info'        : parse('<bold><green>'),    # bold green
    'error'       : parse('<bold><red>'),      # bold red
    'label'       : parse('<bold><cyan>'),     # bold cyan
    'value'       : parse('<bold><yellow>'),   # bold yellow
}

am = AnsiMarkup(tags=user_tags)

_VERBOSE = False

def _verbose_print(msg):
    if _VERBOSE:
        am.ansiprint(f'<info>INFO: {msg}</info>', file=sys.stdout)

def _error_print(msg):
    am.ansiprint(f'<error>ERROR: {msg}</error>', file=sys.stderr)

def _call_external_command(command):
    _verbose_print(f'command: {command}')
    args = shlex.split(command)
    process = subprocess.Popen(args, encoding='utf-8', universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.wait() != 0:
        excusable_error = 'is not a recognized network service'
        if command.find('-getinfo') != -1 and (error.find(excusable_error) != -1 or output.find(excusable_error) != -1):
            return []
        _error_print(f'{command}')
        _error_print(f'stderr, {error}')
        _error_print(f'stdout, {output}')
        return []
    return output.split('\n')

class NetworkInfo:
    def __init__(self, name=None, ip=None, mac=None):
        self._name = name
        self._ip = ip
        self._mac = mac

    @property
    def name(self):
        return 'Lan' if self._name == 'USB 10/100/1000 LAN' else self._name

    @property
    def ip(self):
        return str(self._ip)

    @property
    def mac(self):
        return self._mac

    def __str__(self):
        s = 'IP Address {name}: {self.ip}\n'
        return s + 'Mac Address {self.name}: {self.mac}\n'

class NetworkInfos:
    def __init__(self):
        self._infos = []
        self._index = -1
        if sys.platform != 'darwin':
            self.__linux_find_network_devices()
        else:
            self.__darwin_find_network_devices()
        _verbose_print(f'number of networ devices: {len(self._infos)}')

    def __iter__(self):
        if len(self._infos) > 0:
            self._index = 0
        return self

    def __next__(self):
        if self._index == -1 or self._index >= len(self._infos):
            self._index = -1
            raise StopIteration
        i = self._index
        self._index += 1
        return self._infos[i]

    def __len__(self):
        return len(self._infos)

    def __darwin_get_all_network_devices(self):
        output = _call_external_command('networksetup -listallhardwareports')
        name, mac = None, None
        for line in output:
            port_match = re.search(r'^Hardware Port:\s*(?P<port>.*)', line.strip())
            if port_match:
                name = port_match.group('port').strip()
            mac_match = re.search(r'^Ethernet Address:\s*(?P<mac>.*)', line.strip())
            if mac_match:
                mac = mac_match.group('mac').strip()
            if name and mac:
                yield (name, mac)
                name, mac = None, None

    def __darwin_get_ip_address(self, service_name):
        command = f'networksetup -getinfo \"{service_name}\"'
        output = _call_external_command(command)
        ip, router = None, None
        for line in output:
            ip_match = re.search(r'^IP address:\s*(?P<ip>.*)', line.strip())
            if ip_match:
                ip_str = ip_match.group('ip').strip()
                ip = ipaddress.ip_address(ip_str)
            router_match = re.search(r'^Router:\s*(?P<router>.*)', line.strip())
            if router_match:
                router_str = router_match.group('router').strip()
                router = ipaddress.ip_address(router_str) if router_str else None
        return ip if ip and router else None

    def __darwin_find_network_devices(self):
        for (name, mac) in self.__darwin_get_all_network_devices():
            ip = self.__darwin_get_ip_address(name)
            if not ip:
                continue
            self._infos.append(NetworkInfo(name, ip, mac))

    def __linux_find_network_devices(self):
        nics = psutil.net_if_addrs()
        for name, addresses in nics.items():
            _verbose_print(f'name: {name}')
            ip, mac = None, None
            for address in addresses:
                _verbose_print(f'address: {address}')
                ip_type = ''
                try:
                    if address.family == socket.AF_INET:
                        ip_type = 'IPv4'
                        address_str = address.address if '%' not in address.address else address.address[:address.address.find('%')]
                        ip = ipaddress.ip_address(address_str) if not address_str.startswith('127.') else None
                    if address.family == socket.AF_INET6:
                        ip_type = 'IPv6'
                        address_str = address.address
                        if '%' in address.address:
                            address_str = address.address[:address.address.find('%')]
                        ip = ipaddress.ip_address(address_str) if not address_str.startswith('::1') else None
                    if address.family == psutil.AF_LINK:
                        mac = address.address
                except ValueError as e:
                    _error_print(f'{address.address} is not a valid {ip_type} address')
                if name and ip and mac:
                    self._infos.append(NetworkInfo(name, ip, mac))
                    break
            _verbose_print('')

    def __str__(self):
        s = ''
        for info in self._infos:
            s += str(info)
        return s

class SystemInfo:
    def __init__(self):
        self._hostname = socket.gethostname()
        self._public_ip = location_info.get_ip_address()
        self._network_infos = NetworkInfos()

    @property
    def hostname(self):
        return self._hostname

    @property
    def computer_name(self):
        if self.hostname:
            index = self.hostname.find('.')
            if index != -1:
                return self.hostname[:index]
            return self.hostname
        return ''

    @property
    def public_ip(self):
        return str(self._public_ip)

    @property
    def network_infos(self):
        return self._network_infos

    @property
    def network_infos_length(self):
        return len(self._network_infos)

    def __str__(self):
        s = ''
        return s

def _get_label(label_str):
    return am.ansistring(f'<label>{label_str}</label>')

def _get_value(value_str):
    return am.ansistring(f'<value>{value_str}</value>')

def _get_formatted_system_info():
    system_info = SystemInfo()
    info = []
    info.append((_get_label('Hostname:'), _get_value(system_info.hostname)))
    info.append((_get_label('Computer Name:'), _get_value(system_info.computer_name)))
    info.append((_get_label('Public IP:'), _get_value(system_info.public_ip)))
    for network_info in system_info.network_infos:
        info.append((_get_label(f'IP Address {network_info.name}:'), _get_value(network_info.ip)))
        info.append((_get_label(f'IP Address {network_info.name}:'), _get_value(network_info.mac)))
    return info

def _parse_args():
    parser = argparse.ArgumentParser(description='Output or return various IP and Mac address info on the current system')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

def main():
    _parse_args()
    try:
        infos = _get_formatted_system_info()
        max_label_width = max([len(am.strip(label)) for (label, value) in infos])
        for (label, value) in infos:
            print(f'{label:{max_label_width}} {value}')
    except:
        _error_print('network_info failed -- uncomment traceback info to fix')
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

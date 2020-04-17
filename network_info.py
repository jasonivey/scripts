#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
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
    port = device = mac = None
    for line in output:
        match = re.search(r'^Hardware Port:\s*(?P<port>.*)', line.strip())
        if match:
            port = match.group('port').strip()
            continue
        match = re.search(r'^Device:\s*(?P<device>.*)', line.strip())
        if match:
            device = match.group('device').strip()
            continue
        match = re.search(r'^Ethernet Address:\s*(?P<mac>.*)', line.strip())
        if match:
            mac = match.group('mac').strip()
        if port and device and mac:
            hardware_ports.append((port, device, mac))
            port = device = mac = None
    return hardware_ports

def _get_ip_info_darwin(service, mac):
    command = 'networksetup -getinfo \"{}\"'.format(service)
    output = _call_external_command(command)
    hardware_ports = []
    ip = new_mac = None
    for line in output:
        match = re.search(r'^IP address:\s*(?P<ip>.*)', line.strip())
        if match:
            ip = match.group('ip').strip()
            continue
        match = re.search(r'^{} ID:\s*(?P<mac>.*)'.format(service), line.strip())
        if match:
            new_mac = match.group('mac').strip()
        if ip and new_mac:
            if mac != new_mac:
                raise Exception('ERROR: mac address found with networksetup -listallhardwareports {} is not the same as found when calling {} {}'.format(mac, command, new_mac))
            return ipaddress.ip_address(ip)
    return None

def _get_network_infos_darwin():
    networking_infos = []
    for hardware_port in _list_all_hardware_ports_darwin():
        (port, device, mac) = hardware_port
        ip = _get_ip_info_darwin(port, mac)
        if not ip:
            continue
        networking_infos.append((port, ip))
        networking_infos.append((port, mac))
    return networking_infos
    #print('Hardware Port: {}\nDevice: {}\nEthernet Address: {}\nIP address: {}\n'.format(hardware_port[0], hardware_port[1], hardware_port[2], ip))

def _get_network_infos():
    networking_infos = []
    nics = psutil.net_if_addrs()
    for name, addresses in nics.items():
        _verbose_print('name: %s' % name)
        if name.startswith('awdl'):
            _verbose_print('INFO: skipping {} since it is a Apple wireless direct link to iOS devices'.format(name))
            continue
        ip = None
        mac = None
        for address in addresses:
            _verbose_print('address: {}'.format(address))
            if address.family == socket.AF_INET:
                try:
                    address_str = address.address if '%' not in address.address else address.address[:address.address.find('%')]
                    ip = ipaddress.ip_address(address_str) if not address_str.startswith('127.') else None
                except ValueError as e:
                    ip = None
                    print('ERROR: {} is not a valid IPv4 address'.format(address.address), file=sys.stderr)
            if address.family == socket.AF_INET6 and not ip:
                try:
                    address_str = address.address if '%' not in address.address else address.address[:address.address.find('%')]
                    ip = ipaddress.ip_address(address_str)
                except ValueError as e:
                    ip = None
                    print('ERROR: {} is not a valid IPv6 address'.format(address.address), file=sys.stderr)
            elif address.family == psutil.AF_LINK:
                mac = address.address
            if ip and mac:
                networking_infos.append((name, ip))
                networking_infos.append((name, mac))
                break
        _verbose_print('')
    return networking_infos

def get_networking_infos():
    net_infos = _get_network_infos() if sys.platform != 'darwin' else _get_network_infos_darwin()
    assert len(net_infos) % 2 == 0
    infos = []
    for index in range(0, len(net_infos), 2):
        (name, ip) = net_infos[index]
        infos.append(('IP Address {}'.format(name), ip))
        (name, mac) = net_infos[index + 1]
        infos.append(('MAC Address {}'.format(name), mac))
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
    networking_infos = get_networking_infos()
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

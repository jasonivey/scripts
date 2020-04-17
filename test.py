#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import ipaddress
import os
import re
import shlex
import sys
import subprocess
import traceback

_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE:
        print(s, file=sys.stdout)

def call_external_command(command):
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

def list_all_hardware_ports():
    output = call_external_command('networksetup -listallhardwareports')
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

def get_ip_info(service, mac):
    command = 'networksetup -getinfo \"{}\"'.format(service)
    output = call_external_command(command)
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

def find_networks():
    networks = {}
    for hardware_port in list_all_hardware_ports():
        (port, device, mac) = hardware_port
        ip = get_ip_info(port, mac)
        if not ip:
            continue
        networks[port] = (ip, mac)
    return networks
    #print('Hardware Port: {}\nDevice: {}\nEthernet Address: {}\nIP address: {}\n'.format(hardware_port[0], hardware_port[1], hardware_port[2], ip))

def main(args):
    try:
        for name, network in find_networks().items():
            (ip, mac) = network
            print('{}: {}'.format(name, ip))
            print('{}: {}'.format(name, mac))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

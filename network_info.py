#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import re
import socket
import subprocess
import sys
import traceback

import psutil
import location_info

def _get_network_infos():
    networking_infos = []
    nics = psutil.net_if_addrs()
    for name, addresses in nics.items():
        ip = None
        mac = None
        for address in addresses:
            if address.family == socket.AddressFamily.AF_INET:
                ip = address.address if not address.address.startswith('127.') else None
            elif address.family == socket.AddressFamily.AF_LINK:
                mac = address.address
            if ip and mac:
                networking_infos.append((name, ip))
                networking_infos.append((name, mac))
                break
    return networking_infos

def get_networking_infos():
    net_infos = _get_network_infos()
    assert len(net_infos) % 2 == 0
    infos = []
    for index in range(0, len(net_infos), 2):
        net_info = net_infos[index]
        infos.append(('IP Address {}'.format(net_info[0]), net_info[1]))
        net_info = net_infos[index + 1]
        infos.append(('MAC Address {}'.format(net_info[0]), net_info[1]))
    return infos

def get_external_ip_address():
    router_ip = location_info.get_ip_address()
    return [('Router IP Address', router_ip)] if router_ip else []

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
    external_ip = get_external_ip_address()
    networking_infos = get_networking_infos()
    return hostnames + external_ip + networking_infos

def main():
    try:
        infos = get_system_info()
        name_width = max([len(info[0]) for info in infos])
        for info in infos:
            print(('%-' + str(name_width) + 's : %s') % (info[0], info[1]))
    except:
        print('ERROR: network_info failed -- uncomment traceback info to fix', file=sys.stderr)
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

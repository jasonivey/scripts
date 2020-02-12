#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import re
import subprocess
import sys
import traceback

def _run_command(cmd):
    process = subprocess.Popen(cmd, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    if process.wait() != 0:
        print('ERROR: while running \'{}\''.format(cmd), file=sys.stderr)
        return False
    else:
        return stdoutdata.decode('ascii').split('\n')

def _get_mac_os_interfaces():
    output = _run_command('ifconfig -l')
    assert len(output) == 1
    return output.split(' ')

def _get_linux_os_interfaces():
    output = _run_command('ifconfig -s')
    assert len(output) >= 1

    interfaces = []
    for line in output[1:]:
        match = re.search(r'(?P<interface>[^\s]+)\s+', line)
        if match:
            interfaces.append(match.group('interface'))

    return interfaces

def get_system_info():
    if sys.platform.startswith('darwin'):
        interfaces = _get_mac_os_interfaces()
    else:
        interfaces = _get_linux_os_interfaces()
    return [('"{}"'.format(interface), '') for interface in interfaces]

def main():
    try:
        infos = get_system_info()
        name_width = max([len(info[0]) for info in infos])
        for info in infos:
            print(('%-' + str(name_width) + 's : %s') % (info[0], info[1]))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

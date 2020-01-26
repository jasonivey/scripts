#!/usr/bin/env python

import argparse
import exceptions
import os
import pep8
import re
import shutil
import sys
import traceback

import bzr_vcs

_COMPONENTS = ['rlp-cmake',
              'nlplib',
              'ss',
              'yanfs',
              'libdicom',
              'libwpd-java',
              'tika',
              'feeder',
              'generic-conf',
              'osconfig',
              'webapp',
              'appliance-base',
              'generic-branding',
              'linux-firstboot',
              'perfectsearch-release',
              'web-server',
              'generic-appliance',
              'fujitsu-branding',
              'fujitsu-conf',
              'fujitsu-appliance',
              'perfectsearch-branding',
              'perfectsearch-conf',
              'perfectsearch-appliance',
              'datacove-branding',
              'tangent-conf',
              'tangent-appliance',
              'xi3-branding',
              'xi3-conf',
              'xi3-appliance',
              'appliance-product']

def _parse_args():
    parser = argparse.ArgumentParser(description='Merge two bzr branches')
    parser.add_argument('-s', '--source', dest='source', required=True, help='source branch')
    parser.add_argument('-d', '--destination', dest='destination', required=False, help='destination branch')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show extra output')
    parser.add_argument('-c', '--start-component', dest='start_component', required=False, help='skip over components and start in the middle of the list')
    args = parser.parse_args()
    global _COMPONENTS
    if args.start_component is not None:
        if not args.start_component in _COMPONENTS:
            raise argparse.ArgumentTypeError('start-component is naming an invalid component: {0}\nComponent Names:\n{1}'.format(args.start_component, '\n'.join(_COMPONENTS)))
        else:
            components = _COMPONENTS
            for i, component in enumerate(components):
                if args.start_component == component:
                    _COMPONENTS = _COMPONENTS[i:]
    return args.source, args.destination, args.verbose

def _get_newline():
    return '\r\n' if os.name == 'nt' else '\n'

def _get_sadm_dir():
    command = 'where sadm' if os.name == 'nt' else 'which sadm'
    process = subprocess.Popen(command, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    sadm_path = stdoutdata.split(_get_newline())[0]
    return os.path.dirname(sadm_path)

def _get_sandbox_container_folder():
    with open(os.path.join(_get_sadm_dir(), 'sadm.conf')) as sadm_conf:
        for line in sadm_conf.readlines():
            if line.strip().startswith('sandbox_container_folder'):
                return os.path.abspath(line.strip().split('=')[1].strip())
    raise exceptions.RuntimeError('sandbox.conf does not contain the sandbox_container_folder')

def sandbox_build(path, verbose=False):
    sb_root = bzr_vcs.find_sandbox_root(path)
    if sb_root is None:
        raise exceptions.RuntimeError('Unable to build sandbox where sandbox root is not found')
    process = subprocess.Popen('sb build', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=sb_root)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    if verbose:
        print(stdoutdata)
    return process.returncode == 0 and bool(re.search('BUILD SUCCESSFUL', stdoutdata))

def sandbox_test(path, verbose=False):
    sb_root = bzr_vcs.find_sandbox_root(path)
    if sb_root is None:
        raise exceptions.RuntimeError('Unable to build sandbox where sandbox root is not found')
    process = subprocess.Popen('sb test', shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=sb_root)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    if verbose:
        print(stdoutdata)
    return process.returncode == 0 and bool(re.search('All Test Groups passed!', stdoutdata))

def sandbox_init(sandbox_spec, verbose=False):
    process = subprocess.Popen('sadm init {0}'.format(sandbox_spec), shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = process.communicate()
    process.wait()
    if verbose:
        print(stdoutdata)
    return process.returncode == 0 and bool(re.search('Sandbox is ready.', stdoutdata))

def merge_branches(src, dst, verbose=False):
    sandbox_dir = _get_sandbox_container_folder()
    checkin_message = 'merged to {0}.' + dst + ' from ' + dst

    for component_name in _COMPONENTS:
        sandbox_name = '{1}.{2}.official'.format(component_name, dst)
        sandbox_path = os.path.join(sandbox_dir, sandbox_name)
        if os.path.isdir(sandbox_path):
            shutil.rmtree(sandbox_path, True)
    
        if not sandbox_init(sandbox_name, verbose):
            print('\n\nERROR INIT-ing!!!\n\n')
            sys.exit(1)

        bzr_sandbox = bzr_vcs.Sandbox(sandbox_path, verbose)

        if not bzr_sandbox.merge(src):
            print('\n\nERROR MERGING!!!\n\n')
            sys.exit(1)

        if len(bzr_sandbox.stat()) == 0:
            print('Nothing to merge in this sandbox -- continuing to next!!!')
            continue

        if not sandbox_build(sandbox_path, verbose):
            print('\n\nERROR BUILDING!!!\n\n')
            sys.exit(1)

        if not sandbox_test(sandbox_path, verbose):
            print('\n\nERROR TESTING!!!\n\n')
            sys.exit(1)

        if not bzr_sandbox.checkin(checkin_message.format(component_name)):
            print('\n\nERROR CHECKIN!!!\n\n')
            sys.exit(1)
        
        if not bzr_sandbox.push():
            print('\n\nERROR PUSH!!!\n\n')
            sys.exit(1)

def main():
    src, dst, verbose = _parse_args()
    sys.exit(1)
    try:
        merge_branches(src, dst, verbose)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
	sys.exit(main())

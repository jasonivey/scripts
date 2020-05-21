#!/usr/bin/env python3
# vim: aw:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowrite, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
import os
import shutil
import subprocess
import sys
import traceback

_VERBOSE = False
_COLORS = {
    'blank'  : r'"\033]6;1;bg;*;default\a"',
    'lime'   : r'"\033]6;1;bg;*;default\a\033]6;1;bg;green;brightness;255\a"',
    'red'    : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a"',
    'blue'   : r'"\033]6;1;bg;*;default\a\033]6;1;bg;blue;brightness;255\a"',
    'yellow' : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a\033]6;1;bg;green;brightness;255\a\033]6;1;bg;blue;brightness;0\a"',
    'purple' : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a\033]6;1;bg;green;brightness;0\a\033]6;1;bg;blue;brightness;255\a"',
    'orange' : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a\033]6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;0\a"',
    'aqua'   : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]6;1;bg;green;brightness;255\a\033]6;1;bg;blue;brightness;255\a"',
    'redder' : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;128\a\033]6;1;bg;green;brightness;0\a\033]6;1;bg;blue;brightness;0\a"',
    'olive'  : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;128\a\033]6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;0\a"',
    'green'  : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;0\a"',
    'teal'   : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;128\a"',
    'navy'   : r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]6;1;bg;green;brightness;0\a\033]6;1;bg;blue;brightness;128\a"',
}

def _verbose_print(s):
    if _VERBOSE:
        print(s, file=sys.stdout)

def _parse_args():
    parser = argparse.ArgumentParser(description='Set the mac OS iterm tab color')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('color', const='blank', nargs='?', choices=_COLORS.keys())
    #parser.add_argument('color', default=argparse.SUPPRESS, const='blank', nargs='?', choices=_COLORS.keys())
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose
    if not args.color and not os.isatty(sys.stdin.fileno()):
        color = sys.stdin.readline().strip()
    else:
        color = args.color
    _verbose_print('Args, verbose: {}, color: {}'.format(_VERBOSE, color))
    return color

def _call_system_command(cmd):
    #
    # This works where as process.run or process.Popen do not. Those affect a child process which is destroyed after
    #  the process is destroyed.
    #
    _verbose_print('INFO: command: %s' % cmd)
    status = os.system(cmd)
    if os.WIFEXITED(status):
        exit_code = os.WEXITSTATUS(status)
        if exit_code == 0:
            _verbose_print('INFO: calling {} returned success'.format(cmd))
        else:
            print('ERROR: calling {} returned error {}'.format(cmd, exit_code), file=sys.stderr)
        return exit_code == 0
    elif os.WIFSIGNALED(status):
        if os.WCOREDUMP(status):
            print('ERROR: the call to {} signaled that it core dumped'.format(cmd), file=sys.stderr)
        else:
            _verbose_print('INFO: the call to {} was TERMINATED by a signal'.format(cmd))
            signal = os.WTERMSIG(status)
            print('ERROR: the call to {} was TERMINATED by signal {}'.format(cmd, signal), file=sys.stderr)
        return False
    elif os.WIFSTOPPED(status):
        _verbose_print('INFO: the call to {} was STOPPED by a signal'.format(cmd))
        signal = os.WSTOPSIG(status)
        print('ERROR: the call to {} was STOPPED by signal {}'.format(cmd, signal), file=sys.stderr)
        return False
    return True

def _call_echo_command(str_cmd):
    echo_cmd = 'echo'
    post_cmd = '-n -e'
    postfix = '> /dev/null 2>&1 ;'
    if sys.platform == 'darwin':
        _verbose_print('INFO: running in a mac OS environment')
        if shutil.which('gecho'):
            _verbose_print('INFO: found the gnu version of echo (gecho), using that instead')
            echo_cmd = 'gecho'
        #else:
        #    _verbose_print('INFO: unable to find the gnu version of echo (gecho), using standard version and redirecting output to null')
        #    postfix = '> /dev/null 2>&1 ;'
    #elif 'SSH_CONNECTION' not in os.environ:
    #    post_cmd = '-n'

    cmd = '{} {} {} {}'.format(echo_cmd, post_cmd, str_cmd, postfix)
    _call_system_command(cmd)

def set_tab_color(color):
    if color not in _COLORS:
        print('ERROR: {} is not a color supported by this script'.format(color), file=sys.stderr)
    else:
        _verbose_print('INFO: setting tab color to {}'.format(color))
        _call_echo_command(_COLORS[color])

def main():
    color = _parse_args()
    try:
        set_tab_color(color)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

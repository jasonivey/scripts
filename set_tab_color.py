#!/usr/bin/env python3
# vim: aw:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowrite, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
import os
import shlex
import shutil
from subprocess import run, CalledProcessError, SubprocessError
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

# Previous versions contain various attempts at trying to call the operating system to
#  change the tab color in iTerm2.
def _call_subprocess_run(cmd):
    try:
        _verbose_print('INFO: command: %s' % cmd)
        run(shlex.split(cmd), shell=False, check=True, env=os.environ, stdin=None, stdout=None, stderr=None)
        return True
    except CalledProcessError as err:
        print('ERROR: {} calling {}'.format(err.returncode, cmd))
        return False
    except SubprocessError as err:
        print('ERROR: subprocess run error calling {}'.format(cmd))
        return False

def _call_echo_command(color_str):
    cmd = f'printf {color_str}'
    _call_subprocess_run(cmd)

def set_tab_color(color):
    assert color in _COLORS, '{} is not a color supported by this script'.format(color)
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

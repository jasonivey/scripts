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

# I was unable to get this working for a long time. It would succeed in calling the command but it would not affect
#  the tab color. I thought it was due to the starting of the child process but I finally got it working once I
#  started splitting the arguments, passing shell=False and passing the os.environ in as the new env.
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

# Attempting to figure out why subprocess.call wouldn't work I also tested the following os.spawn calls. There didn't
#  seem to be a problem with these calls at all and I was able to change the tab color successfully.
def _call_os_spawn(cmd):
    _verbose_print('INFO: command: %s' % cmd)
    args = shlex.split(cmd)
    exit_code = os.spawnvpe(os.P_WAIT, args[0], args, os.environ)
    if exit_code == 0:
        _verbose_print('INFO: calling {} returned success'.format(cmd))
        return True
    else:
        print('ERROR: calling {} returned error {}'.format(cmd, exit_code), file=sys.stderr)
        return False

# This worked where I had trouble with subprocess.call due to it creating another process
def _call_os_system(cmd):
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

def _call_echo_command(color_str):
    cmd_name = 'echo'
    cmd_args = '-n -e'
    post_cmd = ''
    if sys.platform == 'darwin':
        _verbose_print('INFO: running in a mac OS environment')
        if shutil.which('gecho'):
            _verbose_print('INFO: found the gnu version of echo (gecho), using that instead')
            cmd_name = 'gecho'
        else:
            _verbose_print('INFO: unable to find the gnu version of echo (gecho), using standard version and redirecting output to null')
            post_cmd = '> /dev/null 2>&1'
    cmd = '{} {} {} {}'.format(cmd_name, cmd_args, color_str, post_cmd)
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

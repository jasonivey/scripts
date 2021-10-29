#!/usr/bin/env python3
# vim: aw:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowrite, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

import argparse
from pathlib import Path
import os
import random
import re
import shlex
from subprocess import run, CalledProcessError, SubprocessError
import sys
import traceback

random.seed(None)
_VERBOSE = False

def _verbose_print(s):
    if _VERBOSE:
        print(s, file=sys.stdout)


class RgbValue:
    RGB_REGEX = re.compile(
        r'(?P<red>\d{1,3})\s*,\s*(?P<green>\d{1,3})\s*,\s*(?P<blue>\d{1,3})')
    RGB_FORMAT = r'"\033]6;1;bg;red;brightness;{}\a\033]6;1;bg;green;' \
                 r'brightness;{}\a\033]6;1;bg;blue;brightness;{}\a"'

    def __init__(self, text):
        self._values = RgbValue.parse(text)
        if not self._values:
            raise ValueError(
                f'invalid rgb value {text}, correct format is rgb(0-255,0-255,0-255)'
            )

    def encode(self):
        return RgbValue.RGB_FORMAT.format(self._values['red'],
                                          self._values['green'],
                                          self._values['blue'])

    @staticmethod
    def is_valid(text):
        return True if RgbValue.parse(text) else False

    @staticmethod
    def parse(text):
        if not (match := RgbValue.RGB_REGEX.search(text)):
            return None
        return {
            'red': match.group('red'),
            'green': match.group('green'),
            'blue': match.group('blue')
        }

    def __str__(self):
        return f'rgb({self._values["red"]},{self._values["green"]},{self._values["blue"]})'


class TabColor:
    COLORS = {
        'blank':
        r'"\033]6;1;bg;*;default\a"',
        'lime':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;green;brightness;255\a"',
        'red':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a"',
        'blue':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;blue;brightness;255\a"',
        'yellow':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a\033]'
        r'6;1;bg;green;brightness;255\a\033]6;1;bg;blue;brightness;0\a"',
        'purple':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a\033]'
        r'6;1;bg;green;brightness;0\a\033]6;1;bg;blue;brightness;255\a"',
        'orange':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;255\a\033]'
        r'6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;0\a"',
        'aqua':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]'
        r'6;1;bg;green;brightness;255\a\033]6;1;bg;blue;brightness;255\a"',
        'redder':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;128\a\033]'
        r'6;1;bg;green;brightness;0\a\033]6;1;bg;blue;brightness;0\a"',
        'olive':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;128\a\033]'
        r'6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;0\a"',
        'green':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]'
        r'6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;0\a"',
        'teal':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]'
        r'6;1;bg;green;brightness;128\a\033]6;1;bg;blue;brightness;128\a"',
        'navy':
        r'"\033]6;1;bg;*;default\a\033]6;1;bg;red;brightness;0\a\033]'
        r'6;1;bg;green;brightness;0\a\033]6;1;bg;blue;brightness;128\a"',
    }

    def __init__(self, color_name=None, rgb_value=None):
        if color_name:
            assert color_name in TabColor.COLORS, f'{color_name} is not a valid color'
        self._color_name = color_name
        self._rgb_value = rgb_value

    @property
    def color(self):
        assert self._color_name, 'attempting to read color property before it has been set'
        return self._color_name

    @property
    def rgb(self):
        assert self._rgb_value, 'attempting to read RGB property before it has been set'
        return str(self._rgb_value)

    def encode(self):
        return TabColor.COLORS[
            self.color] if self._color_name else self._rgb_value.encode()

    def __str__(self):
        return f'{self.color}' if self._color_name else f'{str(self.rgb)}'


def _select_random_color_name():
    color_name = random.choice(list(TabColor.COLORS))
    _verbose_print(f'color selected randomly: {color_name}')
    return color_name


def _is_rgb(text):
    if RgbValue.is_valid(text):
        return RgbValue(text)
    else:
        raise argparse.ArgumentTypeError(
            f'invalid rgb value {text}, should be rgb(0-255,0-255,0-255)')


def _parse_raw_text_for_color(text):
    color_name = None
    if text in TabColor.COLORS:
        color_name = text
    rgb_value = None
    if RgbValue.is_valid(text):
        rgb_value = RgbValue(text)
    return color_name, rgb_value


def _read_color_name_from_stdin():
    # the user is piping the information in...
    text = sys.stdin.readline().strip().lower()
    return _parse_raw_text_for_color(text)


def _read_color_from_path(file_path):
    lines = file_path.read_text().splitlines()
    if len(lines) == 0:
        return None, None
    line = lines[0].strip()
    return _parse_raw_text_for_color(line)


def _find_color_name_elsewhere():
    color_name = rgb_value = None

    file_paths = [
        Path(os.path.expandvars('$HOME/settings/zsh/color.zsh')).resolve(),
        Path(os.path.expandvars('$HOME/settings/bash/.bash_color')).resolve()
    ]

    if not os.isatty(sys.stdin.fileno()):
        color_name, rgb_value = _read_color_name_from_stdin()

    for file_path in file_paths:
        if color_name or rgb_value:
            break
        if not file_path.is_file():
            continue
        color_name, rgb_value = _read_color_from_path(file_path)
    return color_name, rgb_value


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Set the mac OS iterm tab color')
    parser.add_argument('-v',
                        '--verbose',
                        action="store_true",
                        help='increase output verbosity')
    parser.add_argument(
        '--rgb',
        type=_is_rgb,
        required=False,
        help='tab color specified by the form of rgb(0-255, 0-255, 0-255)')
    parser.add_argument('-r', '--random', action="store_true", help='use a random color instead of specifying one')
    parser.add_argument('color',
                        const='blank',
                        nargs='?',
                        choices=TabColor.COLORS.keys(),
                        help=f'one of {", ".join(TabColor.COLORS.keys())}')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose
    color_name = args.color
    rgb_value = args.rgb
    select_random_color = args.random

    # if not --rgb and no color as program arg it may be <stdin>, also try various default files
    if not color_name and not rgb_value and not select_random_color:
        color_name, rgb_value = _find_color_name_elsewhere()

    # if still no color then just choose one randomly
    if select_random_color and not color_name and not rgb_value:
        color_name = _select_random_color_name()

    if not color_name and not rgb_value:
        raise parser.error('a valid color name or rgb value was not specified')
    if color_name and rgb_value:
        raise parser.error('only one color name or rgb value can be specified at a time')

    _verbose_print(f'Args, verbose: {_VERBOSE}, random: {select_random_color}, color: {color_name}, rgb: {rgb_value}')
    return TabColor(color_name, rgb_value)


# Previous versions contain various attempts at trying to call the operating system to
#  change the tab color in iTerm2.
def _call_subprocess_run(cmd):
    try:
        _verbose_print(f'INFO: command: {cmd}')
        run(shlex.split(cmd),
            shell=False,
            check=True,
            env=os.environ,
            stdin=None,
            stdout=None,
            stderr=None)
        return True
    except CalledProcessError as err:
        print(f'ERROR: {err.returncode} calling {cmd}')
        return False
    except SubprocessError as err:
        print(f'ERROR: {err} subprocess run error calling {cmd}')
        return False


def _call_echo_command(color_str):
    cmd = f'printf {color_str}'
    _call_subprocess_run(cmd)


def set_tab_color(tab_color):
    _verbose_print(f'INFO: setting tab color to {tab_color}')
    _call_echo_command(tab_color.encode())


def main():
    tab_color = _parse_args()
    try:
        set_tab_color(tab_color)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type,
                                  exc_value,
                                  exc_traceback,
                                  file=sys.stdout)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

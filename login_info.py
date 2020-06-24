#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from ansimarkup import AnsiMarkup, parse
import argparse
import datetime
import os
import platform
import pprint
import psutil
from psutil._common import bytes2human
import re
import shlex
import subprocess
import sys
import traceback

import location_info
import network_info
from network_info import NetworkInfo, NetworkInfos, SystemInfo
import weather_info


user_tags = {
    'info'        : parse('<bold><green>'),    # bold green
    'error'       : parse('<bold><red>'),      # bold red
    'mail'        : parse('<blink><red>'),     # bliink red
    'label'       : parse('<bold><cyan>'),     # bold cyan
    'value'       : parse('<reset>'),          # white
    'sysinfo'     : parse('<bold><yellow>'),   # bold yellow
    'quote'       : parse('<bold><cyan>'),     # bold cyan
    'location'    : parse('<bold><cyan>'),     # bold cyan
    'weather'     : parse('<reset>'),          # white
    'greeting'    : parse('<bold><green>'),    # bold green
    'loginout'    : parse('<bold><green>'),    # bold green
    'apt'         : parse('<bold><yellow>'),   # bold yellow
    'reboot'      : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

MORNING_EMOJI   = '🌤'
AFTERNOON_EMOJI = '🌎'
EVENING_EMOJI   = '🌖'
NIGHT_EMOJI     = '🌙'

# Morning from 5am - 12pm
MORNING_HOUR=5
# Afternoon from 12pm - 6pm
AFTERNOON_HOUR=12
# Evening from 6pm - 11pm
EVENING_HOUR=18
# Night from 11pm - 4am
NIGHT_HOUR=23

MORNING_LABEL = 'morning'
AFTERNOON_LABEL = 'afternoon'
EVENING_LABEL = 'evening'
NIGHT_LABEL = 'night'

TIME_OF_DAY_LABELS = {MORNING_HOUR   : MORNING_LABEL,
                      AFTERNOON_HOUR : AFTERNOON_LABEL,
                      EVENING_HOUR   : EVENING_LABEL,
                      NIGHT_HOUR     : NIGHT_LABEL}
TIME_OF_DAY = {'morning'   : MORNING_EMOJI,
               'afternoon' : AFTERNOON_EMOJI,
               'evening'   : EVENING_EMOJI,
               'night'     : NIGHT_EMOJI}

COLUMN_LH_WIDTH_1 = 15
COLUMN_RH_WIDTH_1 = 20
COLUMN_LH_WIDTH_2 = 25
COLUMN_RH_WIDTH_2 = 14

_VERBOSE = False

def _verbose_print(msg):
    if _VERBOSE:
        am.ansiprint(f'<info>INFO: {msg}</info>', file=sys.stdout)

def _error_print(msg):
    am.ansiprint(f'<error>ERROR: {msg}</error>', file=sys.stderr)

def _assert_message(msg):
    return am.ansistring(f'<error>ASSERT: {msg}</assert>')

def _print_time_of_daygreeting(message):
    am.ansiprint(f'<greeting>{message}</greeting>\n')

def _print_system_info_time(sys_info):
    am.ansiprint(f'  <sysinfo>{sys_info}</sysinfo>\n')

def _print_columns(label1, value1, label2, value2):
    label1 = label1 + ':' if len(label1) > 0 else label1
    label2 = label2 + ':' if len(label2) > 0 else label2
    col1_lh = am.ansistring(f'<label>{label1}</label>')
    col1_rh = am.ansistring(f'<value>{value1}</value>')
    col2_lh = am.ansistring(f'<label>{label2}</label>')
    col2_rh = am.ansistring(f'<value>{value2}</value>')
    lh_width1 = COLUMN_LH_WIDTH_1 + col1_lh.delta
    rh_width1 = COLUMN_RH_WIDTH_1 + col1_rh.delta
    lh_width2 = COLUMN_LH_WIDTH_2 + col2_lh.delta
    rh_width2 = COLUMN_RH_WIDTH_2 + col2_rh.delta
    print(f'  {col1_lh:{lh_width1}} {col1_rh:{rh_width1}}   {col2_lh:{lh_width2}} {col2_rh:{rh_width2}}')

def _print_boot_time(boot_time):
    lh = am.ansistring('<label>Boot Time:</label>')
    rh = am.ansistring(f'<value>{boot_time}</value>')
    lh_width = COLUMN_LH_WIDTH_1 + lh.delta
    rh_width = COLUMN_RH_WIDTH_1 + rh.delta
    print(f'  {lh:{lh_width}} {rh:{rh_width}}\n')

def _print_last_login(values):
    assert len(values) >= 1, _assert_message('last login message must be at least one line long')
    rhs = []
    rhs_widths = []
    for value in values:
        if value.startswith('Log in:'):
            s = am.ansistring(f'<loginout>Log in:<loginout> <value>{value[len("Log in: "):]}</value>')
        elif value.startswith('Log out:'):
            s = am.ansistring(f'<loginout>Log out:<loginout> <value>{value[len("Log out: "):]}</value>')
        else:
            s = am.ansistring(f'<value>{value}</value>')
        rhs_widths.append(COLUMN_RH_WIDTH_1 + s.delta)
        rhs.append(s)
    lh = am.ansistring('<label>Last Login:</label>')
    lh_width = COLUMN_LH_WIDTH_1 + lh.delta
    for index, (rh, rh_width) in enumerate(zip(rhs, rhs_widths)):
        if index == 0:
            print(f'  {lh:{lh_width}} {rh:{rh_width}}')
        else:
            print(f'                  {rh:{rh_width}}')

def _print_weather(location, weather):
    location = location + ':' if len(location) > 0 else location
    lh = am.ansistring(f'<location>{location}</location>')
    rh = am.ansistring(f'<weather>{weather}</weather>')
    lh_width = COLUMN_LH_WIDTH_1 + lh.delta
    rh_width = COLUMN_RH_WIDTH_1 + rh.delta
    print(f'  {lh:{lh_width}} {rh:{rh_width}}')

def _print_quote(quote):
    if quote and len(quote) > 0:
        am.ansiprint(f'\n<quote>{quote}</quote>')

def _print_packages_available(message):
    if message:
        am.ansiprint(f'\n<apt>{message}</apt>')

def _print_reboot_required(message):
    if message:
        am.ansiprint(f'\n<reboot>{message}</reboot>')

def _get_timezone_info():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

def _get_now():
    return datetime.datetime.now(_get_timezone_info())

def _convert_yearless_timestamp(timestamp):
    dt = datetime.datetime.strptime(timestamp, "%a %b %d %H:%M")
    tz = _get_timezone_info()
    now = datetime.datetime.now(tz)
    year = now.year if dt.month <= now.month else now.year - 1
    return dt.replace(year=year, tzinfo=tz)

def _convert_time_duration(dt, hour, minute):
    delta = datetime.delta(minutes=minute, hours=hour)
    return dt + delta

def _convert_date_time(dt):
    return '{:%d-%b-%Y %I:%M:%S%p %Z}'.format(dt).replace('AM', 'am').replace('PM', 'pm')

def _run_external_command(cmd):
    args = shlex.split(cmd)
    process = subprocess.Popen(args, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.wait() != 0:
        _error_print(error)
        return None
    return output

class MacOsVersionNames:
    def __init__(self):
        self._platform_names = {10.11 : 'Mac OS X', 10.15 : 'macOS 10', 11.0 : 'macOS 11',}
        self._version_names = {10.0 : 'Cheetah', 10.1 : 'Puma', 10.2 : 'Jaguar', 10.3 : 'Panther', \
                               10.4 : 'Tiger', 10.5 : 'Leopard', 10.6 : 'Snow Leopard', 10.7 : 'Lion', \
                               10.8 : 'Mountain Lion', 10.9 : 'Mavericks', 10.10 : 'Yosemite', \
                               10.11 : 'El Capitan', 10.12 : 'Sierra', 10.13 : 'High Sierra', \
                               10.14 : 'Mojave', 10.15 : 'Catalina', 11.0 : 'Big Sur',}

    def _get_platform_name(self, version):
        for max_version, platform_name in self._platform_names.items():
            if version <= max_version:
                return platform_name
        return 'macOS'

    def _get_version_name(self, version):
        return self._version_names[version] if version in self._version_names else 'Unknown'

    def get_version(self, version):
        return f'{self._get_platform_name(version)} {self._get_version_name(version)}'

class MacOsVersionName:
    def __init__(self, version):
        # default version number to infinity == real large
        self._version = float('inf')
        if isinstance(version, float):
            self._version = version
        elif isinstance(version, int):
            self._version = float(version)
        elif isinstance(version, str):
            match = re.search(r'(?P<version_number>\d+(?:\.\d+)?)', version)
            if match:
                self._version = float(match.group('version_number'))

    def __str__(self):
        return MacOsVersionNames().get_version(self._version)

def _get_macosx_name():
    output = _run_external_command('sw_vers')
    assert output, _assert_message('sw_vers command did not return any information')
    version = build = None
    for line in output.splitlines():
        match = re.match('^ProductVersion:\s+(?P<product_version>.*)$', line)
        if match:
            version = match.group('product_version')
        match = re.match('^BuildVersion:\s+(?P<build_version>.*)$', line)
        if match:
            build = match.group('build_version')
    assert version and build, _assert_message('sw_vers is no longer giving the ProductVersion and BuildVersion')
    utsname = platform.uname()
    version_details = '({} {} {})'.format(utsname.system, utsname.release, utsname.machine)
    return '{} {}.{} {}'.format(MacOsVersionName(version), version, build, version_details)

def _get_linux_name():
    name = version = None
    with open('/etc/os-release') as release_info:
        text = release_info.read()
    for line in text.splitlines():
        match = re.match(r'^PRETTY_NAME="(?P<name>[^\"]+)"$', line.strip())
        if match:
            name = match.group('name')
        match = re.match(r'^UBUNTU_CODENAME=(?P<ver>[^\s]+)$', line.strip())
        if match:
            version = match.group('ver')
    if not name:
        name = 'Linux'
    utsname = platform.uname()
    version_details = '(GNU/{} {} {})'.format(utsname.system, utsname.release, utsname.machine)
    if not version:
        return '{} {}'.format(name, version_details)
    else:
        return '{} {} {}'.format(name, version, version_details)

def _get_os_name():
    return _get_macosx_name() if sys.platform == 'darwin' else _get_linux_name()

def _get_packages_available():
    if sys.platform == 'darwin':
        return ''
    updates_available = '/var/lib/update-notifier/updates-available'
    if os.path.isfile(updates_available) and os.access(updates_available, os.R_OK):
        with open(updates_available) as updates_available_file:
            return updates_available_file.read().strip()

def _get_time_of_day():
    hour = _get_now().hour
    if hour >= NIGHT_HOUR or hour < MORNING_HOUR:
        return NIGHT_LABEL
    elif hour >= EVENING_HOUR:
        return EVENING_LABEL
    elif hour >= AFTERNOON_HOUR:
        return AFTERNOON_LABEL
    else:
        assert hour >= MORNING_HOUR and hour < AFTERNOON_HOUR, _assert_message('hour "{}" is out of the 0-23 range').format(hour)
        return MORNING_LABEL

def _get_time_of_day_greeting():
    label = _get_time_of_day()
    assert label in TIME_OF_DAY, _assert_message('unknown label "{}" found for time of day'.format(label))
    os_name = _get_os_name()
    assert os_name, _assert_message('unable to retrieve the operating system version details')
    return 'Good {} {} and welcome to {}'.format(label, TIME_OF_DAY[label], os_name)

def _get_time_of_day_emoji():
    label = _get_time_of_day()
    assert label in TIME_OF_DAY, _assert_message('unknown label "{}" found for time of day'.format(label))
    return TIME_OF_DAY[label]

def _get_load_average():
    load_average = psutil.getloadavg()[0]
    return '{:.2%}'.format(load_average / 100.0)

def _get_process_count():
    return str(len(psutil.pids()))

def _get_root_partition_usage():
    partitions = [partition for partition in psutil.disk_partitions() if partition.mountpoint == '/']
    assert len(partitions) == 1, _assert_message('found {} partitions with the "/" mount point', len(partitions))
    partition = partitions[0]
    usage = psutil.disk_usage(partition.mountpoint)
    total_amount = bytes2human(usage.total)
    used_percent = '{:.1%}'.format(usage.percent / 100.0)
    return '{} of {}'.format(used_percent, total_amount)

def _get_user_count():
    return str(len(psutil.users()))

def _get_virtual_memory_usage():
    virtual_memory = psutil.virtual_memory()
    return '{:.0%}'.format(virtual_memory.percent / 100)

def _get_swap_memory_usage():
    swap_memory = psutil.swap_memory()
    return '{:.0%}'.format(swap_memory.percent / 100)

def _is_reboot_required():
    filename = '/var/run/reboot-required'
    if os.path.isfile(filename):
        with open(filename) as reboot_file:
            return reboot_file.readline().strip()
    return None

def _get_boot_time():
    boot_timestamp = psutil.boot_time()
    boot_time = datetime.datetime.fromtimestamp(boot_timestamp, _get_timezone_info())
    return '{:%a, %d-%b-%Y %I:%M:%S%p %Z}'.format(boot_time).replace('AM', 'am').replace('PM', 'pm')

def _get_system_information_time():
    now = _get_now()
    time_emoji = _get_time_of_day_emoji()
    prefix = 'System information as of'
    return '{0} {1:%a, %d-%b-%Y} {2} {1:%I:%M:%S%p %Z}'.format(prefix, now, time_emoji).replace('AM', 'am').replace('PM', 'pm')

def _get_macosx_available_mail():
    cmd = 'mailq'
    output = _run_external_command(cmd)
    assert output, _assert_message('mailq did not return any output')
    if output.strip() == 'Mail queue is empty':
        return 0
    else:
        return 1

def _get_linux_available_mail():
    cmd = r'pam_tally --file /var/mail/{0} --user {0}'.format(os.getlogin())
    output = _run_external_command(cmd)
    if not output:
        _verbose_print('pam_tally did not return any info -- possible /var/mail/{os.getlogin()} doesn\'t exist')
        return 0
    match = re.match(r'^User\s+{}\s*\(\d+\)\s*has\s*(?P<mail>\d+)$'.format(os.getlogin()), output.strip())
    assert match, _assert_message('definition of pam_tally output has changed')
    return int(match.group('mail'))

def _get_unopened_mail():
    mail_items = _get_macosx_available_mail() if sys.platform == 'darwin' else _get_linux_available_mail()
    if mail_items > 0:
        return am.ansistring(f'<mail>{mail_items}</mail> Unread Mail Items')
    else:
        return f'{mail_items} Unread Mail Items'

def _get_quote():
    quote = _run_external_command('fortune softwareengineering')
    return quote if quote and len(quote) > 1 else ''

def _get_last_login():
    output = _run_external_command('last')
    assert output, _assert_message('system command "last" did not return anything')
    for line in output.splitlines():
        line = line.strip()
        parts = line.split()
        # if the list of parts is not 9-10 items long
        if (9 <= len(parts) <= 10) == False:
            continue
        user = parts[0]
        terminal = parts[1]
        host = ''
        if len(parts) == 10:
            host = parts[2]
        login_time = _convert_yearless_timestamp(' '.join(parts[-7:-3]))
        login_time_str = _convert_date_time(login_time)
        if line.endswith('still logged in'):
            logout_time_str = 'still logged in'
        else:
            match = re.match('^(?P<hour>\d\d):(?P<minute>\d\d)$', parts[-2])
            assert match, _assert_message('the last command did not return the duration of the last login')
            hour = int(match.group('hour'))
            minute = int(match.group('minute'))
            logout_time_str = _convert_date_time(_convert_time_duration(login_time, hour, minute))
        last_login = []
        if host:
            last_login.append(f'{user} logged into {terminal} from {host}')
        else:
            last_login.append(f'{user} logged into {terminal}')
        last_login.append(f'Log in: {login_time_str}')
        last_login.append(f'Log out: {logout_time_str}')
        return last_login
    return []

def _get_weather_info():
    location = location_info.get_location()
    weather = weather_info.get_one_line_weather(location)
    if weather:
        index = weather.find(':')
        if index != -1:
            return weather[:index], weather[index + 2:]
        elif location:
            return location, weather
        else:
            return 'Lehi Utah US', weather
    elif location:
        return location, 'Unavailable'
    else:
        return 'Lehi Utah US', 'Unavailable'

def output_login_info():
    _print_time_of_daygreeting(_get_time_of_day_greeting())
    _print_system_info_time(_get_system_information_time())

    location, weather = _get_weather_info()
    _print_weather(location, weather)
    _print_last_login(_get_last_login())
    _print_boot_time(_get_boot_time())

    system_info = SystemInfo()
    _print_columns('Computer Name', system_info.computer_name, 'Hostname', system_info.hostname)
    _print_columns('Public IP', system_info.public_ip, 'Mail', _get_unopened_mail())
    _print_columns('System Load', _get_load_average(), 'Processes', _get_process_count())
    _print_columns('Usage of /', _get_root_partition_usage(), 'Users Logged In', _get_user_count())

    if len(system_info.network_infos) == 0:
        _print_columns('Memory Usage', _get_virtual_memory_usage(), '', '')
        _print_columns('Swap Usage', _get_swap_memory_usage(), '', '')
    for i, network_info in enumerate(system_info.network_infos):
        if i == 0:
            _print_columns('Memory Usage', _get_virtual_memory_usage(), f'IP address for {network_info.name}', network_info.ip)
            _print_columns('Swap Usage', _get_swap_memory_usage(), f'Mac address for {network_info.name}', network_info.mac)
        else:
            _print_columns('', '', f'IP address for {network_info.name}', network_info.ip)
            _print_columns('', '', f'Mac address for {network_info.name}', network_info.mac)

    _print_packages_available(_get_packages_available())
    _print_quote(_get_quote())
    _print_reboot_required(_is_reboot_required())

def _parse_args():
    parser = argparse.ArgumentParser(description='Replacement for standard Linux banner for both OS X and Linux')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

def main():
    _parse_args()
    try:
        output_login_info()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

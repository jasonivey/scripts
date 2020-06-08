#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

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
#from network_info import NetworkInfo
import weather_info

from ansimarkup import AnsiMarkup, parse

user_tags = {
    'info'        : parse('<bold><green>'),    # bold green
    'error'       : parse('<bold><red>'),      # bold red
    'mail'        : parse('<blink><red>'),     # bliink red
    'label'       : parse('<bold><cyan>'),     # bold cyan
    'value'       : parse('<reset>'),          # white
    'title'       : parse('<bold><yellow>'),   # bold yellow
    'quote'       : parse('<bold><cyan>'),     # bold cyan
    'location'    : parse('<bold><cyan>'),     # bold cyan
    'weather'     : parse('<reset>'),          # white
    'tod'         : parse('<bold><green>'),    # bold green
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


def _verbose_print(msg):
    am.ansiprint('<info>INFO: {}</info>'.format(msg), file=sys.stdout)

def _error_print(msg):
    am.ansiprint('<error>ERROR: {}</error>'.format(msg), file=sys.stderr)

def _assert_message(msg):
    return am.ansistring('<error>ASSERT: {}</assert>'.format(msg))

def _print_greeting(greeting):
    am.ansiprint('<tod>{}</tod>\n'.format(greeting))

def _print_title(title):
    am.ansiprint('  <title>{}</title>\n'.format(title))

#def _print_label_value(label=None, value=None, label_width=0):
#    if label and value and label_width > 0:
#        am.ansiprint(('<label>%-' + str(label_width) + 's:</label> <value>%s</value>') % (label, value))
#    elif value:
#        am.ansiprint('<value>{}</value>'.format(value))

COLUMN_LH_WIDTH_1 = 15
COLUMN_RH_WIDTH_1 = 20
COLUMN_LH_WIDTH_2 = 25
COLUMN_RH_WIDTH_2 = 14

def _print_column(label, value):
    label = label + ':' if len(label) > 0 else lebel
    lh = am.ansistring('<label>{}</label>'.format(label))
    rh = am.ansistring('<value>{}</value>'.format(value))
    lh_width = COLUMN_LH_WIDTH_1 + lh.delta
    rh_width = COLUMN_RH_WIDTH_1 + rh.delta
    print(f'  {lh:{lh_width}} {rh:{rh_width}}')

def _print_columns(label1, value1, label2, value2):
    label1 = label1 + ':' if len(label1) > 0 else label1
    label2 = label2 + ':' if len(label2) > 0 else label2
    col1_lh = am.ansistring('<label>{}</label>'.format(label1))
    col1_rh = am.ansistring('<value>{}</value>'.format(value1))
    col2_lh = am.ansistring('<label>{}</label>'.format(label2))
    col2_rh = am.ansistring('<value>{}</value>'.format(value2))
    lh_width1 = COLUMN_LH_WIDTH_1 + col1_lh.delta
    rh_width1 = COLUMN_RH_WIDTH_1 + col1_rh.delta
    lh_width2 = COLUMN_LH_WIDTH_2 + col2_lh.delta
    rh_width2 = COLUMN_RH_WIDTH_2 + col2_rh.delta
    print(f'  {col1_lh:{lh_width1}} {col1_rh:{rh_width1}}   {col2_lh:{lh_width2}} {col2_rh:{rh_width2}}')

def _print_weather(location, weather):
    location = location + ':' if len(location) > 0 else location 
    lh = am.ansistring('<location>{}</location>'.format(location + ':'))
    rh = am.ansistring('<weather>{}</weather>'.format(weather))
    lh_width = COLUMN_LH_WIDTH_1 + lh.delta
    rh_width = COLUMN_RH_WIDTH_1 + rh.delta
    print(f'  {lh:{lh_width}} {rh:{rh_width}}')

def _print_quote(quote):
    if quote and len(quote) > 0:
        am.ansiprint('\n<quote>{}</quote>'.format(quote))

def _print_packages_available(message):
    if message:
        am.ansiprint('\n<apt>{}</apt>'.format(message))

def _print_reboot_required(message):
    if message:
        am.ansiprint('\n<reboot>{}</reboot>'.format(message))

def _get_time_since(d, now=None):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: 'year' if n == 0 else 'years'),
      (60 * 60 * 24 * 30,  lambda n: 'month' if n == 0 else 'months'),
      (60 * 60 * 24 * 7,   lambda n: 'week' if n == 0 else 'weeks'),
      (60 * 60 * 24,       lambda n: 'day' if n == 0 else 'days'),
      (60 * 60,            lambda n: 'hour' if n == 0 else 'hours'),
      (60,                 lambda n: 'minute' if n == 0 else 'minutes')
    )
    assert isinstance(d, datetime.datetime), _assert_message('get time since must have a datetime argument')
    if not now:
        now = datetime.datetime.now() if not d.tzinfo else datetime.datetime.now(d.tzinfo)

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    assert since >= 0, _assert_message('get time since needs to work with a datetime older than now')
    if since == 0:
        return '0 minutes ago'
    s = ''
    remaining_seconds = 0
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            remaining_seconds = since - (seconds * count)
            s = '{number} {type}'.format(number=count, type=name(count))
            break
    if i + 1 < len(chunks):
        # Now get the second item
        seconds, name = chunks[i + 1]
        count = remaining_seconds // seconds
        if count != 0:
            s += ', {number} {type}'.format(number=count, type=name(count))
    return '{} ago'.format(s) if s else s

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
    process = subprocess.Popen(args, encoding='utf-8', shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.wait() != 0:
        _error_print(error)
        return None
    return output

def _get_macosx_name():
    license_filename = '/System/Library/CoreServices/Setup Assistant.app/Contents/Resources/en.lproj/OSXSoftwareLicense.rtf'
    assert os.path.isfile(license_filename), _assert_message('Mac OS X software license does not exist here {}'.format(license_filename))
    with open(license_filename) as license:
        text = license.read()
    match = re.search(r'SOFTWARE LICENSE AGREEMENT FOR\s+(?P<os_name>[^\\]*)', text)
    assert match, _assert_message('unable to find macOS name within OSXSoftwareLicense.rtf')
    mac_name = match.group('os_name')
    output = _run_external_command('sw_vers')
    version = build = None
    for line in output.split('\n'):
        match = re.match('^ProductVersion:\s+(?P<version>[^\n]+)$', line)
        if match:
            version = match.group('version')
        match = re.match('^BuildVersion:\s+(?P<version>[^\n]+)$', line)
        if match:
            build = match.group('version')
    assert version and build, _assert_message('os_vers is no longer giving the ProductVersion and BuildVersion')
    utsname = platform.uname()
    version_details = '({} {} {})'.format(utsname.system, utsname.release, utsname.machine)
    return '{} {}.{} {}'.format(mac_name, version, build, version_details)

def _get_linux_name():
    name = version = None
    with open('/etc/os-release') as release_info:
        text = release_info.read()
    for line in text.split('\n'):
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
    return total_amount, used_percent

def _get_root_partition_usage_str():
    total_amount, used_percent = _get_root_partition_usage()
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
    assert output, _assert_message('pam_tally did not return any output')
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

def get_tod_greeting():
    return _get_time_of_day_greeting()

def _get_last_login():
    output = _run_external_command('last')
    assert output, _assert_message('system command "last" did not return anything')
    last_login = None
    for line in output.split('\n'):
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
        if host:
            last_login = f'{user} logged into {terminal} from {host} login, {login_time_str} logout, {logout_time_str}'
        else:
            last_login = f'{user} logged into {terminal} login, {login_time_str} logout, {logout_time_str}'
        if last_login:
            break
    return last_login

def _get_weather_report():
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

def _get_network_infos():
    network_infos = network_info.get_networking_infos()
    ip_addresses = mac_addresses = []
    for net_info in network_infos:
        ip_addresses.append(('IP address for {}'.format(net_info.name), str(net_info.ip)))
        mac_addresses.append(('Mac address for {}'.format(net_info.name), net_info.mac))
    return ip_addresses, mac_addresses

def _get_hostname_computer_name():
    hostname = network_info.get_host_name()
    computer_name = network_info.get_computer_name()
    computer_name = computer_name if computer_name else hostname
    return hostname, computer_name

def get_login_info1():
    datetime_info = _get_current_time()
    last_login = _get_last_login()
    system_info = network_info.get_system_info()
    mail_info = _get_unopened_mail()
    return datetime_info + last_login + weather_report + system_info + mail_info

def _get_column_width(rows):
    # Add 1 for the colon
    left_side_width = max([len(row[0]) + 1 for row in rows])
    # Add 2 for the colon and space
    column_width = max([len(row[0]) + len(row[1]) + 2 for row in rows])
    return left_side_width, column_width

def output_login_info():
    login_infos = {}
    login_infos['Hostname'], login_infos['Computer Name'] = _get_hostname_computer_name()
    login_infos['Public IP'] = network_info.get_external_ip_address()
    login_infos['System Load'] = _get_load_average()
    login_infos['Processes'] = _get_process_count()
    login_infos['Usage of /'] = _get_root_partition_usage_str()
    login_infos['Users Logged In'] = _get_user_count()
    login_infos['Memory Usage'] = _get_virtual_memory_usage()
    login_infos['Swap Usage'] = _get_swap_memory_usage()

    _print_greeting(get_tod_greeting())
    _print_title(_get_system_information_time())

    location, weather = _get_weather_report()
    _print_weather(location, weather)
    _print_column('Last Login', _get_last_login())
    _print_column('Boot Time', _get_boot_time() + '\n')

    _print_columns('Computer Name', login_infos['Computer Name'], 'Hostname', login_infos['Hostname'])
    _print_columns('Public IP', login_infos['Public IP'], 'Mail', _get_unopened_mail())
    _print_columns('System Load', login_infos['System Load'], 'Processes', login_infos['Processes'])
    _print_columns('Usage of /', login_infos['Usage of /'], 'Users Logged In', login_infos['Users Logged In'])
    net_infos = network_info.get_networking_infos()
    assert len(net_infos) > 0
    name = net_infos[0].name if not 'USB 10/100/1000 LAN' else 'LAN'
    _print_columns('Memory Usage', login_infos['Memory Usage'], 'IP address for {}'.format(name), str(net_infos[0].ip))
    _print_columns('Swap Usage', login_infos['Swap Usage'], 'Mac address for {}'.format(name), net_infos[0].mac)
    for net_info in net_infos[1:]:
        name = net_infos[0].name if not 'USB 10/100/1000 LAN' else 'LAN'
        _print_columns('', '', 'IP address for {}'.format(name), str(net_info.ip))
        _print_columns('', '', 'Mac address for {}'.format(name), net_info.mac)

    _print_packages_available(_get_packages_available())
    _print_quote(_get_quote())
    _print_reboot_required(_is_reboot_required())

def main():
    try:
        output_login_info()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

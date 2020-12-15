#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
import argparse
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
from shutil import which
import sys
import traceback
from ansimarkup import AnsiMarkup, parse

_VERBOSE_OUTPUT = False

_DATE_CONVERSION_FMT = '%Y-%m-%d'

_COMMANDS_STATS = 'stats'
_COMMANDS_SHOW = 'show'
_COMMANDS_CREATE = 'create'
_COMMANDS_ADD = 'add'
_COMMANDS_UPDATE = 'update'
_WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',]

user_tags = {
    'info': parse('<bold><green>'),
    'error': parse('<bold><red>'),
    'text': parse('<bold><white>'),
    'output': parse('<bold><cyan>'),
    'arg': parse('<bold><yellow>'),}

am = AnsiMarkup(tags=user_tags)


def _print_info(msg):
    if _VERBOSE_OUTPUT:
        am.ansiprint(f'<info>INFO:</info> <text>{msg}</text>')


def _print_error(msg):
    am.ansiprint(f'<error>ERROR:</error> <text>{msg}</text>')


def _format_arg_name_value(name, value, eol=True):
    return am.ansistring(f'<arg>{name}:</arg> <text>{value}</text>') + ('\n' if eol else '')


def _format_name_value(name, value, eol=True):
    return am.ansistring(f'<output>{name}:</output> <text>{value}</text>') + ('\n' if eol else '')


def _format_text(msg, eol=True):
    return am.ansistring(f'<text>{msg}</text>') + ('\n' if eol else '')


def _to_date(value):
    return datetime.strptime(value, _DATE_CONVERSION_FMT).date()


def _from_date(value, include_weekday=False):
    date_str = f'{value:{_DATE_CONVERSION_FMT}}'
    return date_str + (f' ({_WEEKDAYS[value.weekday()]})' if include_weekday else '')


def _is_date(date_str):
    try:
        if date_str.lower() == 'today':
            return date.today()
        elif date_str.lower() == 'yesterday':
            return date.today() - timedelta(days=1)
        elif date_str.lower() == 'tomorrow':
            return date.today() + timedelta(days=1)
        else:
            return _to_date(date_str)
    except Exception as ex:
        raise argparse.ArgumentTypeError('date value is invalid') from ex


def date_range(start_date, end_date):
    time_delta = end_date - start_date
    for day_count in range(time_delta.days):
        yield start_date + timedelta(days=day_count)


def create_graph(amounts):
    spark_path = which('spark')
    if not spark_path:
        return
    cmd = f'{spark_path} {" ".join(map(str, amounts))}'
    lolcat_path = which('lolcat')
    if lolcat_path:
        cmd += f' | {lolcat_path} -a -d 20 -s 5'
    os.system(cmd)


def _convert_arg(name, value):
    if isinstance(value, date):
        return _format_arg_name_value(f'{name}', f'{_from_date(value)}', eol=False)
    else:
        return _format_arg_name_value(f'{name}', f'{value}', eol=False)


def _print_args(commands):
    args = ''
    for command_name, value in commands.items():
        if isinstance(value, dict):
            values = [_convert_arg(name, val) for name, val in value.items()]
            args += _format_name_value(f'command {command_name}', '[{}]'.format(', '.join(values)), eol=True)
        else:
            args += _format_name_value(f'command {command_name}', value, eol=True)
    print(args)


def _parse_args():
    description = 'Medical prescription usage'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--file', required=True, help='file name of persistent data')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='output verbose debugging information')

    sub_parsers = parser.add_subparsers(help='commands', dest='command')
    sub_parsers.add_parser(_COMMANDS_STATS, help='report the stats of the medication')
    sub_parsers.add_parser(_COMMANDS_SHOW, help='dump the medication and usages')

    create = sub_parsers.add_parser(_COMMANDS_CREATE, help='create a new medication')
    create.add_argument('-n', '--name', required=True, help='name of the medication')
    create.add_argument('-c', '--count', required=True, type=int, help='total pills in medication')
    create.add_argument('-u', '--usage', required=True, type=int, help='daily pill usage')
    create.add_argument('-d', '--days', required=False, default=30, type=int,
                        help='total number of days in prescription')
    create.add_argument('-s', '--start_date', default=date.today(), type=_is_date, help='start date of medication')

    add = sub_parsers.add_parser(_COMMANDS_ADD, help='log a medication usage')
    add.add_argument('-a', '--amount', required=True, type=int, help='pill usage amount')
    add.add_argument('-d', '--date', default=date.today(), type=_is_date, help='date of the usage')

    update = sub_parsers.add_parser(_COMMANDS_UPDATE, help='update a medication usage')
    update.add_argument('-a', '--amount', required=True, type=int, help='pill usage amount')
    update.add_argument('-d', '--date', default=date.today(), type=_is_date, help='date of the usage')

    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = args.verbose

    commands = {
        _COMMANDS_STATS: args.command == 'stats',
        _COMMANDS_SHOW: args.command == 'show',
        _COMMANDS_CREATE: {},
        _COMMANDS_ADD: {},
        _COMMANDS_UPDATE: {}}

    if args.command == _COMMANDS_CREATE:
        commands[_COMMANDS_CREATE] = {'name': args.name,
                                      'count': args.count,
                                      'days': args.days,
                                      'daily_count': args.usage,
                                      'start_date': args.start_date}
    elif args.command == _COMMANDS_ADD:
        commands[_COMMANDS_ADD] = {'count': args.amount, 'date': args.date}
    elif args.command == _COMMANDS_UPDATE:
        commands[_COMMANDS_UPDATE] = {'count': args.amount, 'date': args.date}

    _print_args(commands)
    return commands, Path(args.file).resolve()


class MedicationUsage():
    def __init__(self, **kwargs):
        self._count = kwargs['count']
        self._date = kwargs['date']

    def serialize(self):
        obj = {}
        obj['count'] = self._count
        obj['date'] = _from_date(self._date, include_weekday=False)
        return obj

    @classmethod
    def deserialize(cls, obj):
        data = {'count': obj['count'], 'date': _to_date(obj['date'])}
        c = cls(**data)
        return c

    @property
    def count(self):
        return self._count

    def set_count(self, new_count):
        self._count = new_count

    @property
    def date(self):
        return self._date

    def __lt__(self, other):
        return self.date < other.date

    def __eq__(self, other):
        return self.date == other.date


class Medication(object):
    def __init__(self, **kwargs):
        self._name = kwargs['name']
        self._count = kwargs['count']
        self._days = kwargs['days']
        self._daily_count = kwargs['daily_count']
        self._start_date = kwargs['start_date']
        self._todays_date = date.today()
        self._usages = []
        self._dirty = False

    def create_usage_graph(self):
        amounts_used = []
        for curr_date in date_range(self.start_date, self.end_date):
            curr_usage = self.get_usage(curr_date)
            amounts_used.append(curr_usage.count if curr_usage else 0)
        create_graph(amounts_used)

    def stats(self):
        statss = ''
        statss += _format_name_value(f'{"name":<25}', self._name)
        statss += _format_name_value(f'{"todays date":<25}', _from_date(self.todays_date, include_weekday=True))
        statss += _format_name_value(f'{"start date":<25}', _from_date(self.start_date, include_weekday=True))
        statss += _format_name_value(f'{"end date":<25}', _from_date(self.end_date, include_weekday=True))
        statss += _format_name_value(f'{"end pill date":<25}', _from_date(self.actual_end_date, include_weekday=True))
        statss += _format_name_value(f'{"total days in RX":<25}', self.days)
        statss += _format_name_value(f'{"days elapsed":<25}', self.days_elapsed)
        statss += _format_name_value(f'{"days remaining":<25}', self.days_remaining)
        statss += _format_name_value(f'{"days of pills remaining":<25}', self.days_of_pills_remaining)
        statss += _format_name_value(f'{"total pill count":<25}', self.count)
        statss += _format_name_value(f'{"remaining pill count":<25}', self.current_count)
        statss += _format_name_value(f'{"pill amount per day":<25}', self.daily_count)
        statss += _format_name_value(f'{"pills used":<25}', self.used_count)
        statss += _format_name_value(f'{"pills needed":<25}', self.needed_count)
        statss += _format_name_value(f'{"pills in excess":<25}', self.excess_count)
        statss += _format_name_value(f'{"daily recovery count":<25}', f'{self.recovery_count:.2f}')
        return statss

    def update_date(self):
        if len(self.usages) > 0 and self.usages[-1].date > date.today():
            self._todays_date = self.usages[-1].date

    def add_usage(self, **kwargs):
        usage_date = kwargs['date']
        usage = self.get_usage(usage_date)
        if usage:
            _print_info(f'updating (instead of adding) the pill count since the usage '
                        f'{_from_date(usage_date)} already exists')
            self.update_usage(**kwargs)
            return
        new_medication = MedicationUsage(**kwargs)
        _print_info(f'adding {new_medication.count} pills to {_from_date(usage_date)}')
        self._usages.append(new_medication)
        self._usages = sorted(self._usages)
        self.update_date()
        self.set_dirty()

    def update_usage(self, **kwargs):
        usage_date = kwargs['date']
        usage = self.get_usage(usage_date)
        if not usage:
            _print_info(f'adding (instead of updating) the pill count since the usage '
                        f'{_from_date(usage_date)} does not exist')
            self.add_usage(**kwargs)
            return
        updated_count = usage.count + kwargs['count']
        _print_info(f'updating from {usage.count} pills to {updated_count} pills '
                    f'in the {_from_date(usage_date)} usage')
        usage.set_count(updated_count)
        self.update_date()
        self.set_dirty()

    def serialize(self):
        obj = {}
        obj['name'] = self._name
        obj['count'] = self._count
        obj['days'] = self._days
        obj['daily_count'] = self._daily_count
        obj['start_date'] = _from_date(self._start_date, include_weekday=False)
        obj['usages'] = []
        for usage in self._usages:
            obj['usages'].append(usage.serialize())
        return obj

    @classmethod
    def deserialize(cls, obj):
        data = {}
        data['name'] = obj['name']
        data['count'] = obj['count']
        data['days'] = obj['days'] if 'days' in obj else 30
        data['daily_count'] = obj['daily_count']
        data['start_date'] = _to_date(obj['start_date'])
        c = cls(**data)
        for obj_usage in obj['usages']:
            c._usages.append(MedicationUsage.deserialize(obj_usage))
        usages = c._usages
        c._usages = sorted(c._usages)
        if usages != c._usages:
            _print_info('serialized data was not sorted on disk')
            c.set_dirty()
        c.update_date()
        return c

    @property
    def name(self):
        return self._name

    @property
    def count(self):
        return self._count

    @property
    def days(self):
        return self._days

    @property
    def daily_count(self):
        return self._daily_count

    @property
    def current_count(self):
        return self.count - self.used_count

    @property
    def recovery_count(self):
        # avoid divide by zero errors
        if self.excess_count >= 0 or self.days_remaining == 0:
            return 0
        return float(self.current_count) / float(self.days_remaining)

    @property
    def used_count(self):
        return sum([usage.count for usage in self.usages], 0)

    @property
    def needed_count(self):
        return self.days_remaining * self.daily_count

    @property
    def excess_count(self):
        return self.current_count - self.needed_count

    @property
    def start_date(self):
        return self._start_date

    @property
    def todays_date(self):
        return self._todays_date

    @property
    def end_date(self):
        return self.start_date + timedelta(days=self.days)

    @property
    def actual_end_date(self):
        return self.todays_date + timedelta(days=self.days_of_pills_remaining)

    def get_usage(self, date_time):
        return next((usage for usage in self._usages if usage.date == date_time), None)

    @property
    def usages(self):
        return self._usages

    @property
    def days_elapsed(self):
        time_delta = self.todays_date - self.start_date
        elapsed_days = time_delta.days + 1
        return elapsed_days if elapsed_days <= self.days else self.days

    @property
    def days_remaining(self):
        time_delta = self.end_date - self.todays_date
        remaining_days = time_delta.days - 1
        return remaining_days if remaining_days >= 0 and remaining_days <= self.days else 0

    @property
    def days_of_pills_remaining(self):
        return 0 if self.daily_count == 0 else int(self.current_count / self.daily_count)

    @property
    def is_dirty(self):
        return self._dirty

    def set_dirty(self):
        self._dirty = True

    def __str__(self):
        s = _format_name_value(f'{"name":<12}', self.name)
        s += _format_name_value(f'{"count":<12}', self.current_count)
        s += _format_name_value(f'{"days":<12}', self.days)
        s += _format_name_value(f'{"total":<12}', self.count)
        s += _format_name_value(f'{"pills/day":<12}', self.daily_count)
        s += _format_name_value(f'{"start":<12}', _from_date(self.start_date, include_weekday=True))
        usage_count_width = max([len(str(usage.count)) + 1 for usage in self.usages])
        index_width = len(str(len(self.usages)))
        for i, usage in enumerate(self.usages, 1):
            usage_prefix = _format_text('{:>{}}. '.format(i, index_width), eol=False)
            usage_count = _format_name_value('count', '{:<{}}'.format(str(usage.count), usage_count_width), eol=False)
            usage_date = _format_name_value('date', _from_date(usage.date, include_weekday=True))
            s += f'{usage_prefix} {usage_count} {usage_date}'
        return s


def _load_data(file_path):
    if not file_path.is_file():
        error_str = f'unable to deserialize data from {file_path} since it doesn\'t exist'
        _print_error(error_str)
        raise Exception(error_str)

    text = file_path.read_text()
    _print_info(f'deserializing data from {file_path}')
    return Medication.deserialize(json.loads(text))


def _create_database(**kwargs):
    medication = Medication(**kwargs)
    medication.set_dirty()
    return medication


def _unload_data(file_path, medication):
    if not medication.is_dirty:
        _print_info(f'not serializing since data hasn\'t been modified {file_path}')
        return
    _print_info(f'writing serialized data to {file_path}')
    file_path.write_text(json.dumps(medication.serialize(), sort_keys=True, indent=4, separators=(',', ': ')))


def main():
    commands, file_path = _parse_args()

    try:
        if len(commands[_COMMANDS_CREATE]) > 0:
            medication = _create_database(**commands[_COMMANDS_CREATE])
        else:
            medication = _load_data(file_path)

        if len(commands[_COMMANDS_ADD]) > 0:
            medication.add_usage(**commands[_COMMANDS_ADD])
        if len(commands[_COMMANDS_UPDATE]) > 0:
            medication.update_usage(**commands[_COMMANDS_UPDATE])
        elif commands[_COMMANDS_STATS]:
            print(medication.stats())
            medication.create_usage_graph()
        elif commands[_COMMANDS_SHOW]:
            print(medication)
            medication.create_usage_graph()

        _unload_data(file_path, medication)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

from __future__ import print_function
from functools import total_ordering
import argparse
import datetime
import json
import os
import sys
import traceback

_VERBOSE_OUTPUT = False

_DATE_CONVERSION_FMT = '%Y-%m-%d'

_COMMANDS_STATS = 'stats'
_COMMANDS_SHOW  = 'show'
_COMMANDS_CREATE = 'create'
_COMMANDS_ADD = 'add'
_COMMANDS_UPDATE = 'update'

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _to_date(value):
    return datetime.datetime.strptime(value, _DATE_CONVERSION_FMT).date()

def _from_date(value, include_weekday=False):
    if not include_weekday:
        fmt_str = '{0:' + _DATE_CONVERSION_FMT + '}'
        return fmt_str.format(value)
    else:
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fmt_str = '{0:' + _DATE_CONVERSION_FMT + '} ({1})'
        return fmt_str.format(value, weekdays[value.weekday()])

def _is_date(date_str):
    try:
        if date_str.lower() == 'today':
            return datetime.date.today()
        elif date_str.lower() == 'yesterday':
            return datetime.date.today() - datetime.timedelta(days=1)
        elif date_str.lower() == 'tomorrow':
            return datetime.date.today() + datetime.timedelta(days=1)
        else:
            return _to_date(date_str)
    except:
        raise argparse.ArgumentTypeError('date value is invalid')

def _print_args(commands):
    for key, value in commands.items():
        if isinstance(value, dict):
            values = ''
            for subkey, subvalue in value.items():
                if isinstance(subvalue, datetime.date):
                    values += '{0}: {1}, '.format(subkey, _from_date(subvalue, True))
                else:
                    values += '{0}: {1}, '.format(subkey, subvalue)
            print('command {0}: [{1}]'.format(key, values.rstrip(' ,')))
        else:
            print('command {0}: {1}'.format(key, value))

def _parse_args():
    description = 'Medical prescription usage'
    parser = argparse.ArgumentParser(description=description)

    sub_parsers = parser.add_subparsers(help='commands', dest='command')

    stats = sub_parsers.add_parser(_COMMANDS_STATS, help='report the stats of the medication')

    show = sub_parsers.add_parser(_COMMANDS_SHOW, help='dump the medication and usages')

    create = sub_parsers.add_parser(_COMMANDS_CREATE, help='create a new medication')
    create.add_argument('-n', '--name', required=True, help='name of the medication')
    create.add_argument('-c', '--count', required=True, metavar='<NUMBER>', type=int, help='total pills in medication')
    create.add_argument('-u', '--usage', required=True, metavar='<NUMBER>', type=int, help='daily pill usage')
    create.add_argument('-d', '--days', required=False, metavar='<NUMBER>', default=30, type=int, help='total number of days in prescription')
    create.add_argument('-s', '--start_date', metavar='<YYYY-MM-DD>', default=datetime.date.today(), type=_is_date, help='start date of medication')

    add = sub_parsers.add_parser(_COMMANDS_ADD, help='log a medication usage')
    add.add_argument('-a', '--amount', required=True, metavar='<NUMBER>', type=int, help='pill usage amount')
    add.add_argument('-d', '--date', metavar='<YYYY-MM-DD>', default=datetime.date.today(), type=_is_date, help='date of the usage')

    update = sub_parsers.add_parser(_COMMANDS_UPDATE, help='update a medication usage')
    update.add_argument('-a', '--amount', required=True, metavar='<NUMBER>', type=int, help='pill usage amount')
    update.add_argument('-d', '--date', metavar='<YYYY-MM-DD>', default=datetime.date.today(), type=_is_date, help='date of the usage')

    parser.add_argument('-f', '--file', required=True, help='file name of persistent data')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='output verbose debugging information')

    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = args.verbose

    commands = {_COMMANDS_STATS: args.command == 'stats', 
                _COMMANDS_SHOW: args.command == 'show',
                _COMMANDS_CREATE: {},
                _COMMANDS_ADD: {},
                _COMMANDS_UPDATE: {}}

    if args.command == _COMMANDS_CREATE:
        commands[_COMMANDS_CREATE] = {'name':args.name, 'count':args.count, 'days': args.days, 'daily_count':args.usage, 'start_date':args.start_date}
    elif args.command == _COMMANDS_ADD:
        commands[_COMMANDS_ADD] = {'count':args.amount, 'date':args.date}
    elif args.command == _COMMANDS_UPDATE:
        commands[_COMMANDS_UPDATE] = {'count':args.amount, 'date':args.date}

    if _is_verbose_output_enabled():
        _print_args(commands)

    return commands, args.file


class MedicationUsage(object):
    def __init__(self,  **kwargs):
        self._count = kwargs['count']
        self._date = kwargs['date']

    def serialize(self):
        obj = {}
        obj['count'] = self._count
        obj['date'] = _from_date(self._date, False)
        return obj

    @classmethod
    def deserialize(cls, obj):
        data = {'count':obj['count'], 'date':_to_date(obj['date'])}
        c = cls(**data)
        return c

    @property
    def date(self):
        return self._date

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        self._count = value

    @property
    def date(self):
        return self._date

    def __cmp__(self, other):
        return cmp(self.date, other.date)

    def __lt__(self, other):
        return self.date < other.date

    def __eq__(self, other):
        return self.date == other.date

    def __str__(self):
        return 'count: {0}, date: {1}'.format(self.count, _from_date(self.date, True))


class Medication(object):
    def __init__(self, **kwargs):
        self._name = kwargs['name']
        self._count = kwargs['count']
        self._days = kwargs['days']
        self._daily_count = kwargs['daily_count']
        self._start_date = kwargs['start_date']
        self._todays_date = datetime.date.today()
        self._usages = []
        self._dirty = False
    
    def report_stats(self):
        print('name:                    {0}'.format(self.name))
        print('today\'s date:            {0}'.format(_from_date(self.todays_date, True)))
        print('start date:              {0}'.format(_from_date(self.start_date, True)))
        print('end date:                {0}'.format(_from_date(self.end_date, True)))
        print('end pill date:           {0}'.format(_from_date(self.actual_end_date, True)))

        print('total days in RX:        {0}'.format(self.days))
        print('days elapsed:            {0}'.format(self.days_elapsed))
        print('days remaining:          {0}'.format(self.days_remaining))
        print('days of pills remaining: {0}'.format(self.days_of_pills_remaining))

        print('total pill count:        {0}'.format(self.count))
        print('remaining pill count:    {0}'.format(self.current_count))
        print('pill amount per day:     {0}'.format(self.daily_count))
        print('pills used:              {0}'.format(self.used_count))
        print('pills needed:            {0}'.format(self.needed_count))
        print('pills in excess:         {0}'.format(self.excess_count))
        print('daily recovery count:    {0:.2f}'.format(self.recovery_count))

    def update_date(self):
        if len(self.usages) > 0 and self.usages[-1].date > datetime.date.today():
            self._todays_date = self.usages[-1].date

    def add_usage(self, **kwargs):
        new_medication = MedicationUsage(**kwargs)
        for existing_usage in self.usages:
            if existing_usage.date == new_medication.date:
                print('EROR: the usage on {0} has already been added'.format(_from_date(existing_usage.date, True)))
                return
        if _is_verbose_output_enabled():
            print('INFO: adding {0} pills used on {1}'.format(new_medication.count, _from_date(new_medication.date, True)))
        self.usages.append(new_medication)
        self.usages.sort()
        self.update_date()
        self.dirty = True

    def update_usage(self, **kwargs):
        new_medication = MedicationUsage(**kwargs)
        for existing_usage in self.usages:
            if existing_usage.date == new_medication.date:
                if _is_verbose_output_enabled():
                    print('INFO: updating the usage on {0} to be {1} pills used'.format(_from_date(existing_usage.date, True), new_medication.count))
                existing_usage.count = new_medication.count
                self.update_date()
                self.dirty = True
                return
        if _is_verbose_output_enabled():
            print('ERROR: usage for {0} is not found'.format(_from_date(new_medication.date, True)))

    def serialize(self):
        obj = {}
        obj['name'] = self._name
        obj['count'] = self._count
        obj['days'] = self._days
        obj['daily_count'] = self._daily_count
        obj['start_date'] = _from_date(self._start_date, False)
        obj['usages'] = []
        for usage in self._usages:
            obj['usages'].append(usage.serialize())
        return obj

    @classmethod
    def deserialize(cls, obj):
        data = {'name':obj['name'], 'count':obj['count'], 'daily_count':obj['daily_count'], 'start_date':_to_date(obj['start_date'])}
        data['days'] = obj['days'] if obj.has_key('days') else 30
        c = cls(**data)
        for obj_usage in obj['usages']:
            c.usages.append(MedicationUsage.deserialize(obj_usage))
        usages = c.usages
        c.usages.sort()
        c.dirty = usages != c.usages
        c.update_date()
        if c.dirty and _is_verbose_output_enabled():
            print('INFO: serialized data was not sorted on disk')
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
        return 0 if self.excess_count >= 0 else float(self.current_count) / float(self.days_remaining)

    @property
    def used_count(self):
        count = 0
        for usage in self.usages:
            count += usage.count
        return count

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
        return self.start_date + datetime.timedelta(days=self.days)

    @property
    def actual_end_date(self):
        return self.todays_date + datetime.timedelta(days=self.days_of_pills_remaining)

    @property
    def usages(self):
        return self._usages

    @property
    def days_elapsed(self):
        elapsed = (self.todays_date - self.start_date).days + 1
        return elapsed if elapsed <= self.days else self.days

    @property
    def days_remaining(self):
        remaining = (self.end_date - self.todays_date).days - 1
        return remaining if remaining >= 0 and remaining <= self.days else 0

    @property
    def days_of_pills_remaining(self):
        return int(self.current_count / self.daily_count)

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def __str__(self):
        s =  'name:      {0}\n'.format(self.name)
        s += 'count:     {0}\n'.format(self.current_count)
        s += 'days:      {0}\n'.format(self.days)
        s += 'total:     {0}\n'.format(self.count)
        s += 'pills/day: {0}\n'.format(self.daily_count)
        s += 'start:     {0}\n'.format(_from_date(self.start_date, True))
        for i, usage in enumerate(self.usages):
            s += '{0:-2}. {1}\n'.format(i + 1, usage)
        return s


def _load_data(filename):
    with open(filename, 'r') as file:
        if _is_verbose_output_enabled():
            print('INFO: deserializing data from {0}'.format(filename))
        return Medication.deserialize(json.loads(file.read()))

def _create_database(**kwargs):
    medication = Medication(**kwargs)
    medication.dirty = True
    return medication

def _unload_data(filename, medication):
    if not medication.dirty:
        if _is_verbose_output_enabled():
            print('INFO: not serializing identical data to disk {0}'.format(filename))
        return
    with open(filename, 'w') as file:
        if _is_verbose_output_enabled():
            print('INFO: writing the data to {0}'.format(filename))
        file.write(json.dumps(medication.serialize(), sort_keys=True, indent=4, separators=(',', ': ')))

def main():
    commands, filename = _parse_args()

    try:
        if len(commands[_COMMANDS_CREATE]) > 0:
            medication = _create_database(**commands[_COMMANDS_CREATE])
        else:
            medication = _load_data(filename)

        if len(commands[_COMMANDS_ADD]) > 0:
            medication.add_usage(**commands[_COMMANDS_ADD])
        if len(commands[_COMMANDS_UPDATE]) > 0:
            medication.update_usage(**commands[_COMMANDS_UPDATE])
        elif commands[_COMMANDS_STATS]:
            medication.report_stats()
        elif commands[_COMMANDS_SHOW]:
            print(medication)

        _unload_data(filename, medication)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

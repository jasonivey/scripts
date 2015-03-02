from __future__ import print_function
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

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _to_date(value):
    return datetime.datetime.strptime(value, _DATE_CONVERSION_FMT).date()

def _from_date(value):
    fmt_str = '{0:' + _DATE_CONVERSION_FMT + '}'
    return fmt_str.format(value)

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

def _parse_args():
    description = 'Medical perscription usage'
    parser = argparse.ArgumentParser(description=description)
    sub_parsers = parser.add_subparsers(help='commands', dest='command')
    stats = sub_parsers.add_parser(_COMMANDS_STATS, help='report the stats of the medication')
    show = sub_parsers.add_parser(_COMMANDS_SHOW, help='dump the medication and usages')
    create = sub_parsers.add_parser(_COMMANDS_CREATE, help='create a new medication')
    create.add_argument('-n', '--name', required=True, help='name of the medication')
    create.add_argument('-c', '--count', required=True, metavar='<NUMBER>', type=int, help='total pills in medication')
    create.add_argument('-u', '--usage', required=True, metavar='<NUMBER>', type=int, help='daily pill usage')
    create.add_argument('-s', '--start_date', required=True, metavar='<YYYY-MM-DD>', type=_is_date, help='start date of the medication')
    new_usage = sub_parsers.add_parser(_COMMANDS_ADD, help='log a medication usage')
    new_usage.add_argument('-a', '--amount', required=True, metavar='<NUMBER>', type=int, help='pill usage amount')
    new_usage.add_argument('-d', '--date', metavar='<YYYY-MM-DD>', default=datetime.date.today(), type=_is_date, help='date of the usage')
    parser.add_argument('-f', '--file', required=True, help='file name of persistent data')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='output verbose debugging information')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = args.verbose
    commands = {}
    commands[_COMMANDS_STATS] = args.command == 'stats' 
    commands[_COMMANDS_SHOW] = args.command == 'show'
    commands[_COMMANDS_CREATE] = {}
    commands[_COMMANDS_ADD] = {}
    if args.command == 'create':
        commands['create'] = {'name':args.name, 'count':args.count, 'daily_count':args.usage, 'start_date':args.start_date}
    elif args.command == 'add':
        commands['add'] = {'count':args.amount, 'date':args.date}
    return commands, args.file

class MedicationUsage(object):
    def __init__(self,  **kwargs):
        self._count = kwargs['count']
        self._date = kwargs['date']
    
    def serialize(self):
        obj = {}
        obj['count'] = self._count
        obj['date'] = _from_date(self._date)
        return obj

    @classmethod
    def deserialize(cls, obj):
        data = {'count':obj['count'], 'date':_to_date(obj['date'])}
        c = cls(**data)
        return c
    
    @property
    def count(self):
        return self._count
    
    @property
    def date(self):
        return self._date

    def __cmp__(self, other):
        return cmp(self._date, other._date)

    def __str__(self):
        return 'count: {0}, date: {1}'.format(self.count, _from_date(self.date))


class Medication(object):
    def __init__(self, **kwargs):
        self._name = kwargs['name']
        self._count = kwargs['count']
        self._daily_count = kwargs['daily_count']
        self._start_date = kwargs['start_date']
        self._usages = []
    
    def report_stats(self):
        pill_count = self.current_count
        days = (datetime.date.today() - self._start_date).days
        day_count = 30 - days 
        pills_used = self.count - pill_count
        pills_needed = day_count * self.daily_count
        pill_excess = pill_count - pills_needed
        pill_num_days = (pill_count / self.daily_count)
        pill_end_date = datetime.date.today() + datetime.timedelta(days=pill_num_days)
        print('name:             {0}'.format(self.name))
        print('count:            {0}'.format(self.count))
        print('daily count:      {0}'.format(self.daily_count))
        print('start date:       {0}'.format(self.start_date))
        print('end date:         {0}'.format(self.start_date + datetime.timedelta(days=30)))
        print('pill count:       {0}'.format(pill_count))
        print('days:             {0}'.format(days))
        print('day count:        {0}'.format(day_count))
        print('pills used:       {0}'.format(pills_used))
        print('pills needed:     {0}'.format(pills_needed))
        print('pills in excess:  {0}'.format(pill_excess))
        print('pills last until: {0}'.format(_from_date(pill_end_date)))

    def add_usage(self, **kwargs):
        medication_usage = MedicationUsage(**kwargs)
        for usage in self._usages:
            if _from_date(usage.date) == _from_date(medication_usage.date):
                print('EROR: The usage has already been added')
                return
        if _is_verbose_output_enabled():
            print('adding {0} pills used on {1}'.format(medication_usage.count, medication_usage.date))
        self._usages.append(medication_usage)
        self._usages.sort()

    def serialize(self):
        obj = {}
        obj['name'] = self._name
        obj['count'] = self._count
        obj['daily_count'] = self._daily_count
        obj['start_date'] = _from_date(self._start_date)
        obj['usages'] = []
        for usage in self._usages:
            obj['usages'].append(usage.serialize())
        return obj

    @classmethod
    def deserialize(cls, obj):
        data = {'name':obj['name'], 'count':obj['count'], 'daily_count':obj['daily_count'], 'start_date':_to_date(obj['start_date'])}
        c = cls(**data)
        for obj_usage in obj['usages']:
            c.usages.append(MedicationUsage.deserialize(obj_usage))
        return c
    
    @property
    def name(self):
        return self._name

    @property
    def count(self):
        return self._count

    @property
    def daily_count(self):
        return self._daily_count

    @property
    def start_date(self):
        return self._start_date
    
    @property
    def usages(self):
        return self._usages

    @property
    def current_count(self):
        count = 0
        for usage in self._usages:
            count += usage.count
        return self.count - count

    def __str__(self):
        s =  'name:      {0}\n'.format(self.name)
        s += 'count:     {0}\n'.format(self.current_count)
        s += 'total:     {0}\n'.format(self.count)
        s += 'pills/day: {0}\n'.format(self.daily_count)
        s += 'start:     {0}\n'.format(_from_date(self.start_date))
        for i, usage in enumerate(self.usages):
            s += '{0:-2}. {1}\n'.format(i + 1, usage)
        return s


def _load_data(filename):
    with open(filename, 'r') as file:
        if _is_verbose_output_enabled():
            print('reading the data from {0}'.format(filename))
        return Medication.deserialize(json.loads(file.read()))

def _create_database(**kwargs):
    return Medication(**kwargs)

def _unload_data(filename, medication):
    with open(filename, 'w') as file:
        if _is_verbose_output_enabled():
            print('writing the data to {0}'.format(filename))
        file.write(json.dumps(medication.serialize(), sort_keys=True, indent=4, separators=(',', ': ')))

def main():
    commands, filename = _parse_args()

    if _is_verbose_output_enabled():
        for key, value in commands.items():
            if isinstance(value, dict):
                values = ''
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, datetime.date):
                        values += '{0}: {1}, '.format(subkey, _from_date(subvalue))
                    else:
                        values += '{0}: {1}, '.format(subkey, subvalue)
                print('command {0}: [{1}]'.format(key, values.rstrip(' ,')))
            else:
                print('command {0}: {1}'.format(key, value))

    try:
        if len(commands[_COMMANDS_CREATE]) > 0:
            medication = _create_database(**commands[_COMMANDS_CREATE])
        else:
            medication = _load_data(filename)

        if len(commands[_COMMANDS_ADD]) > 0:
            medication.add_usage(**commands['add'])
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

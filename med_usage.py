from __future__ import print_function
import argparse
import datetime
import json
import os
import sys
import traceback

_VERBOSE_OUTPUT = False

_DATE_CONVERSION_FMT = '%Y-%m-%d'

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

'''
{
   "name": "sample",
   "amount": 4,
}
'''

def _is_date(date_str):
    try:
        return _to_date(date_str)
    except:
        raise argparse.ArgumentTypeError('date value is invalid')

def _parse_args():
    description = 'Medical perscription usage'
    parser = argparse.ArgumentParser(description=description)
    sub_parsers = parser.add_subparsers()
    status = sub_parsers.add_parser('status', help='report the status of the medication')
    create = sub_parsers.add_parser('new', help='create a new medication')
    #create = parser.add_argument_group('create')
    create.add_argument('-n', '--name', required=True, help='name of the medication')
    create.add_argument('-c', '--count', required=True, metavar='<NUMBER>', type=int, help='total pills in medication')
    create.add_argument('-u', '--usage', required=True, metavar='<NUMBER>', type=int, help='daily pill usage')
    create.add_argument('-s', '--start_date', required=True, metavar='<YYYY-MM-DD>', type=_is_date, help='start date of the medication')
    #new_usage = parser.add_argument_group('new usage')
    new_usage = sub_parsers.add_parser('usage', help='log a medication usage')
    new_usage.add_argument('-a', '--amount', required=True, metavar='<NUMBER>', type=int, help='pill usage amount')
    new_usage.add_argument('-d', '--date', metavar='<YYYY-MM-DD>', default=datetime.datetime.today(), type=_is_date, help='date of the usage')
    parser.add_argument('-f', '--file', required=True, help='file name of persistent data')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='output verbose debugging information')
    args = parser.parse_args()
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = args.verbose
    if 'name' in dir(args):
        return args.name, args.count, args.usage, args.start_date, None, None, args.file
    elif 'amount' in dir(args):
        return None, None, None, None, args.amount, args.date, args.file
    else:
        return None, None, None, None, None, None, args.file

def _to_date(value):
    return datetime.datetime.strptime(value, _DATE_CONVERSION_FMT)

def _from_date(value):
    fmt_str = '{0:' + _DATE_CONVERSION_FMT + '}'
    return fmt_str.format(value)

class MedicationUsage(object):
    def __init__(self, count, date):
        self._count = count
        self._date = date
    
    def serialize(self):
        obj = {}
        obj['count'] = self._count
        obj['date'] = _from_date(self._date)
        return obj

    @classmethod
    def deserialize(cls, obj):
        c = cls(obj['count'], _to_date(obj['date']))
        return c
    
    @property
    def count(self):
        return self._count
    
    @property
    def date(self):
        return self._date

    def __cmp__(self, other):
        return cmp(self._date, other._date)


class Medication(object):
    def __init__(self, name, count, daily_count, start_date = datetime.datetime.today()):
        self._name = name
        self._count = count
        self._daily_count = daily_count
        self._start_date = start_date 
        self._usages = []

    def report_status(self):
        pill_count = self.current_count
        days = (datetime.datetime.today() - self._start_date).days
        day_count = 30 - days 
        pills_used = self.count - pill_count
        pills_needed = day_count * self.daily_count
        pill_excess = pill_count - pills_needed
        pill_num_days = (pill_count / self.daily_count)
        pill_end_date = datetime.datetime.now() + datetime.timedelta(days=pill_num_days)
        print('name:             {0}'.format(self.name))
        print('count:            {0}'.format(self.count))
        print('daily count:      {0}'.format(self.daily_count))
        print('start date:       {0}'.format(self.start_date.date()))
        print('end date:         {0}'.format(self.start_date.date() + datetime.timedelta(days=30)))
        print('pill count:       {0}'.format(pill_count))
        print('days:             {0}'.format(days))
        print('day count:        {0}'.format(day_count))
        print('pills used:       {0}'.format(pills_used))
        print('pills needed:     {0}'.format(pills_needed))
        print('pills in excess:  {0}'.format(pill_excess))
        print('pills last until: {0}'.format(_from_date(pill_end_date)))

    def add_usage(self, count, dt):
        for usage in self._usages:
            if _from_date(usage.date) == _from_date(dt):
                print('EROR: The usage has already been added')
                return
        self._usages.append(MedicationUsage(count, dt))
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
        c = cls(obj['name'],
                obj['count'],
                obj['daily_count'],
                _to_date(obj['start_date']))
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

def _load_database(filename):
    with open(filename, 'r') as file:
        if _is_verbose_output_enabled():
            print('reading the data from {0}'.format(filename))
        return Medication.deserialize(json.loads(file.read()))

def _load_data(med_name, total_count, daily_count, start_date, filename):
    if med_name:
        medication = Medication(med_name, total_count, daily_count, start_date)
    else:
        medication = _load_database(filename)
    return medication

def _unload_data(filename, medication):
    with open(filename, 'w') as file:
        if _is_verbose_output_enabled():
            print('writing the data to {0}'.format(filename))
        file.write(json.dumps(medication.serialize(), sort_keys=True, indent=4, separators=(',', ': ')))

def main():
    med_name, total_count, daily_count, start_date, usage_amount, usage_date, filename = _parse_args()

    if _is_verbose_output_enabled():
        print('name: {0}, count: {1}, daily: {2}, start: {3}, amount: {4}, date: {5}, file: {6}'.
            format(med_name, total_count, daily_count, start_date, usage_amount, usage_date, filename))
    
    try:
        if not med_name and not os.path.isfile(filename):
            print('Error: must create a medication before adding a new usage')
            return 1

        creating = med_name != None
        adding = usage_amount != None
        status = med_name == None and usage_amount == None

        medication = _load_data(med_name, total_count, daily_count, start_date, filename)
        if adding:
            medication.add_usage(usage_amount, usage_date)
        elif status:
            medication.report_status()
        _unload_data(filename, medication)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

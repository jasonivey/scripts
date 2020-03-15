#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import csv
import datetime
import sys
import traceback


SYMBOL_UNKNOWN = -1
SYMBOL_1 = 1
SYMBOL_2 = 2
SYMBOL_3 = 3

class StockData:
    def __init__(self, symbol, date, adj_close):
        self._symbol = self._convert_symbol(symbol)
        self._date = self._convert_date(date)
        self._adj_close = adj_close

    def _convert_symbol(self, raw_symbol):
        if raw_symbol == 'symbol1':
            return SYMBOL_1
        elif raw_symbol == 'symbol2':
            return SYMBOL_2
        elif raw_symbol == 'symbol3':
            return SYMBOL_3
        else:
            return SYMBOL_UNKNOWN

    def _convert_date(raw_date):
        return datetime.strptime(raw_date, '%Y/%m/%d')

    def __str__(self):
        return '%s - %s - %s'.format(self._symbol, self._date, self._adj_close)


class Stocks:
    def __init__(self):
        self._stocks = []

    def add_stock(symbol, date, adj_close):
        self._stocks.append(StockData(symbol, date, adj_close))


def _read_csv_file(file_name):
    with open(file_name) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        #csv_reader = csv.DictReader(csv_file)
        row_data = []
        for row_numer, row in enumerate(csv_reader):
            if row_number == 0:
                continue
            row_data.append((row[0], row[1], row[2]))


def main():
    location, full_report = _parse_args()
    try:
        weather = get_weather(location) if full_report else get_one_line_weather(location)
        if weather:
            print(weather)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())




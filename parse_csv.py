#!/usr/bin/env python3
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import csv
import datetime
import sys
import traceback
from collections import defaultdict

def _read_csv_file(file_name):
    stocks = defaultdict(list)
    with open(file_name) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        #csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            stocks[row[0]].append((datetime.datetime.strptime(row[1], '%m/%d/%Y'), float(row[2])))

    with open('stock_summary.txt', 'w') as output_file:
        for symbol in stocks.keys():
            print('{}\n{}'.format(symbol, '-' * len(symbol)))
            first_array_elem = stocks[symbol][0]
            min = first_array_elem[1]
            max = 0.0
            sum = 0.0
            for value in stocks[symbol]:
                # print(value)
                if value[1] < min:
                    min = value[1]
                if value[1] > max:
                    max = value[1]
                sum += value[1]
            print('Min: {:.4f}\nMax: {:.4f}\nAve: {:.4f}\n'.format(min, max, sum / len(stocks[symbol])))
            print('Min: {:.4f}\nMax: {:.4f}\nAve: {:.4f}\n'.format(min, max, sum / len(stocks[symbol])),
                    file=output_file)
            min = max = sum = 0.0

def main():
    try:
        _read_csv_file(sys.argv[1])
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0 

if __name__ == '__main__':
    sys.exit(main())


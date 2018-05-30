import csv
import os
import sys

def main():
    new_name = sys.argv[1] + '.tmp'
    with open(sys.argv[1], 'rb') as in_csvfile, open(new_name, 'wb') as out_csvfile:
        reader = csv.reader(in_csvfile, delimiter='\t')
        writer = csv.writer(out_csvfile, delimiter='\t')
        for i, row in enumerate(reader):
            row.append('a' * 16777214)
            writer.writerow(row)
            if i > 10:
                break
    return 0

if __name__ == '__main__':
    sys.exit(main())

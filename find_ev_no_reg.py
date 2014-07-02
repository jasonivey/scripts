#!/usr/bin/env python
import os
import sys
import re

if __name__ == '__main__':
    with open('\\files.py') as file:
        files = file.read().split('\n')
    
    #'EV(DOTNET)?BLDNOREG'
    #'EVBLDNOREG'
    output = open('\\out.txt', 'w')
    for filename in files:
        if len(filename.strip()) == 0 or filename.strip().startswith('#'):
            continue

        last_line_number = -1
        output.write('\nParsing %s\n' % filename)
        with open(os.path.join(os.getcwd(), filename)) as file:
            for match in re.finditer('EV(DOTNET)?BLDNOREG', file.read()):
                str = match.string
                start = str.rfind('\n', 0, match.start()) + 1 if str.rfind('\n', 0, match.start()) != -1 else 0
                end = str.find('\n', match.start()) if str.find('\n', match.start()) != -1 else len(str)
                str = str[start:end].replace('&#x0D;', '').replace('&#x0A;', '\n').replace('&quot;', '"').replace('&gt;', '>')
                line_number = str[:start].count('\n') + 1
                
                if line_number != last_line_number:
                    if line_number != last_line_number + 1:
                        output.write('--- Found ---\n(%d): %s\n' % (line_number, str))
                    else:
                        output.write('(%d): %s\n' % (line_number, str))
                    last_line_number = line_number

    output.close()
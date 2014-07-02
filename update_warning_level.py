import os
import sys
import re


def IsProjectFile(file):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcxproj$', file, re.I)

def FlushFile(filename, old_text, new_text):
    if old_text != new_text:
        print 'Updating %s' % filename
        with open(filename, 'w') as file:
            file.write(new_text)
    else:
        print 'Did not update %s' % filename
    
def AddIgnoreWarning(filename, warning_level):
    with open(filename, 'r') as file:
        text = file.read()

    new_text = None
    pattern = r'(\t*<DisableSpecificWarnings>)(?P<warning_numbers>(\d{4};)*\d{4}?)?(</DisableSpecificWarnings>)'
    if re.search(pattern, text):
        new_text = re.sub(pattern, r'\g<1>4127;4702;4063\g<4>', text)
    else:
        # Set multi-line on, match begin of string, some whitespace followed by warning level
        pattern = r'(?m)^(\s*)(<WarningLevel>Level\d</WarningLevel>)'
        # Add after the warning level, newline, some whitespace followed by disable specific warnings
        new_text = re.sub(pattern, r'\g<0>\n\g<1><DisableSpecificWarnings>4127;4702;4063</DisableSpecificWarnings>', text)

    FlushFile(filename, text, new_text)

def UpdateWarningLevel(filename, warning_level):
    with open(filename, 'r') as file:
        text = file.read()
    
    pattern = r'(\t*<WarningLevel>Level)[^%s](</WarningLevel>)' % warning_level
    regex = re.compile(pattern)
    replaced = regex.sub(r'\g<1>%s\g<2>' % warning_level, text)

    FlushFile(filename, text, replaced)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        warning_level = sys.argv[1]
    else:
        warning_level = '4'

    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            filename = os.path.join(root, file)
            if IsProjectFile(filename):
                UpdateWarningLevel(filename, warning_level)
                if warning_level is '4':
                    AddIgnoreWarning(filename, warning_level)

import sys, os, re

def ParseUnitTestLog(data, regex, verbose):
    callout = []

    regex = re.compile(regex, re.I | re.S)
    for match in regex.finditer(data):
        testname = match.group(1)[match.group('test_name').rfind('\\') + 1:]
        if verbose:
            print('Test: %s' % testname)
            print('\t%s' % match.group('first_summary'))
            print('\t%s\n\n' % match.group('second_summary'))

        if int(match.group('errors')) > 0 or \
            int(match.group('failures')) > 0 or \
            int(match.group('not_run')) > 0 or \
            int(match.group('invalid')) > 0 or \
            int(match.group('ignored')) > 0 or \
            int(match.group('skipped')) > 0:
            callout.append(testname)

    if len(callout) > 0:
        print('Errors/Failures/Not Run/Invalid/Ignored/Skipped:')
        for testname in callout:
            print('\t%s' % testname)


if __name__ == '__main__':
    # This regular expression makes a few assumptions:
    #  1. The name of the EXE is either NUnit-console.exe or NUnit-console-x86.exe
    #  2. The first line of output starts with "NUnit version {number}"
    #  3. The test summary is in the form:
    #     Tests run: {number}, Errors: {number}, Failures: {number}, Inconclusive: {number}, Time: {floating point number} seconds
    #     Not run: {number}, Invalid: {number}, Ignored: {number}, Skipped: {number}
    # As long as this stays consistent between the various versions of NUnit the regex should continue to work.
    
    preRegex = r'NUnit-console(?:-x86)?\.exe (?P<test_name>[^/]*) \/config=(?P=test_name)\.config\s*NUnit version \d'
    postRegex = r'(?P<first_summary>Tests run: (?P<tests_run>\d+), Errors: (?P<errors>\d+), Failures: (?P<failures>\d+), Inconclusive: (?P<inconclusive>\d+), Time: \d+\.\d+ seconds)\s*'
    postRegex += r'(?P<second_summary>Not run: (?P<not_run>\d+), Invalid: (?P<invalid>\d+), Ignored: (?P<ignored>\d+), Skipped: (?P<skipped>\d+))'
    regex = preRegex + '.*?' + postRegex

    verbose = False
    for arg in sys.argv[1:]:
        if arg.lower().startswith('-v'):
            verbose = True

    if len(sys.argv) == 1:
        data = sys.stdin.read()
    else:
        # The with statement only works in Python 2.6 and does an auto file close
        #with open(sys.argv[1]) as file:
        #    data = file.read()
        file = open(sys.argv[1])
        data = file.read()
        file.close()

    ParseUnitTestLog(data, regex, verbose)


import os, sys, re

class Results:

    def __init__(self):
        self.Severity = {}
        self.Severity['Success'] = 0x00000000
        self.Severity['Information'] = 0x40000000
        self.Severity['Warning'] = 0x80000000
        self.Severity['Error'] = 0xC0000000
        
        self.ResultCodeMask = 0x0000FFFF
        self.FacilityMask = 0x0FFF0000
        self.CustomerBit = 0x20000000
        
    def MakeResultCode(self, severity, facility, number):
        return self.Severity[severity] | self.CustomerBit | ( facility & 0xFFF ) << 16 | ( number & 0xFFFF )

if __name__ == '__main__':
    
    doubleQuote = r'"([^"\\]+|\\.)*"'
    regex = re.compile(doubleQuote, re.S | re.X )
    
    facilityPattern =   '''RESULT_FACILITY\s*\(
                            \s*(?P<facility>[^,]+),
                            \s*(?P<number>\d+),
                            #\s*"(?P<description>[^"]+)",
                            \s*(?P<description>''' + doubleQuote + ''')\s*,
                            \s*(?P<pool>\d+)\s*\)
                        '''
                            
    resultPattern =     '''RESULT\s*\(
                            \s*(?P<facility>[^,]+),
                            \s*(?P<severity>[^,]+),
                            \s*(?P<id>[^,]+),
                            \s*(?P<number>\d+),
                            #\s*"(?P<text>[^"]+)"\s*,
                            \s*(?P<text>''' + doubleQuote + ''')\s*,
                            #\s*"(?P<description>[^"]*)"\s*,
                            \s*(?P<description>''' + doubleQuote + ''')\s*,
                            \s*(?P<version>\d+)\s*\)
                        '''
                        
    stringFacilityPattern =     '''STRING_FACILITY\s*\(
                                    \s*(?P<facility>[^,]+),
                                    \s*(?P<number>\d+),
                                    \s*(?P<description>''' + doubleQuote + ''')\s*,
                                    \s*(?P<pool>\d+)\s*\)
                                '''

    stringPattern = '''STRING\s*\(
                        \s*(?P<facility>[^,]+),
                        \s*(?P<id>[^,]+),
                        \s*(?P<number>\d+),
                        \s*(?P<text>''' + doubleQuote + ''')\s*,
                        \s*(?P<description>''' + doubleQuote + ''')\s*,
                        \s*(?:DONT_)?TRANSLATE\s*,
                        \s*(?P<version>\d+)\s*,\s*\(0\)\s*\)
                    '''
                    
    facilityRegex = re.compile( facilityPattern, re.S | re.X )
    resultRegex = re.compile( resultPattern, re.S | re.X )
    
    stringFacilityRegex = re.compile( stringFacilityPattern, re.S | re.X )
    stringRegex = re.compile( stringPattern, re.S | re.X )
    
    #filename = 'd:/sandboxes/main/ws/base/dev/resultdefs.h'
    filename = 'd:/sandboxes/main/ws/base/dev/stringiddefs.h'
    file = open(filename, 'r')
    data = file.read()
    file.close()
    
    #match = facilityRegex.search(data)
    match = stringFacilityRegex.search(data)
    assert(match)
    print('Found facility: %s, %d, %s, %d' % ( match.group('facility'), int(match.group('number')), match.group('description'), int(match.group('pool')) ))
    
    facility = int(match.group('number'))
    results = Results()
    #for i in resultRegex.finditer(data):
    #    print 'Result: %s - %d' % ( i.group('id'), results.MakeResultCode( i.group('severity'), facility, int( i.group('number') ) ) )
    count = len( stringRegex.findall(data) )
    print('Found %d string definitions in the file' % count)
        
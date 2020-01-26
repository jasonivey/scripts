import os, sys, re
from .Utils import RecurseDirectory

def IsProjectFile(file):
    return not re.search('wsfiles', file, re.I) and re.match('^.*\.vcproj$', file, re.I)
 
if __name__ == '__main__':
    pattern = '\t+<(?:file)?configuration\s+name="(?P<Name>[^"]*)"\n(?:.*?)(?:</(?:file)?configuration>\n)'
    regex = re.compile(pattern, re.I |re.S )
    names = {}
    for file in RecurseDirectory( os.getcwd(), IsProjectFile, False ):
        f = open(file, 'r')
        data = f.read()
        f.close()
        for i in regex.finditer(data):
            name = i.group('Name').lower()
            if name in names:
                names[name] = names[name] + 1
            else:
                names[name] = 1
                
    for name, count in list(names.items()):
        print(('%10d : %s' % (count, name)))

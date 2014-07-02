import os, sys, datetime, re

def GetCreateDate(path, label):
    command = 'p4 fstat "%s/BuildNumber.txt@%s"' % (path, label)
    lines = os.popen4( command, 't' )[1].readlines()
    for line in lines:
        trimmedLine = line.lstrip(' .')
        index = trimmedLine.find(' ')
        if index != -1:
            name = trimmedLine[:index]
            value = trimmedLine[index + 1:]
            if name.lower() == 'headtime':
                return datetime.datetime.fromtimestamp(int(value))

    return datetime.datetime.max

def GetLabel(arg):
	if arg.isdigit():
		return 'BuildNumber_%s' % arg
	else:
		return arg

if __name__ == '__main__':
    regex = re.compile('//SEABU/ProductSource/(?P<Category>[^/]+)/(?P<Component>[^/]+)/(?P<Branch>[^/]+)/\.\.\.', re.I)
    view = None
    label = GetLabel(sys.argv[1])

    command = 'p4 label -o %s' % label
    lines = os.popen4( command, 't' )[1].readlines()
    for line in lines:
        sline = line.strip()
        if not sline.startswith('#'):
            print(sline)
        if sline.lower().startswith('//seabu/'):
            view = sline
            
    if not view:
        print('ERROR: Not a valid label.  No view specified!')
    else:
        match = regex.match(view)
        if not match:
            print('ERROR: Not a valid label.  The view was invalid (%s)!' % view)
        else:
            createDate = GetCreateDate(view[:-4], label)
            if createDate == datetime.datetime.max:
                print('ERROR: While trying to retrieve the labels creation date.')
            else:
                print('Created: %s' % createDate.strftime('%Y/%m/%d %H:%M:%S'))


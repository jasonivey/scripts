import os, sys, re, Utils

def ReadFile( filename ):
    file = open( filename, 'r' )
    data = file.read()
    file.close()
    return data
    
def IsHeaderFile( filename ):
    return filename.lower().endswith('.h')

if __name__ == '__main__':
    classes = []
    pattern = r'class\s+(?P<class_name>[^\s:]+)\s*(?P<inheritance>:)(?:\s*(?:public|private|protected)\s*([^\s,]+)\s*,?)+\s*{'
    regex = re.compile(pattern, re.S)
    
    loopCount = 0
    count = len(classes)
    classes.append('DiscoObject')
    while count != len(classes):
        loopCount += 1
        count = len(classes)
        for filename in Utils.RecurseDirectory( os.getcwd(), IsHeaderFile, False ):
            data = ReadFile(filename)
            for i in regex.finditer(data):
                class_name = i.group('class_name')
                
                # Early way to break out of this tedious loop
                if class_name in classes:
                    continue
                
                # Get the inheritance piece of the definition
                begin = i.span('inheritance')[1]
                end = i.end()
                definition = data[begin:end]
                for parent in classes:
                    if re.search('\\b%s\\b' % parent, definition) and class_name not in classes:
                        classes.append(class_name)
        
    print('Took %d times through the directory to find all the objects' % loopCount)
    print('All Disco Objects:')
    for i in range(1, len(classes)):
        print('\t%s' % classes[i])
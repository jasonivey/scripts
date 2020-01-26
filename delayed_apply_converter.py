import os, sys, string, math, re, Utils, codecs

class DelayedApply:
    def __init__(self, dir, data_or_filename):
        self.mSandbox = Utils.FindSandbox(dir)
        self.mSmeObjects = self.FindDiscoObjects()
        self.mSmeOperations = self.FindOperationObjects()
        self.mObjectMap = {}
        self.mOperations = []

        if os.path.isfile(data_or_filename):
            file = open(data_or_filename, 'rb')
            data = file.read()
            file.close()
        else:
            data = data_or_filename

        data = self.ConvertFile(data)
        self.Parse(data)
        print((str(self)))
        
    def ConvertFile(self, data):
        new_data = []
        for i in range(len(data)):
            if (i % 2) == 0:
                new_data.append(data[i])
        return ''.join(new_data)

    def Parse(self, data):
        lines = data.split('\n')
        count = len(lines)
        i = 0
        while i < count:
            # Search for operations first because they will also appear in the the object list
            if lines[i].strip() in  self.mSmeOperations:
                # catalog the operation parameters
                operation = lines[i].strip()
                i += 3
                owner = lines[i].strip()
                self.mOperations.append( [operation, owner] )
            elif lines[i].strip() in self.mSmeObjects:
                object = lines[i].strip()
                i += 1
                id = lines[i].strip()
                if object in list(self.mObjectMap.keys()):
                    if id not in self.mObjectMap[object]:
                        self.mObjectMap[object].append(id)
                else:
                    self.mObjectMap[object] = [id]
            i += 1
    
    def __str__(self):
        retval = 'Objects In Job\n'
        for object in list(self.mObjectMap.keys()):
            retval += '%s\n' % object
            for id in self.mObjectMap[object]:
                retval += '\t%s\n' % id
            retval += '\n'
                
        retval += '\nOperations in Job\n'
        for operation in self.mOperations:
            retval += '%s - %s\n\n' % (operation[0], operation[1])
            
        return retval

    
    def FindDiscoObjects(self):
        dir = os.path.join(self.mSandbox, 'ws', 'Sme', 'Dev')
        return FindClassObjects(dir, 'DiscoObject')

    def FindOperationObjects(self):
        dir = os.path.join(self.mSandbox, 'ws', 'Sme', 'Dev', 'Operation')
        return FindClassObjects(dir, 'Operation')


class ClassEntry:
    def __init__(self, class_name, declaration):
        self.mClassName = class_name
        self.mDeclaration = declaration
        self.mUsed = False
        
    def SetUsed(self):
        self.mUsed = True
        
    def HasBeenUsed(self):
        return self.mUsed
    
    def __cmp__(self, other):
        return cmp(self.mClassName, other.mClassName)


def FindClassObjects(dir, object_name):
    declarations = GetClassDeclarations(dir)
    objects = [object_name]
    previous = len(objects)
    searching = True
    while searching:
        for decl in declarations:
            if decl.HasBeenUsed():
                # Have we already searched and found something in this declaration line
                continue
            elif decl.mClassName in objects:
                # Is this class name a duplicate of another we have already found
                decl.SetUsed()
                continue
            
            for object in objects[:]:
                if decl.mDeclaration.find(object) != -1:
                    decl.SetUsed()
                    objects.append(decl.mClassName)
                    break

        count = len(objects)
        if count == previous:
            searching = False
        else:
            previous = count

    objects.sort()
    return objects


def GetClassDeclarations(dir):
    regex = re.compile( '^[^\w]*class\s+(?P<class_name>[\w]*)\s*:' )
    declarations = []
    for filename in Utils.RecurseDirectory(dir, IsHeaderFile, False):
        file = open(filename, 'r')
        for line in file.readlines():
            match = regex.match(line)
            if match:
                entry = ClassEntry(match.group('class_name'), line[match.end():].strip())
                declarations.append(entry)
        file.close()
    declarations.sort()
    return declarations


def IsHeaderFile(filename):
    return os.path.basename( os.path.dirname(filename) ).lower() != 'test' and filename.lower().endswith('.h')


if __name__ == '__main__':
    if len( sys.argv ) < 2:
        Utils.Error('The delayed apply file needs to be specified on the command line.')
        sys.exit(2)
    
    delayed_apply = DelayedApply(sys.argv[1])
    print((str(delayed_apply)))
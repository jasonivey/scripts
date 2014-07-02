import sys, os, re, win32con, win32api
import winreg as wreg

def RemoveFromCurrentUsersHive(str):
    subkey = r'Software\Microsoft\VisualStudio\8.0\Find'
    handle = GetSubKeyHandle(win32con.HKEY_CURRENT_USER, subkey, win32con.KEY_ALL_ACCESS)
    if not handle:
        return
    
    regex = re.compile(str, re.I)
    values = GetValues(handle, re.compile(r'query \d+', re.I))
    updatedValues = {}
    for value in list(values.keys()):
        if not regex.search(values[value]):
            updatedValues[value] = values[value]
    
    if len(list(values.keys())) != len(list(updatedValues.keys())):
        DeleteValues(handle, values)
        RecreateValues(handle, updatedValues)
    
def RemoveFromUsersHive(str):
    for key in GetKeys(win32con.HKEY_USERS):
        subkey = key + r'\Software\Microsoft\VisualStudio\8.0\Find'
        handle = GetSubKeyHandle(win32con.HKEY_USERS, subkey, win32con.KEY_ALL_ACCESS)
        if not handle:
            continue
        
        regex = re.compile(str, re.I)
        values = GetValues(handle, re.compile(r'query \d+', re.I))
        updatedValues = {}
        for value in list(values.keys()):
            if not regex.search(values[value]):
                updatedValues[value] = values[value]
        
        if len(list(values.keys())) != len(list(updatedValues.keys())):
            DeleteValues(handle, values)
            RecreateValues(handle, updatedValues)

def RecreateValues(handle, values):
    index = 0
    for value in list(values.keys()):
        wreg.SetValueEx(handle, 'Query %d' % index, 0, wreg.REG_SZ, values[value])
        index += 1

def DeleteValues(handle, values):
    for value in list(values.keys()):
        wreg.DeleteValue(handle, value)

def GetValues(handle, regex):
    index = 0
    values = {}
    while True:
        try:
            value = wreg.EnumValue(handle, index)
            name = value[0]
            if regex.search(name):
                assert( name not in list(values.keys()) )
                values[name] = value[1]
        except:
            break
        index += 1
    return values
        
def GetSubKeyHandle(hive, subkey, flags):
    handle = None
    try:
        handle = wreg.OpenKey(hive, subkey, 0, flags)
    except:
        pass
    return handle
        
def GetKeys(hive):
    keys = []
    index = 0
    while True:
        try:
            key = wreg.EnumKey(hive, index)
            keys.append(key)
        except:
            break
        index += 1
    return keys

    
if __name__ == '__main__':
    RemoveFromUsersHive('jason')
    RemoveFromCurrentUsersHive('jason')

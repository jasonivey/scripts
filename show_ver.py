from __future__ import print_function
import os, sys, re, codecs
from win32api import GetFileVersionInfo, GetLastError, LOWORD, HIWORD

# ----- VS_VERSION.dwFileFlags -----
VS_FF_DEBUG             = 0x00000001
VS_FF_PRERELEASE        = 0x00000002
VS_FF_PATCHED           = 0x00000004
VS_FF_PRIVATEBUILD      = 0x00000008
VS_FF_INFOINFERRED      = 0x00000010
VS_FF_SPECIALBUILD      = 0x00000020
VS_FF_KNOWNFLAGS        = VS_FF_DEBUG | \
                          VS_FF_PRERELEASE | \
                          VS_FF_PATCHED | \
                          VS_FF_PRIVATEBUILD | \
                          VS_FF_INFOINFERRED | \
                          VS_FF_SPECIALBUILD

# ----- VS_VERSION.dwFileOS -----
VOS_UNKNOWN             = 0x00000000
VOS_DOS                 = 0x00010000
VOS_OS216               = 0x00020000
VOS_OS232               = 0x00030000
VOS_NT                  = 0x00040000
VOS_WINCE               = 0x00050000
VOS__BASE               = 0x00000000
VOS__WINDOWS16          = 0x00000001
VOS__PM16               = 0x00000002
VOS__PM32               = 0x00000003
VOS__WINDOWS32          = 0x00000004
VOS_DOS_WINDOWS16       = 0x00010001
VOS_DOS_WINDOWS32       = 0x00010004
VOS_OS216_PM16          = 0x00020002
VOS_OS232_PM32          = 0x00030003
VOS_NT_WINDOWS32        = 0x00040004

# ----- VS_VERSION.dwFileType -----
VFT_UNKNOWN             = 0x00000000
VFT_APP                 = 0x00000001
VFT_DLL                 = 0x00000002
VFT_DRV                 = 0x00000003
VFT_FONT                = 0x00000004
VFT_VXD                 = 0x00000005
VFT_STATIC_LIB          = 0x00000007

# ----- VS_VERSION.dwFileSubtype -----
VFT2_UNKNOWN            = 0x00000000
VFT2_DRV_PRINTER        = 0x00000001
VFT2_DRV_KEYBOARD       = 0x00000002
VFT2_DRV_LANGUAGE       = 0x00000003
VFT2_DRV_DISPLAY        = 0x00000004
VFT2_DRV_MOUSE          = 0x00000005
VFT2_DRV_NETWORK        = 0x00000006
VFT2_DRV_SYSTEM         = 0x00000007
VFT2_DRV_INSTALLABLE    = 0x00000008
VFT2_DRV_SOUND          = 0x00000009
VFT2_DRV_COMM           = 0x0000000A
VFT2_DRV_INPUTMETHOD    = 0x0000000B
VFT2_DRV_VERSIONED_PRINTER = 0x0000000C    
VFT2_FONT_RASTER        = 0x00000001
VFT2_FONT_VECTOR        = 0x00000002
VFT2_FONT_TRUETYPE      = 0x00000003

def showFileFlags(flags):
    retval = ''
    
    if flags & ~VS_FF_KNOWNFLAGS:
        retval += '{0:#x}'.format(flags & ~VS_FF_KNOWNFLAGS)
    
    if flags & VS_FF_DEBUG:
        if len(retval):
            retval += ' | '
        retval += 'VS_FF_DEBUG'

    if flags & VS_FF_PRERELEASE:
        if len(retval):
            retval += ' | '
        retval += 'VS_FF_PRERELEASE'

    if flags & VS_FF_PATCHED:
        if len(retval):
            retval += ' | '
        retval += 'VS_FF_PATCHED'

    if flags & VS_FF_PRIVATEBUILD:
        if len(retval):
            retval += ' | '
        retval += 'VS_FF_PRIVATEBUILD'
        
    if flags & VS_FF_INFOINFERRED:
        if len(retval):
            retval += ' | '
        retval += 'VS_FF_INFOINFERRED'

    if flags & VS_FF_SPECIALBUILD:
        if len(retval):
            retval += ' | '
        retval += 'VS_FF_SPECIALBUILD'

    if len(retval) == 0:
        retval += 'UNKNOWN'
        
    return retval

def showFileOS(os):
    if os == VOS_UNKNOWN:
        return 'VOS_UNKNOWN'
    elif os == VOS_DOS:
        return 'VOS_DOS'
    elif os == VOS_OS216:
        return 'VOS_OS216'
    elif os == VOS_OS232:
        return 'VOS_OS232'
    elif os == VOS_NT:
        return 'VOS_NT'
    elif os == VOS__BASE:
        return 'VOS__BASE'
    elif os == VOS__WINDOWS16:
        return 'VOS__WINDOWS16'
    elif os == VOS__PM16:
        return 'VOS__PM16'
    elif os == VOS__PM32:
        return 'VOS__PM32'
    elif os == VOS__WINDOWS32:
        return 'VOS__WINDOWS32'
    elif os == VOS_DOS_WINDOWS16:
        return 'VOS_DOS_WINDOWS16'
    elif os == VOS_DOS_WINDOWS32:
        return 'VOS_DOS_WINDOWS32'
    elif os == VOS_OS216_PM16:
        return 'VOS_OS216_PM16'
    elif os == VOS_OS232_PM32:
        return 'VOS_OS232_PM32'
    elif os == VOS_NT_WINDOWS32:
        return 'VOS_NT_WINDOWS32'
    else:
        return 'Unknown FileOS'

def showFileType(type):
    if type == VFT_UNKNOWN:
        return 'VFT_UNKNOWN'
    elif type == VFT_APP:
        return 'VFT_APP'
    elif type == VFT_DLL:
        return 'VFT_DLL'
    elif type == VFT_DRV:
        return 'VFT_DRV'
    elif type == VFT_FONT:
        return 'VFT_FONT'
    elif type == VFT_VXD:
        return 'VFT_VXD'
    elif type == VFT_STATIC_LIB:
        return 'VFT_STATIC_LIB'
    else:
        return 'Unknown FileType'

def showFileSubtype(type, subtype):
    if type == VFT_DRV:
        if subtype == VFT2_UNKNOWN:
            return 'FileSubtype: VFT2_UNKNOWN'
        elif subtype == VFT2_DRV_PRINTER:
            return 'FileSubtype: VFT2_DRV_PRINTER'
        elif subtype == VFT2_DRV_KEYBOARD:
            return 'FileSubtype: VFT2_DRV_KEYBOARD'
        elif subtype == VFT2_DRV_LANGUAGE:
            return 'FileSubtype: VFT2_DRV_LANGUAGE'
        elif subtype == VFT2_DRV_DISPLAY:
            return 'FileSubtype: VFT2_DRV_DISPLAY'
        elif subtype == VFT2_DRV_MOUSE:
            return 'FileSubtype: VFT2_DRV_MOUSE'
        elif subtype == VFT2_DRV_NETWORK:
            return 'FileSubtype: VFT2_DRV_NETWORK'
        elif subtype == VFT2_DRV_SYSTEM:
            return 'FileSubtype: VFT2_DRV_SYSTEM'
        elif subtype == VFT2_DRV_INSTALLABLE:
            return 'FileSubtype: VFT2_DRV_INSTALLABLE'
        elif subtype == VFT2_DRV_SOUND:
            return 'FileSubtype: VFT2_DRV_SOUND'
        elif subtype == VFT2_DRV_COMM:
            return 'FileSubtype: VFT2_DRV_COMM'
        elif subtype == VFT2_DRV_INPUTMETHOD:
            return 'FileSubtype: VFT2_DRV_INPUTMETHOD'
        else:
            return 'Unknown FileSubtype: {0:x}'.format(subtype)
    elif type == VFT_FONT:
        if subtype == VFT2_FONT_RASTER:
            return 'FileSubtype: VFT2_FONT_RASTER'
        elif subtype == VFT2_FONT_VECTOR:
            return 'FileSubtype: VFT2_FONT_VECTOR'
        elif subtype == VFT2_FONT_TRUETYPE:
            return 'FileSubtype: VFT2_FONT_TRUETYPE'
        else:
            return 'Unknown FileSubtype: {0:x}'.format(subtype)
    elif subtype != 0:
        return ', FileSubtype: {0:x}'.format(subtype)
    else:
        return ''

def ToHex(val):
    if val < 0:
        return hex(val & 0xFFFFFFFF)[:-1]
    else:
        return '{0:08X}'.format(val)

def PrintStr(label, value):
    padding = ' ' * (16 - len(label))
    str = '  {0}:{1} {2}'.format(label, padding, value)
    try:
        print(str)
    except:
        print(re.sub(r'[\x80-\xff]', '*', str))

    
def PrintFileVersionInfo(name):
    if not os.path.exists(name):
        return
    
    print('VERSIONINFO for file "{0}": '.format(os.path.abspath(name)))
    versionStrings = ('Comments',
                   'InternalName',
                   'ProductName',
                   'CompanyName',
                   'LegalCopyright',
                   'ProductVersion',
                   'FileDescription',
                   'LegalTrademarks',
                   'PrivateBuild',
                   'FileVersion',
                   'OriginalFilename',
                   'SpecialBuild',)
    
    try:
        info = GetFileVersionInfo(name, "\\")
    except:
        print('ERROR ({0}): Unable to call GetFileVersionInfo because no version information exists.'.format(GetLastError()))
        sys.exit(0)
    
    PrintStr('Signature', '{0}'.format(ToHex(info['Signature'])))
    PrintStr('StrucVersion', '{0:d}.{1:d}'.format(HIWORD(info['StrucVersion']), LOWORD(info['StrucVersion'])))
    PrintStr('FileVersion', '{0:d}.{1:d}.{2:d}.{3:d}'.format(HIWORD(info['FileVersionMS']), LOWORD(info['FileVersionMS']), HIWORD(info['FileVersionLS']), LOWORD(info['FileVersionLS'])))
    PrintStr('ProductVersion', '{0:d}.{1:d}.{2:d}.{3:d}'.format(HIWORD(info['ProductVersionMS']), LOWORD(info['ProductVersionMS']), HIWORD(info['ProductVersionLS']), LOWORD(info['ProductVersionLS'])))
    if info['FileFlagsMask'] != 0:
        PrintStr('FileFlagsMask', '{0:#x}'.format(info['FileFlagsMask']))
    else:
        PrintStr('FileFlagsMask', '{0:#x}'.format(info['FileFlagsMask']))
    if info['FileFlags'] != 0:
        PrintStr('FileFlags', '{0:#04x} ({1})'.format(info['FileFlags'], showFileFlags(info['FileFlags'])))
    else:
        PrintStr('FileFlags', '{0:#04x}'.format(info['FileFlags']))
    PrintStr('FileOS', '{0}'.format(showFileOS(info['FileOS'])))
    PrintStr('FileType', '{0}{1}'.format(showFileType(info['FileType']), showFileSubtype(info['FileType'], info['FileSubtype'])))
    if info['FileDate']:
        PrintStr('FileDate', '{0:x}'.format(info['FileDate']))
    else:
        PrintStr('FileDate', 'Not Specified')

    pairs = GetFileVersionInfo(name, r'\VarFileInfo\Translation')
    for lang, codepage in pairs:
        #print 'lang: ', lang, 'codepage:', codepage
        for versionString in versionStrings:
            block = r'\StringFileInfo\{0:04X}{1:04X}\{2}'.format(lang, codepage, versionString)
            #print block
            try:
                info = GetFileVersionInfo(name, block)
            except:
                continue
            PrintStr(versionString, info)
    print('\n')

    
if __name__ == '__main__':
    #PrintFileVersionInfo(os.environ["COMSPEC"])
    for i in sys.argv[1:]:
        PrintFileVersionInfo(i)
    
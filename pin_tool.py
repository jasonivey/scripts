import os

def unpin( arg, directory, files ):
    prefix = os.path.basename( directory ).lower()
    if prefix.startswith( 'win32_' ) or prefix.startswith( 'linux_' ) \
               or prefix.startswith( 'win64_' ) or prefix.startswith( 'netware_' ):
        return
    directory = directory.replace( './', '$/Components/Sme/Hydra/' )
    directory += '/*.*'
    command = 'ss Unpin \"' + directory + '\" >> pintool.log'
    print 'Executing command: ' + command
    os.system( command )


if __name__ == '__main__':
    os.environ['SSDIR'] = 's:\\ss\\StorageManagementEngine'
    os.path.walk( '.', unpin, None )

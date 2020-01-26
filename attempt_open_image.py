import sys, os
from SmeApi import *

def CheckLocalResult(result, description):
    if not result.IsSuccess():
        print((GetStringFromResult(result)))
        WriteDebugLogToFile('d:\\out.log')
    return result.IsSuccess()


def OpenImage( filename ):
    try:
        sme = Session()
        sme.Open()
        print('here 1')
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Open'):
            return False
        print('here 1a')
        
        computer = sme.Select( SME_COMPUTER )
        print('here 2')
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Select Computer'):
            return False
        print('here 3')
        openImageOp = computer.GetOpenImage()
        print('here 4')
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Get Open Image'):
            return False
    
        print('here 4a')
        openImageOp.SetAllowMultiThreadingInCAN( False )
        openImageOp.SetPerformCRCChecks( False )
        openImageOp.SetAllowFileAccess( True )
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Set allow multi threading in can'):
            return False
        
        print(filename)
        openImageOp.SetFilename( filename )
        print('here 5')
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Set File Name'):
            return False
        
        openImageOp.Execute()
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Execute'):
            return False
        print('here 6')
        
        sme.Close()
        print('here 7')
        if not CheckLocalResult(sme.GetLastResult(), 'Sme Close'):
            return False
        return True
    except:
        print('Caught an exception')
        return False


if __name__ == '__main__':
    filename = sys.argv[1]
    tracerfile = os.path.join( os.path.dirname(filename), 'tracer.txt' )
    file = open(tracerfile, 'w')
    file.write('working\n')
    file.close()

    retval = OpenImage(filename)
    if retval:
        print(('Opening image %s SUCCEEDED, deleting tracer file.' % filename))
        os.remove(tracerfile)
        assert( not os.path.isfile(tracerfile) )
        sys.exit(0)
    else:
        print(('Opening image %s FAILED, deleting tracer file.' % filename))
        assert( os.path.isfile(tracerfile) )
        sys.exit(1)

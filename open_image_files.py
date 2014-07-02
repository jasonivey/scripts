import sys, os

def OpenImage( filename ):
    tracerfile = os.path.join( os.path.dirname(filename), 'tracer.txt' )
    if os.path.isfile(tracerfile):
        os.remove(tracerfile)
    lines = os.popen4( 'd:\\python\\python.exe AttemptOpenImage.py %s' % filename, 't' )[1].readlines()
    for line in lines:
        sys.stdout.write(line)
    if os.path.isfile(tracerfile):
        print('Opening image %s failed' % filename)
        return False
    else:
        print('Opening image %s succeeded' % filename)
        return True


def GetName(number):
    if number > 1000:
        return '%s_%04d.i%s' % ( name, number, ext )
    else:
        return '%s_%03d.i%s' % ( name, number, ext )
    
    
if __name__ == '__main__':
    name, ext = os.path.splitext(sys.argv[1])
    min = 1
    max = 1700
    last = 0
    next = (min + max) / 2
    succeeded = 0

    while min != max and last != next:
        filename = GetName(next)
        print('Attempting to open image %s' % filename)
        success = OpenImage(filename)
        last = next
        if success:
            succeeded = last
            min = last + 1
        else:
            max = last - 1
        next = (min + max) / 2
        if last == next:
            print('It appears that the last working value was \'%d\'' % succeeded)
            break

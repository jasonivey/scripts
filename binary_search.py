import os, sys

def GetInput(number):
    input = input('How About \'%d\'? (y/n): ' % number).lower()
    if input.startswith('q') or input.startswith('x'):
        sys.exit()
    elif input.startswith('y') or input.startswith('w'):
        return True
    else:
        return False

    
if __name__ == '__main__':
    min = int( eval(input('Min: ')) )
    max = int( eval(input('Max: ')) )
    last = 0
    next = (min + max) / 2
    succeeded = 0

    while min != max and last != next:
        success = GetInput( next )
        last = next
        if success:
            succeeded = last
            min = last + 1
        else:
            max = last - 1
        next = (min + max) / 2
        if last == next:
            print(('It appears that the last working value was \'%d\'' % succeeded))
            break
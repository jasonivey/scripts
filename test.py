#!/usr/bin/env python3
import os
import sys

# NOTE: table can either be a list like the following
table = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

# NOTE: or table can be a dictionary where the indexes are identical to the list (i.e. 0,1,2,3...)
#       to get a value out of either you simply use table[0] or print(table[15]) and prints 'F'
'''
table = {0: '0',
         1: '1',
         2: '2',
         3: '3',
         4: '4',
         5: '5',
         6: '6',
         7: '7',
         8: '8',
         9: '9',
         10: 'A',
         11: 'B',
         12: 'C',
         13: 'D',
         14: 'E',
         15: 'F'}
'''

def decimalToRep(num, base):
    # NOTE: changed rep from a space ' ' to just an empty string '' to be populated inside the while loop
    rep = ''
    # NOTE: special case, num cannot be a negative number and base has to be 2 or larger
    #       normally we would raise an Assertion but we aren't using the UnitTest module 
    #       which would make it easy to create a test which succeeds when an Assertion
    #       is raised.
    if num < 0 or base < 2:
        return rep
    print('\nstart num: {}, base: {}'.format(num, base))
    while num > 0:
        print('num: {}'.format(num))
        # NOTE: changed the remainder operator to be the modulus operator
        rem = num % base
        print('rem: {}'.format(rem))
        # NOTE: we are populating the rep string with indexing into the table what the modulus returned (i.e. 12 % base 10 == 2)
        rep = table[rem] + rep
        print('rep: {}'.format(rem))
        # NOTE: num is now decremented using the remainder operator
        num = num // base 
    print('end: {}'.format(rep))
    return rep

def main(args):
    assert decimalToRep(10, 10) == '10'
    assert decimalToRep(10, 8) == '12'
    assert decimalToRep(10, 2) == '1010'
    assert decimalToRep(10, 16) == 'A'
    # NOTE: For extra credit uncomment the following and make them pass
    assert decimalToRep(-1, 10) == ''
    assert decimalToRep(100, -1) == ''
    assert decimalToRep(100, 0) == ''
    assert decimalToRep(100, 1) == ''
    # NOTE: For extra-extra credit think of any other bounds (i.e. too large or too small) we aren't thinking of to test
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

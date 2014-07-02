#!/usr/bin/env python
import argparse
import os
import sys

#import Subversion

class Response(object):
    def __init__(self, all=False, default='n'):
        self._default = default.lower()
        self._all = all
        if not self._all:
            print('All prompts are defined [y/n/a] or yes/no/all case insensitive.')

    def _GetAnswer(self, prompt):
        answer = None
        while not answer:
            try:
                answer = raw_input('%s [y/n/a]? ' % prompt).strip().lower()
            except SyntaxError, EOFError:   # Forward compatibility. Python 3.0 throws exceptions when no input is given.
                answer = self._default
            if len(answer) == 0:
                answer = self._default      # The user choose the default <enter>
            elif answer.startswith('y') or answer.startswith('n') or answer.startswith('a'):
                answer = answer[:1]         # The user choose some form of 'y', 'n' or 'a'
            else:
                answer = None               # The user entered something but it isn't valid -- try again!
        return answer

    def GetResponse(self, prompt):
        if self._all:
            return True
        answer = self._GetAnswer(prompt)
        if answer.startswith('a') or answer.startswith('y'):
            self._all = answer.startswith('a')
            return True
        else:
            return False


def ParseArgs():
    desc = 'Clean a directory of all non-svn files\nPrompts'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-s', '--simulate', default=False, action='store_true')
    parser.add_argument('-q', '--quiet', default=False, action='store_true')
    parser.add_argument('-n', '--no-prompt', default=False, action='store_true')
    args = parser.parse_args()
    return args.simulate, args.quiet, args.no_prompt


def main(args):
    simulate, quiet, no_prompt = ParseArgs()
    
    SVN_DIR = r'.svn'
    
    print('Cleaning %s' % os.getcwd())
    response = Response(all=no_prompt, default='y')
    svn = Subversion.Subversion()
    
    for root, dirs, files in os.walk(os.getcwd(), False):
        if root.lower().find(SVN_DIR) != -1:
            continue
        for file in files:
            path = os.path.join(root, file)
            if path.lower().find(SVN_DIR) != -1:
                continue
            if not svn.IsFileInRepository(path) and response.GetResponse('DEL %s' % path):
                if not quiet:
                    print('DEL %s' % path)
                if not simulate:
                    os.remove(path)
        for dir in dirs:
            path = os.path.join(root, dir)
            if path.lower().find(SVN_DIR) != -1:
                continue
            in_repository = svn.IsFileInRepository(path)
            if not in_repository:
                if len(os.listdir(path)) != 0 and not simulate:
                    print('ERROR: Directory %s is not empty' % path)
                if response.GetResponse('RMDIR %s' % path):
                    if not quiet:
                        print('RMDIR %s' % path)
                    if not simulate:
                        os.rmdir(path)
    return 0

if __name__ == '__main__':
    sys.exit( main(sys.argv) )



#!/usr/bin/env python

import argparse
import os
import re
import sys
import shutil
import subprocess


def _copy_differences(perforce, src, dst):
	output = perforce.GetDifferences( src )
	name = os.path.splitext(dst)[0] + '.diff'
	file = open(name, 'w')
	file.write(output)
	file.close()


def _copy_opened_file( perforce, src, sandbox, dir, include_diff ):
    basename = os.path.basename( src )
    begin = src.find( sandbox ) + len( sandbox ) + 1
    if file[begin] == os.path.sep:
        begin += 1
    end = len( src ) - len( basename )
    dst = os.path.join( dir, file[begin:end] )
    MakeRecursiveDir( dst )                
    shutil.copy( src, dst )
    if include_diff:
        CopyDifferences(perforce, src, os.path.join(dst, basename))
    print('Copied %s to %s successfully' % ( src, dst ))


def _copy_file_to_workspace( perforce, src, dir, sandbox ):
    begin = src.find( dir ) + len( dir ) + 1
    dst = os.path.join( sandbox, src[begin:] )
    CHECK( os.path.exists( dst ), 'The source file, %s, must exist in the sandbox' % dst )
    #perforce.OpenForEdit( dst )
    CHECK( perforce.OpenForEdit( dst ), 'Error while opening the file, %s, for edit' % dst )
    shutil.copyfile( src, dst )
    print('Copied %s to %s successfully' % ( src, dst ))

def _get_opened_files(dir):
    process = subprocess.Popen('bzr sb stat', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, bufsize=1, cwd=dir)
    process.wait()
    output = process.stdout.read().strip()


def _find_sandbox_root(start_dir):
    dir = start_dir
    parent = os.path.abspath(os.path.join(dir, '..'))
    while parent != dir:
        if os.path.isfile(os.path.join(dir, 'sandbox.conf')):
            return dir
        else:
            dir = parent
        parent = os.path.abspath(os.path.join(dir, '..'))
    raise exceptions.RuntimeError('Unable to find the sandbox.conf file within {0}'.format(start_dir))

def _directory_or_parent_exists(dir):
	if not os.path.isdir(dir):
		if not os.path.isdir(os.path.dirname(dir)):
			msg = "{0} is not a valid directory".format(os.path.dirname(dir))
			raise argparse.ArgumentTypeError(msg)
	return os.path.normpath(os.path.abspath(dir))

def _directory_exists(dir):
    if not os.path.isdir(dir):
        msg = "{0} is not a valid directory".format(dir)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(dir))

def _parse_args():
	parser = argparse.ArgumentParser(description='Copy bazaar opened files')
	action_group = parser.add_mutually_exclusive_group(required=True)
	action_group.add_argument('-b', '--backup', metavar='directory', dest='backup', type=_directory_or_parent_exists, help='backup opened or new sandbox files')
	action_group.add_argument('-r', '--restore', metavar='directory', dest='restore', type=_directory_or_parent_exists, help='restore backed-up files to sandbox')
	parser.add_argument('-d', '--sandbox', metavar='directory', dest='sandbox', required=False, type=_directory_exists, help='sandbox directory')
	
	args = parser.parse_args()
	sandbox = _find_sandbox_root(os.getcwd()) if not args.sandbox else _find_sandbox_root(args.sandbox)
	return args.backup, args.restore, sandbox

def main():
	backup_directory, restore_directory, sandbox = _parse_args()
	print(backup, restore, sandbox)
	
	if backup:
		os.makedirs(backup_directory)

if __name__ == '__main__':
	main()
	
    #sandbox = FindSandbox( os.getcwd() )
    
    #if backup:
    #    CreateDestination( dir )
    #    if change:
    #        files = perforce.GetChangeListFiles( change, os.getcwd(), sandbox )
    #    else:
    #        files = perforce.GetOpenedFiles( os.getcwd(), sandbox )
    #    for file in files:
    #    #for file in RecurseDirectory( os.getcwd(), IsNotReadOnly ):
    #        if file.lower() not in exceptions:
    #            CopyOpenedFile( perforce, file, sandbox, dir, False )
    #            if revert:
    #                perforce.Revert(file)
    #else:
    #    for file in RecurseDirectory(dir):
    #        if not file.lower().endswith('.diff'):
    #            CopyFileToWorkspace( perforce, file, dir, sandbox )

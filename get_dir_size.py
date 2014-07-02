import os, sys, Utils

def ParseArgs(args):
	verbose = False
	dirs = []
	
	for arg in args:
		if Utils.IsSwitch(arg) and arg[1:].lower().startswith('v'):
			verbose = True
		elif os.path.isdir(arg):
			dirs.append(os.path.abspath(arg))
	
	if len(dirs) == 0:
		dirs.append(os.getcwd())
	
	return verbose, dirs
		
	
if __name__ == '__main__':
	verbose, initDirs = ParseArgs(sys.argv)
	totalSize = int(0)
	
	for dir in initDirs:
		for name in os.listdir(dir):
			if os.path.isdir(os.path.join(dir, name)):
				size = int(0)
				for root, dirs, files in os.walk( os.path.join(dir, name) ):
					for file in files:
						fname = os.path.join(root, file)
						try:
							size += os.path.getsize(fname)
						except (IOError, OSError) as inst:
							print('Exception raised: ', inst)
							pass	# I was occassionally getting a path too long OSError
				totalSize += size
				if verbose:
					print('\t%s Size: %s Bytes (%s MB)' % (name, Utils.Commafy(size), Utils.Commafy(size / int(1048576))))
			else:
				totalSize += int(os.path.getsize(os.path.join(dir, name)))
			
		print('%s Total Size: %s Bytes (%s MB)' % (dir,  Utils.Commafy(totalSize),  Utils.Commafy(totalSize / int(1048576))))
		
		
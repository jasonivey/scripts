import os, sys, Utils

def IsDebugLog(filename):
	return filename.lower().endswith('.dbg')
	

def ConvertDebugLog(filename):
	cdl = os.path.join('d:\\utils', 'ConvertDebugLog.exe')
	assert( os.path.exists( cdl ) )
	
	newname = '%s.txt' % os.path.splitext(filename)[0]
	command = '%s %s %s' % (cdl, filename, newname)
	successline = 'converted %s to %s\n' % (filename, newname)
	
	return successline in os.popen4( command, 't' )[1].readlines()

	
if __name__ == '__main__':
	for name in Utils.RecurseDirectory( os.getcwd(), IsDebugLog, False ):
		if ConvertDebugLog(name):
			print(('Converted %s' % os.path.basename(name)))
		else:
			print(('Error converting %s' % os.path.basename(name)))

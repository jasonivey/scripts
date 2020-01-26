import os, sys, re, Utils
from mx.DateTime import DateTime

def IsDebugLog(filename):
    return filename.lower().endswith('.dbg')

if __name__ == '__main__':
    
    pattern = r'Parameters: Operation Copy To New Volume \(Apply\).*Finished: Operation Copy To New Volume \(Apply\)'
    regex = re.compile(pattern, re.S)

    op_time_pattern = r'Section Total\s*:\s*1\s*(?P<time>\d+\.\d+)'
    op_time_regex = re.compile(op_time_pattern)
    
    overlapped_io_pattern = r'Using Overlapped I/O with a queue size of (?P<queue_size>\d+) when writing to this image file\.'
    overlapped_io_regex = re.compile(overlapped_io_pattern)
    
    print('File Name,Using ThreadPool,Overlapped Queue Size,Time')
    
    for name in Utils.RecurseDirectory(os.getcwd(), IsDebugLog, False):
        name = '%s.txt' % os.path.splitext(name)[0]
        file = open(name, 'r')
        data = file.read()
        file.close()
        
        for match in regex.findall(data):
            threadpool = match.find('CanWrite PoolThread') != -1
            time_match = op_time_regex.search(match)
            assert( time_match )
            time = float( time_match.group('time') )
            overlapped_io_match = overlapped_io_regex.search(match)
            if overlapped_io_match:
                queue_size = int( overlapped_io_match.group('queue_size') )
            else:
                queue_size = 0
            print(('%s,%s,%d,%f' % (name, threadpool, queue_size, time)))
            
from __future__ import print_function
import argparse
import calendar
import datetime
import sys
import time
import traceback
from threading import Timer

def _parse_args():
    description = 'Print the current time in binary'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-n', '--newline', default=False, action='store_true', help='flag whether to output newlines between time')
    args = parser.parse_args()
    return args.newline

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

def print_time(newlines):
    #print('newlines: {0}'.format(newlines))
    time_digit = calendar.timegm(time.gmtime())
    time_binary = str(bin(time_digit))[2:]
    time_str = datetime.datetime.fromtimestamp(time_digit).strftime("%Y-%m-%d %H:%M:%S")
    if not newlines:
        #sys.stdout.write('{0} : {1}\r'.format(time_binary, time_str))
        #s = '{0} : {1}\r'.format(time_binary, time_str)
        #print(s,)
        print('{0} : {1}\r'.format(time_binary, time_str), end='')
        #print '{}\r'.format(x),
        #sys.stdout.write('{0} : {1}\r'.format(time_binary, time_str))
    else:
        print('{0} : {1}'.format(time_binary, time_str))

def main():
    newlines = _parse_args()
    timer = RepeatedTimer(1, print_time, newlines)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
    finally:
        timer.stop()
    return 0

if __name__ == '__main__':
    sys.exit(main())

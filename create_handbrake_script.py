#!/usr/bin/env python
from __future__ import print_function
import os
import sys
from heapq import heappush, heappop

def main():
    paths = []
    for root, dirs, files in os.walk(os.getcwd()):
        for filename in files:
            if filename.endswith('.avi'):
                heappush(paths, os.path.join(root, filename))
    
    command = '"C:\Program Files (x86)\Handbrake\HandBrakeCLI.exe" ' \
              '-i "{0}" -t 1 -c 1 -o "{1}" -f mp4 -4  -w 640 --loose-anamorphic ' \
              '-e x264 -b 1000 -r 29.97 --pfr  -a 1 -E faac -6 dpl2 -R Auto -B ' \
              '160 -D 0.0 --verbose=1'
    
    with open(r'd:\run.bat', 'w') as run_bat:
        while paths:
            path = heappop(paths)
            source = path
            basename, extension = os.path.splitext(path)
            destination = (basename[:basename.find('[')].strip() if '[' in path else basename) + '.m4v'
            destination = os.path.join('D:\media\Complete', os.path.basename(destination))
            print(command.format(source, destination), file=run_bat)
    
if __name__ == '__main__':
    sys.exit(main())



#!/usr/bin/env python

import argparse
import logging
import logging.handlers
import sys
import traceback

def _update_logger(verbosity):
    if verbosity == 0:
        _log.setLevel(logging.ERROR)
    elif verbosity == 1:
        _log.setLevel(logging.INFO)
    elif verbosity >= 2:
        _log.setLevel(logging.DEBUG)

def _initialize_logger():
    logger = logging.getLogger(__name__)
    logging.captureWarnings(True)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    #handler = logging.handlers.TimedRotatingFileHandler(config_file.log_file,
    #                                                    when="midnight",
    #                                                    interval=1,
    #                                                    backupCount=7)
    #handler.setFormatter(formatter)
    #logger.addHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    #logger.setLevel(logging.INFO)
    return logger

_log = _initialize_logger()

# url,username,password,extra,name,grouping,fav
class LastPass(object):
    def __init__(self, **kwargs):
        self._url = kwargs['url'] if 'url' in kwargs else None
        self._username = kwargs['username'] if 'username' in kwargs else None
        self._password = kwargs['password'] if 'password' in kwargs else None
        self._extra = kwargs['extra'] if 'extra' in kwargs else None
        self._name = kwargs['name'] if 'name' in kwargs else None
        self._grouping = kwargs['grouping'] if 'grouping' in kwargs else None
        self._fav = kwargs['fav'] if 'fav' in kwargs else None

    @staticmethod
    def _parse_fields(data):
        names = ['url','username','password','extra','name','grouping','fav']
        fields = {}
        start = -1
        end = 0
        for name in names:
            end = data.find(',', start + 1)
            if end == -1:
                if len(data[start + 1:]) == 0: break
                end = len(data)
            fields[name] = data[start + 1 : end]
            _log.info(fields)
            start = end
        return fields

    @classmethod
    def deserialize(cls, data):
        return cls(**cls._parse_fields(data))

    def __str__(self):
        return 'url: {0}, username: {1}, password: {2}, extra: {3}, name: {4}, grouping: {5}, fav: {6}' \
            .format(self._url, self._username, self._password, self._extra, self._name, self._grouping, self._fav)


def _parse_args():
    parser = argparse.ArgumentParser(description='Parse lastpass exported data')
    parser.add_argument('file', type=argparse.FileType('r'), nargs='+', help='lastpass exported data files')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    args = parser.parse_args()
    _update_logger(args.verbose)
    return args.file

def _parse_lastpass(handle):
    _log.info('parsing %s' % handle)
    # url,username,password,extra,name,grouping,fav
    lastpasses = []
    for i, line in enumerate(handle.readlines()):
        if i == 0: continue
        _log.info(line.strip())
        lastpasses.append(LastPass.deserialize(line.strip()))
        if line.count(',') > 6:
            _log.alert('HELP!!!')
            sys.exit(1)

def main():
    handles = _parse_args()
    try:
        for handle in handles:
            _parse_lastpass(handle)
            handle.close()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

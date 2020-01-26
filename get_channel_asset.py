#!/usr/bin/env python
# coding: utf-8
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import contextlib
import exceptions
import logging
import logging.handlers
import json
import re
import sys
import urllib.request, urllib.error, urllib.parse
import uuid
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
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

_log = _initialize_logger()

def _is_uuid(uuid_str):
    try:
        return str(uuid.UUID(uuid_str))
    except ValueError:
        raise argparse.ArgumentTypeError('uuid value "%s" is invalid' % uuid_str)

def _parse_args():
    parser = argparse.ArgumentParser(description='Get asset information for a channel')
    parser.add_argument('channel', type=_is_uuid, nargs='+', help='channel external identifier (i.e. a519cb94154e4b9282a6122bb61a6ed2)')
    parser.add_argument('-s', '--server', type=str, default='bbtv.qa.movetv.com', help='host name of CMS server')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    args = parser.parse_args()
    _update_logger(args.verbose)
    _log.debug('verbose: %d, cms: %s, channels: %s' % (args.verbose, args.server, args.channel))
    return args.server, args.channel

class Asset(object):
    def __init__(self, channel_id, cms):
        self._channel_id = uuid.UUID(channel_id)
        self._cms = cms
        self._qvt = None
        self._container_id = None
        self._playback_info = None
        self._id = None
        self._m3u8 = None

    @staticmethod
    def _request_http_data(url, title):
        try:
            _log.info('requesting %s' % url)
            with contextlib.closing(urllib.request.urlopen(url)) as request:
                return request.read()
        except urllib.error.HTTPError as err:
            _log.error('unable to request %s from url %s: %s', title, url, err)
        return None

    def parse_container_id(self):
        url = 'http://{}/cms/publish3/channel/qvt/4/{}/today.qvt'.format(self._cms, self._channel_id.hex) 
        data = Asset._request_http_data(url, 'today qvt')
        if not data:
            _log.err('no data returned from today qvt request')
            return
        self._qvt = json.loads(data)
        if 'container_id' not in self._qvt:
            _log.err('container_id not found in today qvt request')
            return
        self._container_id = self._qvt['container_id']
        _log.info('container_id: %s (type: %s)' % (self._container_id, type(self._container_id)))

    def parse_playback_info(self):
        url = 'http://{}/cms/api/channels/{}/schedule/now/playback_info.qvt'.format(self._cms, self._container_id)
        data = Asset._request_http_data(url, 'playback info')
        if not data:
            _log.err('no data returned from playback info request')
            return
        self._playback_info = json.loads(data)
        #for key, value in self._playback_info['playback_info'].iteritems():
        #    if type(value) not in [type([]), type({})]:
        #        _log.debug('%s: %s' % (key, value))
        #    else:
        #        _log.debug('%s: %s' % (key, type(value)))
        self._parse_id()
        self._parse_m3u8()

    def _parse_id(self):
        m3u8_url_template = self._playback_info['playback_info']['m3u8_url_template']
        match = re.search("[0-9a-f]{32}", m3u8_url_template)
        if not match:
            raise exceptions.RuntimeError('unable to parse m3u8_url_template to find asset id')
        self._id = uuid.UUID(match.group(0))
        _log.info('asset id: %s' % self._id)

    def _parse_m3u8(self):
        version = None
        target_duration = 10
        encryption = None
        m3u8_url_template = self._playback_info['playback_info']['m3u8_url_template']
        if 'clips' in self._playback_info['playback_info']:
            clips = self._playback_info['playback_info']['clips']
            for clip in clips:
                if 'type' in clip and clip['type'] == 'content':
                    url = clip['location']
                    data = Asset._request_http_data(url, 'qmx')
                    if not data:
                        continue
                    qmx_data = json.loads(data)
                    if 'version' in qmx_data:
                        version = int(float(qmx_data['version']))
                    if 'encryption' in qmx_data and \
                       'keys' in qmx_data['encryption'] and \
                       len(qmx_data['encryption']['keys']) > 0:
                        encryption = 'internal'
                if version != None and encryption != None:
                    break
        if not version: version = 4
        m3u8_url_template = m3u8_url_template.replace('$version$', str(version))
        m3u8_url_template = m3u8_url_template.replace('$target_duration$', str(target_duration))
        if encryption:
            m3u8_url_template = m3u8_url_template.replace('$encryption_type$', encryption)
        else:
            m3u8_url_template = m3u8_url_template.replace('_$encryption_type$', '')
        m3u8_url_template = m3u8_url_template.replace('_$audio_type$', '')
        _log.debug('m3u8_url_template: %s' % m3u8_url_template)
        data = Asset._request_http_data(m3u8_url_template, 'root m3u8')
        if not data:
            raise exceptions.RuntimeError('unable to request m3u8')
        for line in data.split('\n'):
            if line.strip().endswith('.m3u8'):
                _log.debug('Found first m3u8: %s' % line)
                self._m3u8 = m3u8_url_template[:m3u8_url_template.rfind('/') + 1]
                self._m3u8 += line.strip()
                break
        if not self._m3u8:
            raise exceptions.RuntimeError('unable to find profile m3u8 within root m3u8')
        _log.info('m3u8: %s' % self._m3u8)


def main():
    cms, channels = _parse_args()
    try:
        for channel in channels:
            _log.info('processing %s' % channel)
            asset = Asset(channel, cms)
            asset.parse_container_id()
            asset.parse_playback_info()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python

import json
import urllib.request, urllib.error, urllib.parse
import os
import sys
import argparse
import traceback
import re

from dateutil import tz
from datetime import datetime

def _convert_time(input_hour):
    try:
        hour = int(input_hour)
        dt = datetime.now(tz.tzlocal())
        dt = datetime(dt.year, dt.month, dt.day, hour, 0, 0, 0, tz.tzlocal())
        return dt.strftime("%s")
        #return dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    except:
        msg = '{0} is not a valid hour (0-23)'.format(input_hour)
        raise argparse.ArgumentTypeError(msg)

def _parse_command_line():
    parser = argparse.ArgumentParser(description='Schedules assets on the LSDVR to be recorded')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='output verbose information')
    parser.add_argument('-s', '--simulated', dest='simulated', action='store_true', help='simulate the scheduling or actually execute the operations')
    parser.add_argument('-z', '--zipcode', dest='zipcode', required=False, default='84003', help='zip code of current location')
    parser.add_argument('-c', '--callsign', dest='callsigns', required=True, action='append', default=[], help='call signs of the channels to record')
    parser.add_argument('-b', '--begin_hour', dest='begin_time', type=_convert_time, required=True, help='begin hour to schedule asset for recording')
    parser.add_argument('-e', '--end_hour', dest='end_time', type=_convert_time, required=True, help='end hour to schedule asset for recording')
    parser.add_argument('-l', '--lsdvr', dest='lsdvr', required=True, help='IP address/hostname of LSDVR to record assets')
    args = parser.parse_args()
    begin_time = datetime.fromtimestamp(int(args.begin_time), tz.tzlocal())
    end_time = datetime.fromtimestamp(int(args.end_time), tz.tzlocal())
    return args.verbose, args.simulated, args.zipcode, args.callsigns, begin_time, end_time, args.lsdvr

def _get_channel_ids(zipcode):
    channels = []
    ota_channel_catalog = urllib.request.urlopen('http://bbtv.qa.movetv.com/cms/publish3/channel/ota_channel_catalog/{0}.json'.format(zipcode)).read()
    channel_catalog = json.loads(ota_channel_catalog)
    for channel in channel_catalog['channels']:
        callsign = channel['service_info']['network_affiliate_name']
        guid = channel['channel_guid']
        qvt = channel['qvt_url']
        channels.append((callsign, guid, qvt))
    return channels

def _get_asset_start_time(asset_url):
    #'lsdvr:///channel/24459c5e91054bd9a12e3263fe17b3b8/asset/b56c0b0bce5df0edf157101ec696103a/start/1400583610/stop/1400585410.0'
    start_stop_regex = '/start/(\d+)/stop/(\d+)\.\d'
    match = re.search(start_stop_regex, asset_url)
    return int(match.group(1)) if match else 0

def _is_asset_within_range(asset_time, begin_time, end_time):
    asset_utc = datetime.utcfromtimestamp(asset_time)
    asset_utc = asset_utc.replace(tzinfo=tz.tzutc())
    asset_local = asset_utc.astimezone(tz.tzlocal())
    return asset_local >= begin_time and asset_local < end_time
    
def _get_assets_to_schedule(verbose, url, lsdvr, begin_time, end_time):
    assets_urls = []
    qvt_json = urllib.request.urlopen(url).read()
    qvt = json.loads(qvt_json)
    for show in qvt['shows']:
        clips_url = show['clips_url']
        asset_start_time = _get_asset_start_time(clips_url)
        if asset_start_time != 0 and _is_asset_within_range(asset_start_time, begin_time, end_time):
            if verbose:
                print('Found {0}'.format(show['title']))
            assets_urls.append(re.sub('[^:]+\://', 'http://{0}'.format(lsdvr), clips_url))
    return assets_urls

def main():
    verbose, simulated, zipcode, callsigns, begin_time, end_time, lsdvr = _parse_command_line()

    if verbose:
        print('simulated : {0}'.format(simulated))
        print('zipcode   : {0}'.format(zipcode))
        print('callsigns : {0}'.format(callsigns))
        print('begin time: {0}'.format(begin_time))
        print('end time  : {0}'.format(end_time))
        print('lsdvr     : {0}'.format(lsdvr))

    try:
        assets_urls = []
        channel_ids = _get_channel_ids(zipcode)

        for channel_id in channel_ids:
            if channel_id[0] in callsigns:
                assets_urls = assets_urls + _get_assets_to_schedule(verbose, channel_id[2], lsdvr, begin_time, end_time)

        for url in assets_urls:
            if not simulated:
                output = ''
                try:
                    output = urllib.request.urlopen(url).read()
                except urllib.error.HTTPError as e:
                    print(e)
                if verbose and len(output) != 0:
                    print(output)
            else:
                print(url)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

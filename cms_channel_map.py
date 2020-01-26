#!/usr/bin/env python

#
# The following script will retrieve the CMS rf footprint given the zip code and environment to use.
#  It will then parse this JSON blob and pull the LSDVR relevant fields to create a channel list
#  which can be embedded within a start_channel_map message or a rf_footprint message for the LSDVR.
# If specified that channel list will be forwarded onto the specified LSDVR to start a specific
#  scan.  The result of this message is then printed out.
#

import exceptions
import json
import os
import sys
import argparse
import re
import traceback
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse


def _get_environment(env):
    if env == 'qa':
        return 'eqa'
    else:
        return env

def _get_cms_rf_footprint(env, zipcode, verbose):
    uri = 'http://bbtv.cms.{0}.movenetworks.com/cms/publish3/channel/ota_channel_catalog/{1}.json'.format(_get_environment(env), zipcode)
    if verbose:
        print('requesting json from {0}'.format(uri))
    response_data = None
    try:
        req = urllib.request.Request(uri)
        response = urllib.request.urlopen(req)
        response_data = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise exceptions.RuntimeError('ERROR: opening url {0}. {1}'.format(uri, e.reason))
    return response_data

def _send_scan_message(address, json_data, verbose):
    headers = {'Content-type': 'application/json; charset=UTF-8'}
    uri = 'http://{0}/api'.format(address)
    if verbose:
        print('posting json from {0}'.format(uri))
    response_data = None
    try:
        req = urllib.request.Request(uri, json_data, headers) 
        response = urllib.request.urlopen(req)
        response_data = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise exceptions.RuntimeError('ERROR: opening url {0}. {1}'.format(uri, e.reason))
    return response_data

def _generate_lsdvr_message(scan_type, footprint, verbose):
    message = {}
    message['message_type'] = 'start_channel_map_scan'
    message['task'] = scan_type
    message['channels'] = footprint['channels']
    if verbose:
        print('LSDVR message\n{0}'.format(json.dumps(footprint, sort_keys=True, separators=(',', ': '), indent=4)))
    return json.dumps(message)
    
def _parse_command_line():
    parser = argparse.ArgumentParser(description='Retrieves and sends the channel map from CMS')
    parser.add_argument('-e', '--environment', dest='environment', required=False, default='dev', help='environment to use to query the CMS')
    parser.add_argument('-z', '--zipcode', dest='zipcode', required=True, default='84097', help='zip code to use to query the CMS')
    lsdvr_group = parser.add_argument_group('lsdvr')
    lsdvr_group.add_argument('-a', '--address', dest='address', required=False, default=None, help='IP address of the LSDVR')
    lsdvr_group.add_argument('-s', '--scan-type', dest='scan_type', choices=['antenna_placement', 'channel_map'], required=False, default=None, help='specify which type of channel map scan to start')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='enable verbose output')
    parser.add_argument('-p', '--pprint', dest='pretty', action='store_true', help='enable styled JSON output')
    parser.add_argument('-o', '--output', dest='output', type=argparse.FileType('w'), metavar='<output file>', default=None, help='file to output results')
    args = parser.parse_args()

    environment = args.environment
    zipcode = args.zipcode
    address = args.address
    scan_type = args.scan_type
    verbose = args.verbose
    pretty = args.pretty
    output = args.output

    if address and not scan_type:
        parser.error('--address must be used in conjunction with --scan_type')
    elif scan_type and not address:
        parser.error('--scan_type must be used in conjunction with --address')
    elif not address and not scan_type and not output:
        parser.error('--output must be specified if not sending data to LSDVR')
    return environment, zipcode, address, scan_type, verbose, pretty, output

def main():
    environment, zipcode, address, scan_type, verbose, pretty, output = _parse_command_line()
    
    if verbose:
        print ('environment: {0}, zip code: {1}, lsdvr: {2}, address: {3}, scan type: {4}, verbose: {5}, pretty print: {6}, dest: {7}'.format(environment, zipcode, address, scan_type, verbose, pretty, dest))

    try:
        cms_json_footprint = _get_cms_rf_footprint(environment, zipcode, verbose)
        if not cms_json_footprint:
            raise exceptions.RuntimeError('ERROR: unable to retrieve a cms rf footprint')
        
        print('Pulled data from CMS')
        if verbose:
            print('CMS RF Footprint for environment {0} and zip code {1}', environment, zipcode)
            print(json.dumps(json.loads(cms_json_footprint), sort_keys=True, separators=(',', ': '), indent=4))

        cms_footprint = json.loads(cms_json_footprint)

        footprint = {}
        footprint['channels'] = []
        for cms_channel in cms_footprint['channels']:
            channel = {}
            if cms_channel['channel_guid'] == 'c4ecaf4783864ca9a94d9b0108c77746':
                continue
            channel['channel_guid'] = cms_channel['channel_guid']
            channel['key_channel'] = cms_channel['service_info']['network_affiliate_name'] in ['NBC', 'CBS', 'ABC', 'FOX']
            channel['service_info'] = {}
            channel['service_info']['callsign'] = cms_channel['service_info']['callsign']
            channel['service_info']['channel_rf'] = cms_channel['service_info']['channel_rf']
            channel['service_info']['channel_major'] = cms_channel['service_info']['channel_major']
            channel['service_info']['channel_minor'] = cms_channel['service_info']['channel_minor']
            footprint['channels'].append(channel)

        if output:
            print('Dumping converted data to output file')
            if pretty:
                output.write(json.dumps(footprint, sort_keys=True, separators=(',', ': '), indent=4))
            else:
                output.write(json.dumps(footprint))

        if verbose and output != sys.stdout:
            print('LSDVR Footprint for environment {0} and zip code {1}', environment, zipcode)
            print(json.dumps(footprint, sort_keys=True, separators=(',', ': '), indent=4))

        if address and scan_type:
            print('Posting message to LSDVR')
            message = _generate_lsdvr_message(scan_type, footprint, verbose)
            message_response = _send_scan_message(address, message, verbose)
            print('message response:\n{0}'.format(message_response))

        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

if __name__ == '__main__':
    sys.exit(main())

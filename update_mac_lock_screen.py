#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
from lxml import etree
import math
import numpy as np
import os
import pathlib
import requests
import subprocess
import sys
import textwrap
import time
import traceback

user_tags = {
    'info'        : parse('<bold><green>'),    # bold green
    'error'       : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

_MAX_ITERATIONS = 5
_VERBOSE = False
_QUOTE_MAX_LINE_WIDTH = 70
_DRY_RUN = False
_CRON_JOB = False
_INVALID_QUOTE_FILENAME = '~/invalid_quotes.txt'

def _is_dry_run():
    return _DRY_RUN

def _verbose_print(msg):
    if _VERBOSE:
        if _CRON_JOB:
            print(f'INFO: {msg}', file=sys.stdout)
        else:
            am.ansiprint(f'<info>INFO: {msg}</info>', file=sys.stdout)

def _error_print(msg):
    if _CRON_JOB:
        print(f'ERROR: {msg}', file=sys.stderr)
    else:
        am.ansiprint(f'<error>ERROR: {msg}</error>', file=sys.stderr)

def _write_invalid_quote(quote):
    invalid_quote_path = pathlib.Path(_INVALID_QUOTE_FILENAME).expanduser()
    with invalid_quote_path.open(mode='a+') as invalid_quote_file:
        invalid_quote_file.write(f'{quote}\n')

class RandomIntegerGenerator(object):
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if RandomIntegerGenerator.__instance == None:
           RandomIntegerGenerator()
        return RandomIntegerGenerator.__instance

    def __init__(self):
        seed = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
        self._generator = np.random.default_rng(seed)
        """ Virtually private constructor. """
        if RandomIntegerGenerator.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            RandomIntegerGenerator.__instance = self

    def integers(self, low=0, high=None, mod=1):
        self._generator.integers(low, high) % mod
'''
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print('Creating random integer generator')
            cls._instance = super(cls).__new__(cls)
            seed = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
            cls._instance._generator = np.random.default_rng(seed)
        return cls._instance

    def integers(self, start=0, stop=None, mod=1):
        self._instance._generator.integers(low, high) % mod_value
'''
def _make_external_command_return_output(args):
    try:
        _verbose_print(f'command: {" ".join(args)}')
        completed_process = subprocess.run(args, capture_output=True, timeout=2.0, check=True, encoding='utf-8')
        return True, completed_process.stdout.strip()
    except subprocess.SubprocessError as err:
        _error_print(f'failed while calling {" ".join(args)}, {err}')
        return False, None
    except Exception as err:
        _error_print(f'failed while calling {" ".join(args)}, {err}')
        return False, None

def _make_external_command(args):
    retval, _ = _make_external_command_return_output(args)
    return retval

def _make_http_call(uri):
    try:
        response = requests.get(uri, timeout=0.5)
        response.raise_for_status()
        response_str = response.text.strip().encode('utf-8')
        return response_str if response_str and len(response_str) > 0 else None
    except requests.exceptions.RequestException as e:
        _error_print(f'failed during http call to {uri}')
        _error_print(e)
    return None

def _get_available_fortunes():
    if sys.platform == 'darwin':
        return ['online', 'random', 'art', 'ascii-art', 'computers', 'cookie', 'definitions', 'drugs', 'education', \
                'ethnic', 'food', 'fortunes', 'goedel', 'humorists', 'kids', 'law', 'linuxcookie', 'literature', \
                'love', 'magic', 'medicine', 'men-women', 'miscellaneous', 'news', 'off', 'people', 'pets', \
                'platitudes', 'politics', 'riddles', 'science', 'softwareengineering', 'songs-poems', 'sports', \
                'startrek', 'translate-me', 'wisdom', 'work', 'zippy']
    else:
        return ['online', 'random', 'art', 'ascii-art', 'computers', 'cookie', 'debian', 'definitions', 'disclaimer', \
                'drugs', 'education', 'ethnic', 'food', 'fortunes', 'goedel', 'humorists', 'kids', 'knghtbrd', 'law', \
                'linux', 'linuxcookie', 'literature', 'love', 'magic', 'medicine', 'men-women', 'miscellaneous', \
                'news', 'paradoxum', 'people', 'perl', 'pets', 'platitudes', 'politics', 'pratchett', 'riddles', \
                'science', 'softwareengineering', 'songs-poems', 'sports', 'startrek', 'tao', 'translate-me', \
                'wisdom', 'work', 'zippy']

def _parse_args():
    parser = argparse.ArgumentParser(description='Update the macOS X lock screen with a random quote')
    sources = _get_available_fortunes()
    source_help = 'choose the source of the quote. Online is pulled from an general online ' \
                  'repo. Random will select randomly from the set of local fortune sources.' \
                  'Or specify the exact fortune source to use.'
    parser.add_argument('source', choices=sources, help=source_help)
    parser.add_argument('-d', '--dry-run', action="store_true", help='run the script without actually setting the quote')
    parser.add_argument('-v', '--verbose', action="store_true", help='increase output verbosity')
    parser.add_argument('-c', '--running-as-cron', action="store_true", help='notifies the script it is being run by the cronjob')
    args = parser.parse_args()
    global _VERBOSE, _DRY_RUN, _CRON_JOB
    _VERBOSE = args.verbose
    _DRY_RUN = args.dry_run
    _CRON_JOB = args.running_as_cron
    source = args.source
    if source == 'random':
        random_generator = RandomIntegerGenerator()
        index = random_generator.integers(low=2, high=len(sources))
        source = sources[index]
        _verbose_print(f'random source requested... using {source}')
    return source

#def _indent_author(quote):
#    index = quote.rfind('\n')
#    if index != -1:
#        return f'{quote[:index]}  {quote[index:]}'
#    return quote

def _wrap_quote(quote, max_width):
    if len(quote) <= max_width:
        _verbose_print(f'max width: {max_width}, line width: {len(quote)}')
        return textwrap.fill(quote, width=max_width)

    line_count = math.ceil(len(quote) / max_width)
    line_width = min(math.ceil(len(quote) / line_count) + 10, max_width)
    _verbose_print(f'max width: {max_width}, line count: {line_count}, line width: {line_width}')
    return textwrap.fill(quote, line_width)

def _format_fortune_quote(quote):
    formatted_quote = _wrap_quote(quote, _QUOTE_MAX_LINE_WIDTH)
    _verbose_print(f'formatted quote\n{formatted_quote}')
    return formatted_quote

def _format_online_quote(quote, author):
    formatted_quote = _wrap_quote(full_quote, _QUOTE_MAX_LINE_WIDTH)
    full_quote = f'{formatted_quote}\n{author}' if author is not None else formatted_quote
    _verbose_print(f'formatted quote\n{full_quote}')
    return full_quote

def _set_quote(quote):
    args = ['sudo', ' defaults', 'write', '/Library/Preferences/com.apple.loginwindow', 'LoginwindowText', f'"{quote}"']
    _verbose_print(f'calling the following command:\n{" ".join(args)}')
    retval = True if _is_dry_run() else _make_external_command(args)
    if not retval:
        _error_print(f'error encountered while writing to LogginwindowText setting the following quote\n{quote}')
        _write_invalid_quote(quote)
        return retval
    args = ['sudo', 'diskutil', 'apfs', 'updatePreboot', '/']
    _verbose_print(f'calling the following command:\n{" ".join(args)}')
    retval = True if _is_dry_run() else _make_external_command(args)
    if not retval:
        _error_print(f'error encountered while updating preboot after setting the following quote\n{quote}')
        _write_invalid_quote(quote)
        return retval
    _verbose_print(f'successfully set loginwindow text and updating preboot for quote\n{quote}')
    return retval

def set_local_fortune_quote(source):
    for i in range(_MAX_ITERATIONS):
        retval, quote = _make_external_command_return_output(['fortune', source])
        if not retval or not quote:
            _error_print(f'encountered while attempting to retrieve a {source} fortune')
            return
        if quote.find('%') != -1:
            _error_print(f'the following quote appears to be invalid, skipping:\n{quote}')
            _write_invalid_quote(quote)
            continue
        formatted_quote = _format_fortune_quote(quote)
        if not formatted_quote:
            _error_print(f'unable to format the following quote successfully:\n{quote}')
            _write_invalid_quote(quote)
            continue
        if _set_quote(formatted_quote):
            break
    if i == _MAX_ITERATIONS:
        _verbose_print(f'after {MAX_ITERATIONS} we were unable to set a quote')

def _get_xml_element_text(root, path):
    get_element_array = etree.XPath(path)
    element_array = get_element_array(root)
    full_text = ''
    for element in element_array:
        full_text += '\n' + element.text.strip(' "') if len(full_text) > 0 else element.text.strip(' "')
    return full_text if len(full_text) > 0 else None

def set_random_online_quote():
    URL = 'http://feeds.feedburner.com/quotationspage/qotd'
    rss_data = _make_http_call(URL)
    print(f'rss data: {rss_data}')
    if not rss_data:
        _error_print(f'failed to return quotes from {URL}')
        return False
    root = etree.fromstring(rss_data)
    assert root is not None, _error_print(f'response from {URL} failed to be parsed as XML:\n{rss_data}')
    get_count = etree.XPath('count(//rss/channel/item)')
    count = int(get_count(root))
    _verbose_print(f'rss feed return {count} items')
    random_generator = RandomIntegerGenerator()
    for i in range(_MAX_ITERATIONS):
        items_index = random_generator.integers(low=0, high=sys.maxsize) % count
        author = _get_xml_element_text(root, f'//rss/channel/item[{items_index}]/title')
        quote = _get_xml_element_text(root, f'//rss/channel/item[{items_index}]/description')
        if quote is None and author is None:
            _error_print(f'quering for title and description within index {i} of the item array')
            continue
        elif quote is None:
            _error_print(f'quering for description (quote) within index {i} of the item array')
            continue
        elif author is None:
            _error_print(f'quering for author within index {i} of the item array')
            _verbose_print(f'rss feed returned the following quote\n{quote}')
        else:
            _verbose_print(f'rss feed returned the following quote\n{quote}\n  {author}')
        formatted_quote = _format_online_quote(quote, author)
        if not formatted_quote:
            _error_print(f'unable to format the following quote successfully:\n{quote}')
            _write_invalid_quote(quote)
            continue
        if _set_quote(formatted_quote):
            break
    if i == _MAX_ITERATIONS:
        _verbose_print(f'after {MAX_ITERATIONS} we were unable to set a quote')

def main():
    source = _parse_args()
    try:
        if source == 'online':
            set_random_online_quote()
        else:
            set_local_fortune_quote(source)
    except:
        #_error_print('uncaught exception caught in main -- debug via uncommenting the traceback calls')
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

from contextlib import closing
import urllib
from lxml import etree
import re

def _get_links_in_html_page(doc):
    class CollectorTarget(object):
        def __init__(self):
            self.links = []
        def start(self, tag, attrib):
            #print('len of links: {0}'.format(len(self.links)))
            if tag == '{http://www.w3.org/1999/xhtml}a':
                if attrib.has_key('href'):
                    self.links.append(attrib['href'])
            #print("start %s %r" % (tag, dict(attrib)))
        def end(self, tag):
            pass
            #print("end %s" % tag)
        def data(self, data):
            pass
            #print("data %r" % data)
        def comment(self, text):
            pass
            #print("comment %s" % text)
        def close(self):
            #print('len of links: {0}'.format(len(self.links)))
            #print("close")
            return self.links
    parser = etree.XMLParser(target = CollectorTarget())
    return etree.XML(doc, parser)

def _get_streams_ids(ipaddr, verbose):
    ids = []
    url = 'http://{0}'.format(ipaddr)
    with closing(urllib.urlopen(url)) as site:
        for link in _get_links_in_html_page(site.read()):
            match = re.match(r'^(?P<id>[\dA-F]{32})/$', link)
            if match:
                ids.append(match.group('id'))
    return ids

def list_streams(ipaddr, verbose):
    for id in _get_streams_ids(ipaddr, verbose):
        print(id)

class StreamSize(object):
    def __init__(self, name, url):
        self.name = name
        self.urls = [url]
        self.sizes = []
    def add_url(self, url):
        self.urls.append(url)
    def get_average(self):
        average = 0.0
        for size in self.sizes:
            average += size
        return average / float(len(self.sizes))
    def process(self):
        for url in self.urls:
            with closing(urllib.urlopen(url)) as site:
                meta = site.info()
                self.sizes.append(float(meta.getheaders("Content-Length")[0]))
    def __str__(self):
        str = ''
        average = self.get_average()
        name = self.name
        str = '{0}: {1}'.format(name, round(average, 1))
        if average >= 100000 and average < 1000000:
            str += ' ({0} kb)'.format(round(average / 1024.0, 1))
        elif average >= 1000000:
            str += ' ({0} mb)'.format(round(average / (1024.0 * 1024.0), 1))
        return str

def get_stream_partitions(ipaddr, stream, verbose):
    partitions = []
    url = 'http://{0}/{1}/'.format(ipaddr, stream)
    with closing(urllib.urlopen(url)) as site:
        for link in _get_links_in_html_page(site.read()):
            match = re.match(r'^(?P<partition>[\dA-F]{4})/$', link)
            if match:
                partitions.append(match.group('partition'))
    return partitions

def get_stream_files(ipaddr, stream, partition, verbose):
    stream_files = []
    url = 'http://{0}/{1}/{2}/'.format(ipaddr, stream, partition)
    with closing(urllib.urlopen(url)) as site:
        for link in _get_links_in_html_page(site.read()):
            match = re.match(r'^(?P<stream>[\dA-F]{32})_(?P<profile>\d{2})(?P<number>[\dA-F]{8})\.ts$', link)
            if match:
                name = match.group(0)
                number = int(match.group('number'), 16)
                profile = int(match.group('profile'), 16)
                stream_files.append((name, number, profile))
    return stream_files

def get_stream_files_sizes(ipaddr, stream, partition, verbose):
    streams = {}
    url = 'http://{0}/{1}/{2}/'.format(ipaddr, stream, partition)
    with closing(urllib.urlopen(url)) as site:
        for link in _get_links_in_html_page(site.read()):
            match = re.match(r'^(?P<stream>[\dA-F]{32})_(?P<profile>\d{2})(?P<id>[\dA-F]{8})\.ts$', link)
            if match:
                id = int(match.group('id'), 16)
                name = '%s_XX%08X.ts' % (match.group('stream'), id)
                if streams.has_key(id):
                    streams[id].add_url(url + match.group())
                else:
                    streams[id] = StreamSize(name, url + match.group())
    return streams
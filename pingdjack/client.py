# -*- coding:utf-8 -*-
import re
from urllib.request import urlopen
from urllib.parse import urlsplit
import xmlrpc.client
from xml.parsers.expat import ExpatError

from html5lib import HTMLParser

def external_urls(html, root_url):
    '''
    Finds external links in an HTML fragment and returns an iterator
    with their URLs.

    root_url defines a root outside of which links are considered external.
    '''
    s, root_host, root_path, q, f = urlsplit(root_url)

    def is_external(url):
        schema, host, path, query, fragment = urlsplit(url)
        return schema in ('', 'http', 'https') and host != '' and \
               (host != root_host or not path.startswith(root_path))

    doc = HTMLParser().parseFragment(html)
    urls = (n.attributes.get('href', '') for n in doc if n.name == 'a')
    return (u.encode('utf-8') for u in urls if is_external(u))

def ping(source_url, target_url):
    '''
    Makes a pingback request to target_url on behalf of source_url, i.e.
    effectively saying to target_url that "the page at source_url is
    linking to you".
    '''

    def search_link(content):
        match = re.search(r'<link rel="pingback" href="([^"]+)" ?/?>', content)
        return match and match.group(1)

    request_url = 'http:%s' % target_url if target_url.startswith('//') else target_url
    f = urlopen(request_url)
    try:
        info = f.info()
        server_url = info.get('X-Pingback', '') or \
                                  search_link(f.read(512 * 1024))
        if server_url:
            server = xmlrpc.client.ServerProxy(server_url)
            server.pingback.ping(source_url, target_url)
    finally:
        f.close()

def ping_external_urls(source_url, html, root_url):
    '''
    Makes pingback requests to all external links in an HTML fragment.

    source_url is a URL of the page contaning HTML fragment.
    root_url defines a root outside of which links are considered external.
    '''
    for url in external_urls(html, root_url):
        try:
            ping(source_url, url)
        except (IOError, xmlrpc.client.Error, ExpatError):
            # One failed URL shouldn't block others
            pass

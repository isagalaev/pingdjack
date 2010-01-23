# -*- coding:utf-8 -*-
from urllib2 import urlopen
from urlparse import urlsplit
import xmlrpclib
import cgi

from html5lib import HTMLParser
from django import http
from django.views.decorators.http import require_POST
from django import dispatch
from django.core.urlresolvers import resolve, Resolver404

# Connect a handler to the "received" signal that will handle pingback
# requests made to your server. The signal provides the following keyword
# arguments:
#
# - sender: a Django HttpRequest instance of a request handling the pingback
# - source_url: a URL that links to your server URL
# - target_url: a URL being linked to by the page at source_url
# - view: resolved view function for target_url
# - args: arguments for the view function
# - kwargs: keyword arguments for the view
# - author: the page author's name guessed from the source page HTML
# - excerpt: an excerpt from the text surrounding the link in the source page
#   HTML
#
# The signal is sent only after the server performs validity checks on provided
# URLs. This guarantees that they are both exist, that target_url belongs to
# this server and that source_url indeed is linking here.

received = dispatch.Signal(providing_args=['source_url', 'target_url', 'view', 'args', 'kwargs', 'author', 'excerpt'])

CONTAINERS = [
    'body', 'section', 'nav', 'article', 'aside',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hgroup', 'header', 'footer', 'address',
    'p', 'pre', 'blockquote', 'ol', 'ul', 'li', 'dl', 'dt', 'dd', 'div',
    'td', 'th', 'caption', 'form', 'fieldset', 'legend', 'details',
]

def parse_data(source_url, target_url):
    '''
    Parses the page at target_url looking for the link with source_url and
    tries to guess page author's name and text excerpt.

    Returns (author, excerpt) if found or None otherwise.
    '''
    f = urlopen(source_url)
    content_type = cgi.parsef.info().getheader('content-type', 'text/html')
    value, params = cgi.parse_header(content_type)
    charset = params.get('charset', 'utf-8').replace("'", '')
    doc = HTMLParser().parse(f.read.decode(charset))
    for node in doc:
        if node.name == u'a' and node.attributes.get('href') == target_url:
            link = node
            break
    else:
        raise Exception('Target URL is not found under source URL')

    def text(node):
        result = u''.join(s.value for s in node if s.type == 4)
        return result.replace(u'\n', u' ').strip()

    def find(node, name, exclude):
        childNodes = (n for n in node.childNodes if n != exclude)
        for child in childNodes:
            if child.name == name:
                return child
            result = find(child, name, None)
            if result:
                return result

    # find excerpt
    container = link.parent
    while container.name not in CONTAINERS:
        container = container.parent
    excerpt = text(container)

    # find author
    container, node = link.parent, link
    while container:
        address = find(container, 'address', node)
        if address:
            author = text(address)
            break
        container, node = container.parent, container
    else:
        title = find(doc, 'title', None)
        author = title and text(title) or unicode(source_url)
    return author, excerpt

def _handle_pingback(request, root, source_url, target_url):
    schema, host, path, query, fragment = urlsplit(target_url)
    if host != request.get_host() or not path.startswith(root):
        raise Exception('Target URL is not under "%s://%s%s"' % (
            request.is_secure() and 'https' or 'http',
            request.get_host(),
            root,
        ))
    try:
        urlconf = getattr(request, 'urlconf', None)
        view, args, kwargs = resolve(path, urlconf)
    except Resolver404:
        raise Exception('Target URL not found on server')
    author, excerpt = parse_data(source_url, target_url)
    received.send(request,
        source_url = source_url,
        target_url = target_url,
        view = view,
        args = args,
        kwargs = kwargs,
        author = author,
        excerpt = excerpt,
    )

@require_POST
def server_view(request, root='/'):
    '''
    Server view handling pingback requests.

    Include this view in your urlconf under any path you like and
    provide a link to this URL in your HTML:

        <link rel="pingback" href="..."/>

    Or send it in an HTTP server header:

        X-Pingback: ...

    The optional parameter "root" sets a root path within which server will
    consider incoming target URLs as its own.
    '''
    try:
        args, method = xmlrpclib.loads(request.raw_post_data)
        if method != 'pingback.ping':
            raise Exception('Unknown method "%s"' % method)
        _handle_pingback(request, root, *args)
        result = xmlrpclib.dumps((None,), methodresponse=True, allow_none=True)
    except Exception, e:
        fault = xmlrpclib.Fault(1, str(e))
        result = xmlrpclib.dumps(fault)
    return http.HttpResponse(result)

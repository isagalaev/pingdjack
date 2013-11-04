'''
Server and client implementation of Pingback protocol
(http://hixie.ch/specs/pingback/pingback-1.0).

Relies upon semantics of HTML5 to discover links, parse source text excerpt
and author name.
'''

from .client import external_urls, ping, ping_external_urls
from .server import received, parse_data, server_view
from .errors import SourceNotFound, TargetNotFoundUnderSource, \
                    TargetDoesNotExist, UnpingableTarget, DuplicatePing, \
                    AccessDenied, UpstreamError

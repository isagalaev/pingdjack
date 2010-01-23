# -*- coding:utf-8 -*-
import xmlrpclib

class Error(xmlrpclib.Fault):
    code = 0
    message = 'Unknown error'

    def __init__(self, message=None, **kwargs):
        message = message or self.message
        super(Error, self).__init__(self.code, message, **kwargs)

class SourceNotFound(Error):
    code = 16
    message = 'Source URL is not found'

class TargetNotFoundUnderSource(Error):
    code = 17
    message = 'Target URL is not found under source URL'

class TargetDoesNotExist(Error):
    code = 32
    message = 'Target URL does not exist'

class UnpingableTarget(Error):
    code = 33
    message = 'Target does not accept pingbacks'

class DuplicatePing(Error):
    code = 48
    message = 'Pingback has already been registered'

class AccessDenied(Error):
    code = 49
    message = 'AccessDenied'

class UpstreamError(Error):
    code = 50
    message = 'Server could not communicate with upstream'

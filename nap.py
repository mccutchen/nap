"""A generic, simple, potentially-dumb wrapper around a RESTful
API. Attribute accesses are translated into path components in API URLs,
method calls are translated into HTTP requests."""

import httplib
import logging
import os
import re
import sys
import urllib


class Api(object):
    """A simple wrapper around a RESTful API. Should be subclassed for each
    API to be wrapped. Subclasses MUST set the

        _api_host
        _api_url_template

    class attributes and MAY override the

        _process_params
        _process_headers
        _process_response

    instance methods to control how HTTP requests are made."""

    _api_host = None
    _api_url_template = '%s'
    _api_use_https = False

    def __init__(self, paths=None):
        self.paths = paths or tuple()

    def __getattr__(self, name):
        return self(name)

    def __call__(self, name):
        return TwitterAPI(self.paths + (str(name),))

    def get(self, **kwargs):
        return self._request('get', **kwargs)

    def post(self, **kwargs):
        return self._request('post', **kwargs)

    def put(self, **kwargs):
        return self._request('put', **kwargs)

    def delete(self, **kwargs):
        return self._request('delete', **kwargs)

    def _request(self, method, **kwargs):
        """Makes a request to the Twitter API using the given HTTP method and
        the current set of path components for this object. Any kwargs will be
        used as request parameters (appended to the URL for GET requests, sent
        in the request body otherwise).
        """
        url, body = build_url(method, self.paths, **kwargs)
        return make_request(method, url, body)

    def _process_params(self, params):
        """Preprocesses parameters before making a request. By default, all
        parameters are converted to utf-8 strings."""
        result = {}
        for k, v in params.iteritems():
            result[k] = unicode(v).encode('utf8')
        return result

    def _process_headers(self):
        """Generate a dict of headers to add to the request."""
        return {}

    def _process_response(self, resp):
        """Post-processes the response object."""
        return resp



##############################################################################
# Helper functions
##############################################################################
def build_url(method, paths, **kwargs):
    """Builds an appropriate Twitter API URL to request. Returns a 2-tuple of
    (url, request body).

    The URL will be built as follows: The given paths be joined with slashes
    and inserted into the URL_TEMPLATE string. Any kwargs are interpreted as
    request parameters and will be appended to the URL for GET requests or
    treated as the request body otherwise.
    """
    url = URL_TEMPLATE % '/'.join(paths)
    params = preprocess_params(kwargs)
    if method == 'get':
        if params:
            url += '?' + urllib.urlencode(params)
        body = None
    else:
        body = urllib.urlencode(params) if params else None
    return url, body

def preprocess_params(params):
    """Preprocess request parameters. Only transforms bools into the
    appropriate strings, at the moment.
    """
    processed = dict(params)
    for k, v in processed.iteritems():
        if isinstance(v, bool):
            processed[k] = str(int(v))
    return processed

def make_request(method, url, body, headers=None, parse_json=True):
    """Makes an HTTP request. Responses are assumed to be JSON, and will be
    parsed as such.
    """
    logging.info('Request: %s %s', method.upper(), url)
    if body:
        logging.info('Request body: %r', body)
    conn = httplib.HTTPConnection(API_HOST)
    conn.request(method.upper(), url, body)
    resp = conn.getresponse()
    if resp.status != 200:
        raise TwitterError('Bad Response: %s %s' % (resp.status, resp.reason))
    if parse_json:
        return json.load(resp, object_hook=AttrDict)
    else:
        return resp.read()


if __name__ == '__main__':
    api = TwitterAPI()
    print api.statuses.public_timeline.get(trim_user=True)

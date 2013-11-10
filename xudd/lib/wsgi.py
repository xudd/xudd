import logging
import urlparse
import sys

try:
    from io import BytesIO # python 3
except ImportError:
    from cStringIO import StringIO as BytesIO # python 2

from tornado import escape


from xudd.actor import Actor, super_init

_log = logging.getLogger(__name__)


class WSGI(Actor):
    def __init__(self, hive, id, app=None):
        super(WSGI, self).__init__(hive, id)
        self.message_routing.update({
            'handle_request': self.handle_request,
            'set_app': self.set_app
        })

        self.wsgi_app = app

    def set_app(self, message):
        '''
        Set the WSGI backend app.

        Expects:
            body: {
                app: <WSGI app>
            }
        '''
        self.wsgi_app = message.body['app']

    def handle_request(self, message):
        _log.info('Got request')

        _log.debug('message body: {0}'.format(message.body))

        options = message.body.get('options')

        uri_parts = urlparse.urlparse(''.join([
            'http://fake.example',
            options.get('uri')
        ]))

        environ = {
            'REQUEST_METHOD': options.get('method'),
            'SCRIPT_NAME': '',
            'PATH_INFO': escape.url_unescape(uri_parts.path),
            'QUERY_STRING': uri_parts.query,
            "REMOTE_ADDR": options.get('remote_ip'),
            "SERVER_NAME": options.get('server_name'),
            "SERVER_PORT": str(options.get('port')),
            "SERVER_PROTOCOL": options.get('version'),
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": 'http',
            "wsgi.input": BytesIO(escape.utf8(message.body.get('body'))),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        if "Content-Type" in options.get('headers'):
            environ["CONTENT_TYPE"] = options.get('headers').pop("Content-Type")
        if "Content-Length" in options.get('headers'):
            environ["CONTENT_LENGTH"] = options.get('headers').pop("Content-Length")
        for key, value in options.get('headers').items():
            environ["HTTP_" + key.replace("-", "_").upper()] = value

        response = []
        data = {
            'status': 200,
            'headers': {}}

        def start_response(status, response_headers, exc_info=None):
            data['status'] = status
            data['headers'] = response_headers

            return response.append

        app_return_value = self.wsgi_app(environ, start_response)

        if app_return_value is not None:
            try:
                response_iterator = iter(app_return_value)
                for i in response_iterator:
                    response.append(i)
            except TypeError as exc:
                _log.error('response: {0}; error: {1}'.format(
                    response_iterator,
                    traceback.format_exc()))

        _log.info('response: {0}'.format(response))

        message.reply(
            directive='respond',
            body={
                'response': 'HTTP/1.1 {status}\r\n{headers}\r\n\r\n{body}'.format(
                    status=data.get('status'),
                    headers='\r\n'.join(
                        [': '.join(i) for i in data.get('headers')]),
                    body=''.join(response))
            })



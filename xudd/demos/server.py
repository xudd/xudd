from __future__ import print_function

import sys
import logging
import select
import socket
import traceback

from tornado import httputil, httpserver, escape

try:
    from io import BytesIO # python 3
except ImportError:
    from cStringIO import StringIO as BytesIO # python 2

from xudd.actor import Actor, super_init
from xudd.hive import Hive

_log = logging.getLogger(__name__)

MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10M


class Server(Actor):
    @super_init
    def __init__(self, hive, id):
        self.message_routing.update({
            'respond': self.respond,
            'listen': self.listen
        })
        self.requests = {}

    def listen(self, message):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(0)  # XXX: Don't know if this helps much
        self.socket.bind(('', 8000))
        self.socket.listen(1024)

        while True:
            readable, writable, errored = select.select(
                [self.socket],
                [],
                [],
                .0000001)  # XXX: This will surely make it fast! (?)

            if readable:
                _log.info('Got new request ({0} in local index)'.format(len(self.requests)))
                req = self.socket.accept()

                # Use the message id as the internal id for the request
                message_id = self.send_message(
                    to='http',
                    directive='handle_request',
                    body={
                        'request': req
                    }
                )

                _log.debug('Sent request to worker')

                self.requests.update({
                    message_id: req
                })

            yield self.wait_on_self()

    def respond(self, message):
        _log.debug('Responding')

        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])
        sock.close()
        del self.requests[message.in_reply_to]
        _log.info('Responded')


class HTTPHandler(Actor):
    @super_init
    def __init__(self, hive, id):
        self.message_routing.update({
            'handle_request': self.handle_request,
            'handle_request_body': self.handle_request_body
        })

    def handle_request(self, message):
        sock, bind = message.body['request']

        while True:
            r, w, e = select.select([sock], [], [], .0001)

            if not r:
                yield self.wait_on_self()
            else:
                first_data = sock.recv(8192)

                _log.debug('first_data: {0}'.format(first_data))

                # XXX: Sometimes first_data is zero-length when running
                # `ab -n 10000 -c 500 URI` against the server, this block
                # catches those cases, but I'm still not sure why they occur.
                try:
                    request_line, rest = first_data.split('\r\n', 1)

                    method, uri, version = request_line.split(' ')

                    http_headers, rest = rest.split('\r\n\r\n', 1)

                    headers = httputil.HTTPHeaders.parse(http_headers)

                    _log.info('headers: {0}'.format(headers))

                    remote_ip = sock.getpeername()[0]

                    content_length = headers.get('Content-Length')

                    if content_length:
                        content_length = int(content_length)

                        if content_length > MAX_REQUEST_SIZE:
                            raise Exception('Content-Length too long')

                        if headers.get('Expect') == '100-continue':
                            sock.sendall('HTTP/1.1 100 (Continue)\r\n\r\n')

                            additional_data = b''

                            while True:
                                r, w, e = select.select([sock], [], [], .0001)

                                if not r:
                                    yield self.wait_on_self()

                                additional_data += sock.recv(content_length)

                                if len(additional_data) == content_length:
                                    break

                            _log.debug('additional_data: {0}'.format(
                                additional_data))

                            rest += additional_data

                    body = rest
                    _log.debug('body: {0}'.format(body))

                    option_names = ('method', 'uri', 'version', 'headers',
                                    'remote_ip', 'content_length')
                    options = dict(
                        method=method,
                        uri=uri,
                        version=version,
                        headers=headers,
                        remote_ip=remote_ip,
                        content_length=content_length,
                        server_name=bind[0],
                        port=bind[1])

                    _log.debug('options: {0}'.format(options))

                    _log.info('{method} {uri} ({content_length})'.format(
                        **options))
                except Exception as exc:
                    _log.error('Failed to parse request: {0}\n---\n{0}'.format(
                        traceback.format_exc(),
                        first_data
                    ))

                    message.reply(
                        directive='respond',
                        body={
                            'response': 'HTTP/1.1 400 Invalid Request\r\n'
                                'Connection: close'
                        })
                    break  # Don't try to parse the request any further as
                           # we've already replied with a 400

                parsed = yield self.wait_on_message(
                    to=self.id,
                    directive='handle_request_body',
                    body={
                        'options': options,
                        'body': body
                    }
                )

                response = yield self.wait_on_message(
                    to='wsgi',
                    directive='handle_request',
                    body={
                        'body': body,
                        'options': options,
                        'arguments': parsed.body['arguments'],
                        'files': parsed.body['files']
                    })

                message.reply(
                    directive='respond',
                    body={
                        'response': response.body.get('response')
                    })

                break

    def handle_request_body(self, message):
        options = message.body['options']

        files = {}
        arguments = {}

        if options['method'] in ('POST', 'PATCH', 'PUT'):
            _log.debug('Parsing message body')
            httputil.parse_body_arguments(
                options['headers'].get('Content-Type', ''),
                message.body['body'],
                arguments,
                files)

        message.reply(
            body={
                'arguments': arguments,
                'files': files
            })


class WSGI(Actor):
    @super_init
    def __init__(self, hive, id):
        self.message_routing.update({
            'handle_request': self.handle_request
        })

        import mediagoblin.app

        self.mediagoblin = mediagoblin.app.MediaGoblinApp('mediagoblin.ini',
                                                          False)

    def handle_request(self, message):
        _log.info('Got request')

        _log.debug('message body: {0}'.format(message.body))

        options = message.body.get('options')

        environ = {
            'REQUEST_METHOD': options.get('method'),
            'SCRIPT_NAME': '',
            'PATH_INFO': escape.url_unescape(options.get('uri')),
            'QUERY_STRING': '',
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

        for i in self.mediagoblin(environ, start_response):
            response.append(i)

        _log.info('response: {0}'.format(response))

        message.reply(
            directive='respond',
            body={
                'response': 'HTTP/1.1 {status}\r\n{headers}\r\n\r\n{body}'.format(
                    status=data.get('status'),
                    headers=[': '.join(i) for i in data.get('headers')],
                    body=''.join(response))
            })


class WebSocketHandler(Actor):
    @super_init
    def __init__(self, hive, id):
        self.message_routing.update({
            'handle_request': self.handle_request
        })

    def handle_request(self, message):
        pass

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    logging.getLogger('xudd.hive').setLevel(logging.INFO)
    logging.getLogger('xudd.actor').setLevel(logging.INFO)

    hive = Hive()

    server_id = hive.create_actor(Server, id='server')

    hive.create_actor(HTTPHandler, id='http')
    hive.create_actor(WSGI, id='wsgi')

    hive.send_message(to='server', directive='listen')

    try:
        hive.run()
    finally:
        try:
            _log.info('Closing sockets')
            server = hive._actor_registry[server_id]
            server.socket.close()
            for key, val in server.requests.iteritems():
                sock, bind = val

                sock.close()
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()

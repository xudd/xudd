import logging
import select
import traceback

from tornado import httputil, httpserver, escape

from xudd.actor import Actor, super_init

_log = logging.getLogger(__name__)


class HTTP(Actor):
    '''
    Parses HTTP from socket data
    '''
    def __init__(self, hive, id, request_handler):
        super(HTTP, self).__init__(hive, id)
        self.message_routing.update({
            'handle_request': self.handle_request,
            'handle_request_body': self.handle_request_body
        })

        self.request_handler = request_handler

    def handle_request(self, message):
        '''
        Handles a socket request

        Expects:
            body: {
                'request': <the return value of socket.accept()>
            }

        Much of the code for parsing HTTP is inspired by the tornado framweork
        <http://tornadoweb.org>.
        '''
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

                arguments, files = self.handle_request_body(method, headers, body)

                response = yield self.wait_on_message(
                    to=self.request_handler,
                    directive='handle_request',
                    body={
                        'body': body,
                        'options': options,
                        'arguments': arguments,
                        'files': files
                    })

                message.reply(
                    directive='respond',
                    body={
                        'response': response.body.get('response')
                    })

                break

    def handle_request_body(self, method, headers, body):

        files = {}
        arguments = {}

        if method in ('POST', 'PATCH', 'PUT'):
            _log.debug('Parsing message body')
            httputil.parse_body_arguments(
                headers.get('Content-Type', ''),
                body,
                arguments,
                files)

        return arguments, files

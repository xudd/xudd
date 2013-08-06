from __future__ import print_function

import logging
import select
import socket

from wsgiref.simple_server import WSGIRequestHandler

from tornado import httputil

from xudd.actor import Actor, super_init
from xudd.hive import Hive

_log = logging.getLogger(__name__)


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
                .0000001)

            if readable:
                _log.info('Got new request ({0} in local index)'.format(len(self.requests)))
                req = self.socket.accept()

                # Use the message id as the internal id for the request
                request_id = self.wait_on_message(
                    to='http',
                    directive='handle_request',
                    body={
                        'request': req
                    }
                )

                _log.debug('Sent request to worker')

                self.requests.update({
                    request_id: req
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
            'self_reply': lambda x: x
        })

    def handle_request(self, message):
        sock, bind = message.body['request']

        while True:
            r, w, e = select.select([sock], [], [], .0001)

            if not r:
                self.wait_on_self()
            else:
                first_data = sock.recv(8192)

                request_line, rest = first_data.split('\r\n', 1)

                http_headers, rest = rest.split('\r\n\r\n', 1)

                headers = httputil.HTTPHeaders.parse(http_headers)

                _log.info('headers: {0}'.format(headers))

                message.reply(
                    directive='respond',
                    body={
                        'response': 'HTTP/1.1 200 OK\r\nConnection: close\r\n'
                    })

                break



class WSGI(Actor):
    @super_init
    def __init__(self, hive, id):
        self.message_routing.update({
            'handle_request': self.handle_request
        })

    def handle_request(self, message):
        _log.info('Got request')

        message.reply(
            directive='respond',
            body={
                'response': 'HTTP/1.1 200 OK\r\nConnection: close\r\n'
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

    logging.getLogger('xudd.hive').setLevel(logging.INFO)
    logging.getLogger('xudd.actor').setLevel(logging.INFO)

    hive = Hive()

    server_id = hive.create_actor(Server, id='server')

    wsgi_id = hive.create_actor(WSGI, id='wsgi')
    http_id = hive.create_actor(HTTPHandler, id='http')

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

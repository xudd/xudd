from __future__ import print_function

import logging
import select
import socket

from SocketServer import TCPServer
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from xudd.actor import Actor
from xudd.hive import Hive

_log = logging.getLogger(__name__)


class Server(Actor):
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)
        self.message_routing.update({
            'respond': self.respond,
            'listen': self.listen,
            'select': self.select
        })
        self.requests = {}

    def listen(self, message):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)  # XXX: Don't know if this helps much
        self.socket.bind(('', 8000))
        self.socket.listen(1024)

        self.send_message(to=self.id, directive='select')

    def select(self, message):
        readable, writable, errored = select.select(
            [self.socket],
            [],
            [],
            .0000001)

        if readable:
            _log.info('Got new request ({0} in local index)'.format(len(self.requests)))
            req = self.socket.accept()
            message_id = self.wait_on_message(
                to='wsgi',
                directive='handle_request',
                body={
                    'request': req
                }
            )

            _log.debug('Sent request to worker')

            self.requests.update({
                message_id: req
            })

        self.send_message(to=self.id, directive='select')

    def respond(self, message):
        _log.debug('Responding')

        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])
        sock.close()
        del self.requests[message.in_reply_to]
        _log.info('Responded')


class WSGI(Actor):
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)
        self.message_routing.update({
            'handle_request': self.handle_request
        })

    def handle_request(self, message):
        _log.info('Got request')
        sock, bind = message.body['request']
        r, w, e = select.select([sock], [], [], 5)

        if not r:
            raise Exception('Timeout')

        _log.debug(sock.recv(8192))
        message.reply(
            directive='respond',
            body={
                'response': '''HTTP/1.1 200 OK\r\nConnection: close\r\n'''
            })

class WebSocketHandler(Actor):
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)
        self.message_routing.update({
            'handle_request': self.handle_request
        })

    def handle_request(self, message):
        pass

def main():
    logging.basicConfig(level=logging.INFO)

    hive = Hive()

    server_id = hive.create_actor(Server, id='server')

    wsgi_id = hive.create_actor(WSGI, id='wsgi')

    hive.send_message(to='server', directive='listen')

    try:
        hive.run()
    finally:
        _log.info('Closing sockets')
        server = hive._actor_registry[server_id]
        server.socket.close()
        for key, val in server.requests.iteritems():
            sock, bind = val

            sock.close()

if __name__ == '__main__':
    main()

from __future__ import print_function

import logging
import select

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
            'handle': self.handle,
            'ping': self.ping
        })
        self.requests = {}

    def ping(self, message):
        _log.debug('Pong')

    def respond(self, message):
        _log.debug('Responding')

        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])
        sock.close()
        _log.debug('Responded')

    def listen(self, message):
        self.request_handler = BaseHTTPRequestHandler
        self.request_handler.protocol_version = 'HTTP/1.1'
        self.httpd = HTTPServer(('', 8000), self.request_handler)

        self.send_message(to=self.id, directive='handle')

    def handle(self, message):
        r, w, e = select.select([self.httpd], [], [], .0000001)

        if r:
            _log.debug('Got readable')
            req = self.httpd.get_request()
            message_id = self.send_message(
                to='wsgi',
                directive='request',
                body={
                    'request': req
                }
            )

            _log.debug('Sent request to worker')

            self.requests.update({
                message_id: req
            })

        self.send_message(to=self.id, directive='handle')

class WSGI(Actor):
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)
        self.message_routing.update({
            'request': self.request
        })

    def request(self, message):
        _log.info('Got request')
        sock, bind = message.body['request']
        _log.debug(sock.recv(8192))
        message.reply(
            directive='respond',
            body={
                'response': '''HTTP/1.1 200 OK\r\n\r\n'''
            })

def main():
    logging.basicConfig(level=logging.DEBUG)

    hive = Hive()

    server = hive.create_actor(Server, id='server')

    wsgi = hive.create_actor(WSGI, id='wsgi')

    hive.send_message(to='server', directive='listen')

    hive.run()

if __name__ == '__main__':
    main()

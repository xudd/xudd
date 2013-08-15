import socket
import select
import logging

from xudd.actor import Actor, super_init

_log = logging.getLogger(__name__)

class Server(Actor):
    @super_init
    def __init__(self, hive, id=None, request_handler=None):
        self.message_routing.update({
            'respond': self.respond,
            'listen': self.listen
        })
        self.requests = {}
        self.request_handler = request_handler


    def listen(self, message):
        body = message.body

        port = body.get('port', 8000)
        host = body.get('host', '127.0.0.1')

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(0)  # XXX: Don't know if this helps much
        self.socket.bind((host, port))
        self.socket.listen(5)  # Max 5 connections in queue

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
                    to=self.request_handler,
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

    def send(self, message):
        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])

    def close(self, message):
        sock, bind = self.requests.get(message.in_reply_to)
        sock.close()

    def respond(self, message):
        _log.debug('Responding')

        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])
        sock.close()
        del self.requests[message.in_reply_to]
        _log.info('Responded')


class Client(Actor):
    @super_init
    def __init__(self, hive, id, message_handler=None):
        self.message_routing.update({
            'connect': self.connect,
            'send': self.send,
        })

        self.message_handler = message_handler

    def connect(self, message):
        try:
            host = message.body['host']
            port = message.body['port']
        except KeyError:
            raise ValueError('{klass}.connect must be called with `host` and\
                             `port` arguments in the message body'.format(
                             self.__class__.__name__))

        # Options
        timeout = message.body.get('timeout', socket.getdefaulttimeout())
        chunk_size = message.body.get('chunk_size', 1024)

        self.socket = socket.create_connection((host, port), timeout)
        self.socket.setblocking(0)  # XXX: Don't know if this helps much

        _log.info('Connected to {host}:{port}'.format(host=host, port=port))

        while True:
            readable, writable, errored = select.select(
                [self.socket],
                [],
                [],
                .0000001)  # XXX: This will surely make it fast! (?)

            if readable:
                chunk = self.socket.recv(chunk_size)

                if chunk is '':
                    raise RuntimeError('socket connection broken')

                _log.debug('chunk: {!r}'.format(chunk))

                self.send_message(
                    to=self.message_handler,
                    directive='handle_message',
                    body={'chunk': chunk})

            yield self.wait_on_self()

    def send(self, message):
        out = message.body['message']
        length = len(out)
        total_sent = 0
        while total_sent < length:
            sent = self.socket.send(out[total_sent:])

            if sent == 0:
                raise RuntimeError('socket connection broken')

            total_sent += sent

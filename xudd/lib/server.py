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

    def respond(self, message):
        _log.debug('Responding')

        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])
        sock.close()
        del self.requests[message.in_reply_to]
        _log.info('Responded')

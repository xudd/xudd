import logging
import re

from xudd import PY2
from xudd.actor import Actor
from xudd.contrib.irc import ParsedMessage, ParsedParams, ParsedPrefix

_log = logging.getLogger(__name__)


if PY2:
    IRC_EOL = '\r\n'
else:
    IRC_EOL = b'\r\n'


class IRCClient(Actor):
    def __init__(self, hive, id, message_handler=None,
                 encoding='utf8'):
        super(IRC, self).__init__(hive, id)

        self.message_routing.update({
            'handle_chunk': self.handle_chunk,
            'respond': self.respond,
        })
        self.message_handler = message_handler

        self.authenticated = False

        self.encoding = encoding

        if PY2:
            self.incoming = ''
        else:
            self.incoming = b''

    def handle_chunk(self, message):
        self.incoming += message.body['chunk']

        if not self.authenticated:
            _log.error('NOT AUTHENTICATED')
            response = yield self.wait_on_message(
                to=self.message_handler,
                directive='handle_login',
                body={'action': 'login'})

            _log.debug('RESPONSE: {0.body!r}'.format(response))

            if 'line' in response.body:
                raw_message = self.encode(response.body['line'])
                raw_message += IRC_EOL

                _log.debug(' >>> {!r}'.format(raw_message))

                message.reply(
                    directive='send',
                    body={
                        'message': raw_message
                    })

                self.authenticated = True
        else:
            while IRC_EOL in self.incoming:
                line, self.incoming = self.incoming.split(IRC_EOL, 1)

                _log.debug(' <<< {!r}'.format(line))

                line = self.decode(line)

                msg = ParsedMessage(line)
                prefix = ParsedPrefix(msg.prefix)
                params = ParsedParams(msg.params)
                command = msg.command.upper()

                body = {
                    'message': msg,
                    'prefix': prefix,
                    'params': params,
                    'command': command
                }

                response = yield self.wait_on_message(
                    to=self.message_handler,
                    directive='handle_message',
                    body=body)

                if 'line' in response.body:
                    raw_message = self.encode(response.body['line'])
                    raw_message += IRC_EOL

                    _log.debug(' >>> {!r}'.format(raw_message))

                    message.reply(
                        directive='send',
                        body={
                            'message': raw_message
                        })

    def respond(self, message):
        if not 'line' in message.body:
            return

    def decode(self, str_or_bytes):
        if PY2:
            return str_or_bytes.decode(self.encoding, 'replace')
        else:
            return str(str_or_bytes, encoding=self.encoding)

    def encode(self, str_or_unicode):
        if PY2:
            return str_or_unicode.encode(self.encoding, 'replace')
        else:
            return bytes(str_or_unicode, encoding=self.encoding)

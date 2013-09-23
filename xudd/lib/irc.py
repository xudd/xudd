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
        super(IRCClient, self).__init__(hive, id)

        self.message_routing.update({
            'handle_chunk': self.handle_chunk,
        })

        self.message_handler = message_handler

        self.authenticated = False

        self.encoding = encoding

        if PY2:
            self.incoming = ''
        else:
            self.incoming = b''

    def send_if_line(self, original_message, response_from_handler):
        if 'line' in response_from_handler.body:
            lines = [response_from_handler.body['line']]
        elif 'lines' in response_from_handler.body:
            lines = response_from_handler.body['lines']
        else:
            return

        message = ''

        for line in lines:
            _line = self.encode(line) + IRC_EOL
            _log.debug(' >>> {!r}'.format(_line))
            message += _line

        original_message.reply(
            directive=u'send',
            body={
                'message': message
            })


    def handle_chunk(self, message):
        self.incoming += message.body['chunk']

        ## Call the message handler and ask for password &c.
        if not self.authenticated:
            _log.error('NOT AUTHENTICATED')
            response = yield self.wait_on_message(
                to=self.message_handler,
                directive='handle_login')

            self.send_if_line(message, response)

            self.authenticated = True  # XXX: We only assume so

            response = yield self.wait_on_message(
                to=self.message_handler,
                directive='on_authenticated'
            )
            self.send_if_line(message, response)

        ## Parse the ``incoming`` buffer and pass the parsed message to the
        ## message handler
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
                    directive='handle_line',
                    body=body)

                self.send_if_line(message, response)

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

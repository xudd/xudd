import logging
import sys
import traceback

from xudd.lib.tcp import Client
from xudd.lib.irc import IRCClient
from xudd.hive import Hive
from xudd.actor import Actor

_log = logging.getLogger(__name__)


class IRCBot(Actor):
    def __init__(self, hive, id,
                 nick='ppnx',
                 realname='XUDD IRC Client',
                 user='ppnx',
                 password=None):
        super(IRCBot, self).__init__(hive, id)

        self.nick = nick
        self.realname = realname
        self.user = user
        self.password = password

        self.message_routing.update({
            'handle_login': self.handle_login,
            'handle_message': self.handle_message,
        })

    def handle_message(self, message):
        if not 'message' in message.body:
            _log.error('No message in body of {!r}'.format(message))
            # XXX: FOR SOME REASON MESSAGES FROM lib.irc.IRC with
            # directive=handle_login ENDS UP HERE, THIS IS A REALLY UGLY
            # WORKAROUND THAT JUST WORKS
            return self.handle_login(message)

        msg = message.body['message']
        command = message.body['command']
        params = message.body['params']
        prefix = message.body['prefix']

        if 'PING' == command:
            return message.reply(body={'line': 'PONG'})
        elif 'PRIVMSG' == command:
            if params.middle.startswith('#'):
                in_channel = True
                via = params.middle
            else:
                via = prefix.nick

            _log.info('Message from ')

            code = params.trailing[1:]

            if params.middle == self.nick:
                message.reply(body={
                    'line': u'PRIVMSG {0} :{1}'.format(
                        via, msg)
                })

        return message.reply()

    def handle_login(self, message):
        _log.info('Logging in')
        msg = 'USER {user} {hostname} {servername} :{realname}'.format(
                        user=self.user,
                        hostname='*',
                        servername='*',
                        realname=self.realname
                    )
        msg += '\r\n'
        msg += 'NICK {nick}'.format(nick=self.nick)

        message.reply(
            directive='reply',
            body={
                'line': msg
            })


def connect():
    logging.basicConfig(level=logging.DEBUG)

    logging.getLogger('xudd.hive').setLevel(logging.INFO)
    logging.getLogger('xudd.actor').setLevel(logging.INFO)

    hive = Hive()

    hive.create_actor(IRCBot, id='bot')
    irc_id = hive.create_actor(IRCClient, id='irc', message_handler='bot')
    client_id = hive.create_actor(Client, id='tcp_client',
                                  chunk_handler=irc_id)

    hive.send_message(
        to='tcp_client',
        directive='connect',
        body={'host': 'irc.freenode.net', 'port': 6667})


    hive.run()

if __name__ == '__main__':
    connect()

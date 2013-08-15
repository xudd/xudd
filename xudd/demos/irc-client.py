import logging

from xudd.lib.tcp import Client
from xudd.lib.irc import IRC
from xudd.hive import Hive

_log = logging.getLogger(__name__)

def handler(message=None, prefix=None, params=None, command=None):
    _log.debug(message, prefix, params, command)

    return 'PRIVMSG joar: {!r}'.format((message, prefix, params, command))

def connect():
    logging.basicConfig(level=logging.DEBUG)

    logging.getLogger('xudd.hive').setLevel(logging.INFO)
    logging.getLogger('xudd.actor').setLevel(logging.INFO)

    hive = Hive()

    irc_id = hive.create_actor(IRC, id='irc', message_handler=handler)
    client_id = hive.create_actor(Client, id='client', message_handler=irc_id)

    hive.send_message(
        to=client_id,
        directive='connect',
        body={'host': 'irc.freenode.net', 'port': 6667})

    hive.run()

if __name__ == '__main__':
    connect()

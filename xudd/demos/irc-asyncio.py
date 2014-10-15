"""
"""
from __future__ import print_function

import asyncio
import logging
import sys

from xudd.actor import Actor
from xudd.hive import Hive

_log = logging.getLogger(__name__)


IRC_EOL = b'\r\n'


class IrcBot(Actor):
    def __init__(self, hive, id,
                 nick, user=None,
                 realname="XUDD Bot 2",
                 connect_hostname="irc.freenode.net",
                 connect_port=6667):
        super().__init__(hive, id)

        self.realname = realname
        self.nick = nick
        self.user = user or nick

        self.connect_hostname = connect_hostname
        self.connect_port = connect_port

        self.authenticated = False
        self.reader = None
        self.writer = None

        self.message_routing.update(
            {"connect_and_run": self.connect_and_run})

    def connect_and_run(self, message):
        self.reader, self.writer = yield from asyncio.open_connection(
            message.body.get("hostname", self.connect_hostname),
            message.body.get("port", self.connect_port))

        self.login()
        while True:
            line = yield from self.reader.readline()
            line = line.decode("utf-8")
            self.handle_line(line)

    def login(self):
        _log.info('Logging in')
        lines = [
            'USER {user} {hostname} {servername} :{realname}'.format(
                        user=self.user,
                        hostname='*',
                        servername='*',
                        realname=self.realname
            ),
            'NICK {nick}'.format(nick=self.nick)]
        self.send_lines(lines)

    def send_lines(self, lines):
        for line in lines:
            line = line.encode("utf-8") + IRC_EOL
            self.writer.write(line)

    def handle_line(self, line):
        _log.debug(line.strip())


def main():
    logging.basicConfig(level=logging.DEBUG)

    # Fails stupidly if no username given
    try:
        username = sys.argv[1]
    except IndexError:
        raise IndexError("You gotta provide a username as first arg, yo")

    hive = Hive()
    irc_bot = hive.create_actor(IrcBot, username)

    hive.send_message(
        to=irc_bot,
        directive="connect_and_run")

    hive.run()


if __name__ == "__main__":
    main()

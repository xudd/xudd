"""
"""
from __future__ import print_function

import asyncio
import logging

from xudd.actor import Actor
from xudd.hive import Hive

_log = logging.getLogger(__name__)


IRC_EOL = b'\r\n'


class IrcBot(Actor):
    def __init__(self, hive, id,
                 nick="ppnx2", user="ppnx2",
                 realname="XUDD Bot 2"):
        super().__init__(hive, id)

        self.user = user
        self.realname = realname
        self.nick = nick

        self.authenticated = False
        self.reader = None
        self.writer = None

        self.message_routing.update(
            {"connect_and_run": self.connect_and_run})

    def connect_and_run(self, message):
        self.reader, self.writer = yield from asyncio.open_connection(
            message.body.get("hostname", "irc.freenode.net"),
            message.body.get("port", 6667))

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

    hive = Hive()
    irc_bot = hive.create_actor(IrcBot)

    hive.send_message(
        to=irc_bot,
        directive="connect_and_run")

    hive.run()


if __name__ == "__main__":
    main()

"""
"""
from __future__ import print_function

import urllib.parse
import asyncio
import time
import argparse

from xudd.tools import join_id
from xudd.hive import Hive
from xudd.actor import Actor
from xudd.lib.multiprocess import MultiProcessAmbassador


@asyncio.coroutine
def print_http_headers(url):
    url = urllib.parse.urlsplit(url)
    reader, writer = yield from asyncio.open_connection(url.hostname, 80)
    query = (
        "HEAD {url.path} HTTP/1.0\r\n"
        "Host: {url.hostname}\r\n"
        "\r\n").format(url=url)
    writer.write(query.encode("latin-1"))
    while True:
        line = yield from reader.readline()
        if not line:
            break

        line = line.decode("latin1").rstrip()
        if line:
            print("HTTP header> %s" % line)


class WebReader(Actor):
    def __init__(self, hive, id):
        super(WebReader, self).__init__(hive, id)

        self.message_routing.update(
            {"read_webs": self.read_webs,
             "chuckle_end": self.chuckle_end})

    def _setup_chuckle_end(self, future):
        self.hive.send_message(to=self.id, directive="chuckle_end")

    def chuckle_end(self, message):
        print("Haha!  Guess that's the end of that...")
        self.hive.send_shutdown()

    def read_webs(self, message):
        print("before readin")
        future = asyncio.async(print_http_headers(message.body["url"]))
        future.add_done_callback(self._setup_chuckle_end)
        print("after readin")


def main():
    import sys
    url = sys.argv[1]

    hive = Hive()
    web_reader = hive.create_actor(WebReader)

    hive.send_message(
        to=web_reader,
        directive="read_webs",
        body={"url": url})

    hive.run()


if __name__ == "__main__":
    main()

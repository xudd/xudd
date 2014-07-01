"""
Fire this up and it'll wait for messages from pyzmq_listen_sender.py
"""

from __future__ import print_function

import zmq

from xudd.hive import Hive
from xudd.actor import Actor


class Listener(Actor):
    def __init__(self, hive, id):
        super(Listener, self).__init__(hive, id)
        self.message_routing.update(
            {"listen_loop": self.listen_loop})

        self._setup_socket()
        
    def _setup_socket(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("ipc:///tmp/zmqtest")

    def listen_loop(self, message):
        while True:
            if self.socket.poll(10) == 1:
                self.hive.send_message(
                    to=message.body["echoer"],
                    directive="echo",
                    body={"text": self.socket.recv_unicode()})
            # else:
            #     print("skipped this round")

            yield self.wait_on_self()


class Echoer(Actor):
    def __init__(self, hive, id):
        super(Echoer, self).__init__(hive, id)
        self.message_routing.update(
            {"echo": self.echo})

    def echo(self, message):
        print(message.body["text"])


def main():
    hive = Hive()

    listener = hive.create_actor(
        Listener, id="listener")
    echoer = hive.create_actor(
        Echoer, id="echoer")

    hive.send_message(
        to=listener,
        directive="listen_loop",
        body={"echoer": echoer})

    hive.run()


if __name__ == "__main__":
    main()

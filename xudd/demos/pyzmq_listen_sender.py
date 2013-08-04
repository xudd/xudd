"""
To be used with pyzmq_listen_test.py

Fire this up and you can start sending messages to the listener.
"""

import zmq

from xudd import PY2


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("ipc:///tmp/zmqtest")

    while True:
        if PY2:
            message_to_send = raw_input(u"RETRO_PROMPT> ")
        else:
            message_to_send = input(u"RETRO_PROMPT> ")

        if message_to_send == u"quit":
            return

        socket.send_unicode(message_to_send)


if __name__ == "__main__":
    main()


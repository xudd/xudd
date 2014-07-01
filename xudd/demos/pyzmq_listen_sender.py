"""
To be used with pyzmq_listen_listener.py

Fire this up and you can start sending messages to the listener.
"""

import zmq


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("ipc:///tmp/zmqtest")

    while True:
        message_to_send = input(u"RETRO_PROMPT> ")

        if message_to_send == u"quit":
            return

        socket.send_unicode(message_to_send)


if __name__ == "__main__":
    main()


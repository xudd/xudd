.. _asyncio-support:

===============
Asyncio Support
===============

Behind the scenes, XUDD makes use of
`asyncio <https://docs.python.org/3.4/library/asyncio.html>`_
to do message passing.  But XUDD has a nice interoperability layer
where your actors can interface nicely with the rest of the asyncio
ecosystem.

Like message passing with XUDD, asyncio makes heavy use of `yield
from`.  However, the astute reader may notice that the way this is
called is pretty different than XUDD's message passing... this is
because how `yield from` would work in XUDD was designed far before
asyncio integration.

Nonetheless, the differences are not so big, and thanks to asyncio and
XUDD's clever interoperability layer, you can make use of a tremendous
amount of asyncio features such as asynchronous network and filesystem
communication, timer systems, and much more.

Asyncio by example
==================

A simple IRC bot
----------------

For a good example of this, let's look at this simple IRC bot (no need
to follow it all, we'll break it down):

.. include:: ../../xudd/demos/irc-asyncio.py
   :code: python

This bot, as written above, doesn't do much... it just logs in and
spits out all messages it receives to the log as debugging info.

Nonetheless, that might look daunting.  From the `main()` method
though, it's obvious that the first thing done is to handle a
`connect_and_run` method on the IRC bot (the handler of which just so
happens to be `connect_and_run()`.  So let's look at that method in
detail::

    def connect_and_run(self, message):
        self.reader, self.writer = yield from asyncio.open_connection(
            message.body.get("hostname", self.connect_hostname),
            message.body.get("port", self.connect_port))

        self.login()
        while True:
            line = yield from self.reader.readline()
            line = line.decode("utf-8")
            self.handle_line(line)

This little snippet of code does almost the entirety of the busywork
in this IRC bot.



A bit of clarification
----------------------

XUDD didn't always use asyncio, and in fact, the goal of using "yield
from" in XUDD existed before asyncio existed (or even before "yield
from" itself did, but that's a bit of a digression).  Because of this, 

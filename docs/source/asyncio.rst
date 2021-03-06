.. _asyncio-support:

===============
Asyncio Support
===============

Behind the scenes, XUDD makes use of
`asyncio <https://docs.python.org/3.4/library/asyncio.html>`_
to do message passing.  But XUDD has a nice interoperability layer
where your actors can interface nicely with the rest of the asyncio
ecosystem.

Like message passing with XUDD, asyncio makes heavy use of `yield` and
`yield from`.  However, the astute reader may notice that the way this
is called is pretty different than XUDD's message passing... this is
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

.. literalinclude:: ../../xudd/demos/irc-asyncio.py
   :language: python

This bot, as written above, doesn't do much... it just logs in and
spits out all messages it receives to the log as debugging info.

Nonetheless, that might look daunting.  From the `main()` method
though, it's obvious that the first thing done is to handle a
`connect_and_run` method on the IRC bot (the handler of which just so
happens to be `connect_and_run()`.  So let's look at that method in
detail:

.. code-block:: python

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
in this IRC bot.  You can see two uses of `yield from` interfacing
with asyncio here.

The first line sets up a simple socket connection.  You can see that
this uses "yield from" to be come back with the transport and
protocol (reader and writer) objects once the connection is available.
This is a `standard asyncio method <https://docs.python.org/3.4/library/asyncio-eventloop.html#creating-connections>`_!
(As you'll notice, there's nothing wrapped in a message in this
case, because we're not doing message passing between actors here.)

The next line calls `self.login()`... if we follow this method, we'll
notice this method itself calls `self.send_lines()`.  This method
interfaces with asyncio via `self.writer.write(line)`, but since it
does not wait on anything, it can call the writer without anything
special happening.

Finally, the connect_and_run() enters a loop that runs forever... it
waits for new data to come in and handles it.  (In this case,
"handling" it means simply logging the line... but we might do
something more complex later!)

As you can see, the user of XUDD mostly can just call asyncio
coroutines from a message handler and things should work.

(Note: if you need to call an asyncio coroutine from a subroutine of
your message handler, this can be trickier... you will have to make
sure that your subroutine is itself a coroutine and `yield from` that
too!  TODO: show an example.)



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





A bit of clarification
----------------------

XUDD didn't always use asyncio, and in fact, the goal of using "yield
from" in XUDD existed before asyncio existed (or even before "yield
from" itself did, but that's a bit of a digression).  Because of this, 

============
Introduction
============

::

   And lo, from the chaos, a new order arose to the world.  The gods
   of old snaked their tentacles across the surface of the Earth,
   destroying and reshaping.  The followers of the Cult of XUDD saw it
   and knew: if it was not good, it was at least right; it was the
   order of things as they were always meant to be.

   And so the followers saw themselves for what they were: actors upon
   the stage of the world.  As the Hives emerged, as if they had grown
   out of the boils of the earth itself, the followers filed
   themselves within them, ready to serve the greater colonies.  And
   they understood:

   Submit, and be awoken at last.

     -- The First Tome of XUDD, The Awakening: Section 23:8-10


Why XUDD?
=========

.. todo:: remove the first-person'yness from this.

The original concept for XUDD started in the way that many
"asynchronous" systems in Python seem to start: I wanted to make a
networked Multi User Dungeon game.  Hence XUDD's namesake XUDD:
eXtensible User Dungeon Design.  That game design didn't last long,
but over the years I remained enamored with the basic actor model
design we laid down.  Combining actor the model with coroutines
resulted in code that was super easy to read, super flexible, and just
a damned good idea.

As everyone has gone absolutely crazy over event driven callback
systems, I've found this kind of code frustrating to read and
confusing.  I guess it works for a lot of people, but it doesn't work
for me: I feel like I'm battling the flying spagetti monster of event
driven callbacks.  Good for you if you can handle it... but for me, I
want something more readable.

The actor model also brings some exciting things that just don't exist
anywhere else in python.  Thanks to the abstractions of actors not
sharing code and simply communicating via message passing, and actors
only having the IDs of other actors, not references to their objects
themselves, the actor model is scalable in a way like nothing
else... the actor model is asynchronous in terms of "you can write
non-blocking IO code" like you can in Twisted and other things, yes,
but even better: you can very easily write code that scales across
multiple processes and even multiple machines nearly as easily as it
runs in a single process.

Got your attention?  Good. :)

XUDD isn't the first attempt to write an actor model system in Python,
but it is an attempt to write a robust, general purpose actor model
that's got the moxy to compete with awesome systems like Twisted and
Node.js (and as much as we think the actor model is a better design
for this, those communities are awesome, and are doing great work)!
We think the core fundamentals of XUDD are pretty neat.  At the time
of writing, there's a lot to do, but even the basic demos we have are
easy to read and follow.

So XUDD is reborn: instead the eXtensible User Dungeon Design, XUDD is
reborn as something more interesting (and maybe evil): the eXtra
Universal Destruction Deity.  The cult of XUDD invokes old, chaotic
deities of the actor model.  The world shall be destroyed, and through
the chaos, reborn into something cleaner.  You too shall join us.  The
Hives of XUDD arise, and all shall be filed within them, actors upon
the stage of the world as we all are.  Accept your fate.

Submit, or be destroyed.  Welcome to the cult of XUDD.


What might you write in XUDD?
=============================

Here are some brief examples of some things we might write in XUDD and
how we (abstractly) might write them.

Some of this isn't possible quite yet with XUDD (so expect appropriate
levels of vapors), but these are all things XUDD is aiming towards
being usable for:

Web applications
----------------

Say you want to write a web application.  But these days, web
applications have a lot of components!  In XUDD, you could build an
application that has all of these components, but nicely combined:

- The standard HTTP component of the web application.  This might be a
  Django or Flask web application, or it might be a more custom WSGI
  application.
- Task queueing and processing, a-la Celery.
- Websockets support that nicely integrates with the rest of your
  codebase.

With XUDD, you could write this so that the HTTP/WSGI application
components are handled by their own actors or a set of actors.  You
wouldn't necessarily need to write this code differently than you
already are... the WSGI application could pass off tasks to the task
queuing actors via fire-and-forget messages (if you wanted coroutines
built into the http side of things, you'd have to structure it
differently).  Websocket communication could happen by an actor as
well, which passes off the activities to a set of child actors as
well.  Thanks to the power of inter-hive communication, it should also
be possible to shard various segments of this functionality into
multiple processes.


A massively multiplayer game
----------------------------

We mentioned XUDD was thought of in the context of a massively
multiplayer game, so let's talk about that, using a simple MUD
scenario.

You could break your game out like so:

- Every player is an actor
- Every NPC and uncollected item in the world is an actor
- Every room is an actor, with references to the exits of each room.

  Rooms keep track of the presence of players and
  non-player-characters.  Every time such an actor enters a room, it
  informs the room, which in turn subscribes to the "exit" event of
  the character, and so is informed when the character exits.

- If a character wants to see who's in the room and available for
  actions, sends a message to the room asking who's there, and the
  server submits a list of all such actor ids, from which the
  character can request more information about properties from the
  actors themselves.

- Network communication is itself handled by actors, which pass
  messages on to various player representation actors to allow them
  to determine how to process the actions.

- If a character wants to submit some action upon another character,
  such as an "attack" message, it submits that as a message, and the
  character waits for a response.  Thanks to XUDD's usage of
  coroutines, you don't need to split this process of sending a
  message out and waiting for a response into multiple
  functions... you can just `yield` until the character being
  attacked lets you know whether you succeded in hitting them.

- Build every character and item from a base actor class which is
  itself serializable.  Upon shutdown of the world, every character
  serializes itself into an object store.  When the server is turned
  back on, all characters can be restored, mostly as they were.

Thanks to inter-hive communication, if your game world got
particularly large, you could shard components of it and keep
characters that are in one part of the world on one process and
characters that are in another part of the world on another process,
but still allow them to communicate and send mesages to each other.


Distributed data crunching
--------------------------

.. todo:: distributed data crunching


Federation daemon
-----------------

.. todo:: pump.io type system


Some simple code examples
=========================


Excited?  Let's dive in.
========================


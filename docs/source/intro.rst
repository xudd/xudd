============
Introduction
============

::

   And lo, from the chaos, a new order arose to the world.  The gods
   of old snaked their tentacles across the surface of the Earth,
   destroying and reshaping.  The followers of the Cult of XUDD saw it
   and knew: if it was not good, it was at least right; it was the
   order of things as they were always meant to be.  Submit, and be
   awoken at last.
     -- The First Tome of XUDD, The Awakening: Section 23:8


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
how we might write them.

.. todo:: web applications
.. todo:: mmorpg
.. todo:: distributed data crunching
.. todo:: pump.io type system


Some simple code examples
=========================


Excited?  Let's dive in.
========================


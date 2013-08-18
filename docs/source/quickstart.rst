Let's go over the core concepts and do a quick demo.

The premise
===========

Imagine that you have a security robot that's on a mission... it has
to go through a room in a warehouse and searches for infected droids.
Any infected droids it finds it terminates.

This means we'll have the following components:

- The worker droids, which are either infected or not infected.  These
  will be actors.
- A security robot, which will scan for infected droids and vaporizes
  any infected droid with laser blasts.  This will also be an actor.
- A room that both the security robot and the droids will all be in.
  This will also be an actor.
- An overseer, which initializes the entire simulation (including the
  room, all droids, and the security robot).
- A hive, on which the above actors will register themselves and be
  managed by.

That's pretty manageable!  Let's get started.

Setting it all up
=================

Main function and the Hive
--------------------------

Let's start out by importing our needed functions and setting up the
main function.

.. code-block:: python

    from __future__ import print_function
    import random
    
    from xudd.hive import Hive
    from xudd.actor import Actor
    
    
    class Overseer(Actor):
        pass

    
    def main():
        # Create the hive
        hive = Hive()
    
        # Add overseer, who populates the world and runs the simulation
        hive.create_actor(Overseer, id="overseer")
        hive.send_message(
            to="overseer",
            directive="init_world")
    
        # Actually initialize the world
        hive.run()
    
    
    if __name__ == "__main__":
        main()

Okay, not too hard!  As you can see, we've laid down the basic
structure, though not quite everything we need is there.  Let's walk
through the `main()` function:

- First, it creates the Hive object.  This object will manage the
  actors we add to it as well as their execution.
- Next, create an Overseer actor.  Any arguments you pass in here will
  be passed in as positional and keyword arguments to the actor's
  init.  As you can see here, you can also pass in the id of an actor
  explicitly (though you don't have to, and usually, you won't.)
- `Hive.create_actor()` returns the id of the actor we initialized.
  Usually you'd keep a reference to such an id and use that to
  communicate with the actor; in this case, we already know what the
  id is since we set it up explicitly.  (Later in this document, we'll
  use whatever id is returned by `create_actor()`.)
- Next, we send a message to the overseer with the directive
  "init_world".  Once the hive starts, the Overseer will look to see
  if it has a message handler for that directive and will try to
  perform whatever actions are needed.
- Then we actually start the Hive up... it runs till the simultation
  completes, then the program exits.

You might be wondering, why not do this instead?

.. code-block:: python

    overseer = Overseer(id="overseer")
    overseer.init_world()

That looks simple enough, right?  But it doesn't match the pattern
that XUDD uses.

Since we're following the actor model, you don't get direct access
to the actor you create, just a reference to their id (the actor
model avoids the kind of complexities one might run into in other
concurrent models by having a "shared nothing" environment).  Don't
worry, it's very easy to code actors that can negotiate doing just
about anything... but it's up to the actual actor to do so.

There are significant advantages to doing this... these might not be
obvious immediately (and don't worry if they aren't) but by following
the actor model in the way that XUDD does, several features are opened
to us:

- It's easy to write concurrent, non-blocking code that doesn't
  generally have problems with issues like managing locking (or
  avoiding deadlocks!); by moving the domain of a resource to a single
  actor and allowing each actor to execute just one instruction at a
  time, actors can independently and safely manage resources.
- By abstracting the system to actors and message passing, we can
  actually spread workloads across multiple processes or even multiple
  machines (that's right, concurrency without fighting the GIL!)
  nearly as easily as writing it all to run in one process.  (Often
  the code you write for just one process can easily run on multiple
  processes!)

But anyway, that's getting a bit ahead of ourselves.  As you may have
noticed, we haven't even gotten the Overseer working yet... this code
doesn't run!  So let's actually flesh that out.

Setting up the Overseer
-----------------------




Building a simple room
======================

Building the worker droids
==========================

Building the security robot
===========================

Connect everything together and run!
====================================

Where to go from here
=====================




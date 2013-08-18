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

(By the way: if you're impatient, you can see a fully finished verison
of this demo in `xudd/demos/simple_robotscanner.py`, which is included
with XUDD!)

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

Replace the Overseer class with this code:


.. code-block:: python

    def droid_list(num_clean, num_infected):
        """
        Create a list of (shuffled) clean droids and infected droids
        """
        droids = [Flase] * num_clean + [True] * num_infected
        random.shuffle(droids)
        return droids
        
    
    class Overseer(Actor):
        """
        Actor that initializes the world of this demo and starts the mission.
        """
        def __init__(self, hive, id):
            super(Overseer, self).__init__(hive, id)
    
            self.message_routing.update(
                {"init_world": self.init_world})
    
        def init_world(self, message):
            """
            Initialize the world we're operating in for this demo.
            """
            # Create room and droids
            room = self.hive.create_actor(WarehouseRoom)
            
            for is_droid_clean in droid_list(5, 8):
                droid = self.hive.create_actor(
                    Droid, infected=is_droid_clean, room=room)
                yield self.wait_on_message(
                    to=droid,
                    directive="register_with_room")
    
            # Add security robot
            security_robot = self.hive.create_actor(SecurityRobot)
    
            # Tell the security robot to begin their mission
            self.hive.send_message(
                to=security_robot,
                directive="begin_mission",
                body={"room": room})


Alright, what does this do?

First of all, we added a droid_list function.  This isn't very
complex... it just creates a shuffled list of True and False objects,
to represent which droids are infected and which aren't.  Pretty
simple.

This Overseer actor is pretty simple to understand.  It's mostly just
used to set up the world that the droids and security robot are going
to run in.

Take a look at the Overseer `__init__` method.  You'll notice it takes
two parameters, `hive` and `id`.  The `hive` object is not actually a
reference to the Hive itself... instead, actors get reference to a
`HiveProxy` object.  This both ensures that all actors get a universal
API for interacting with their hive, even if that hive has some
unusual implementation details.  It also tries to make sure that
actors don't try to poke at parts of the hive that shey shouldn't be.
The `id` attribute is exactly what it sounds like, the id of the
actor, as the rest of the world sees it.

In the `__init__` method, the Overseer extends its `message_routing`
attribute.  This specifies what methods should be called when it gets
a message with a certain directive.

Next, let's look at the Overseer's `init_world` method.  This does
exactly what it says it does; it sets up the rest of the actors and
gets them running.  Let's dissect it piece by piece:

- It receives a message as its first argument.  This will be of course
  a message constructed from the parameters in the main() method.
  This comes wrapped in a special `Message` object.  We didn't supply
  anything other than the `to` field and the `directive` so there's
  not too much to look at here.
- First, you'll see that it creates the room.  Pretty simple; this API
  is exactly as it was in the `main()` function to create the Overseer
  (except this time we're using the HiveProxy rather than the Hive
  itself).  One distinction though: this time we don't specify the id.
  Instead, we assign the id that's generated and returned by
  `create_actor` to the `room` variable.
- Next, we loop over a list of randomly shuffled `True` and `False`
  variables as generated by our `droid_list` method representing
  infected and clean droids respectively.  For each of these:

  - We create an actor using the create_actor method.  As you can see
    though, this time we pass in some keyword parameters that are sent
    to the constructor of the Droid class when the hive initializes it.

  - Next we send a message... but wait!  We use a different pattern
    than the simple `send_message` we used before.  What's this
    `yield` thing, and how does `self.wait_on_message` differ from
    `send_message`?

    By adding a yield to this statement, we've transformed this
    message handler into a `coroutine`.  This is pretty awesome,
    because it means that whenever the message hits a `yield`, the
    coroutine *suspends execution* to be woken up later!  In this
    case, our coroutine needs to make sure that this droid properly
    registers itself with its room before we can continue.  Keep in
    mind that if you're writing asynchronous code, there's no
    guarantee in what order messages will execute (especially if
    you're splitting things across processes)... you don't want the
    security robot to scan the room for infected droids and miss some
    because it started scanning before the droids registered
    themselves with the room.

    By yielding, we avoid that race condition.  Instead, our
    init_world method suspends into the background until the message
    we sent out has been processed and our actor gets woken up again
    with the confirmation that this task has happened.

    By using `yield` and `self.wait_on_message` together, we can write
    non-blocking asynchronous code without ending up in callback hell.
    If we were doing this with callbacks only, we couldn't have this
    all in one function.  Thanks to XUDD's use of coroutines, you can
    write asynchronous code that feels natural.  Pretty cool right?

- Now that all our droids are set up, we can initialize our
  SecurityRobot and give it the directive to `begin_mission`.  This
  should look fairly familiar!  There's only one new thing this time,
  which is the body of the message.  This is a dictionary that gives
  parameters to the handler of the message... you can put whatever you
  need to in here (just make sure your actors agree on what it means).
  In this case, we need to tell the SecurityRobot what room it's
  investigating.
  
By the way, you might notice the last command doesn't use a yield and
just uses the simple `send_message()` method.  Nothing else happened
after this last `send_message` but if there were, it would just keep
continuing to execute.  This is because XUDD uses two patterns for
message sending:

- **fire and forget:** a simple `hive.send_message()` simply sends the
  message and we continue on our way.  We don't need to sit around
  waiting for a reply, so we can continue executing things and those
  messages will be processed when they are gotten to.
- **yielding for a reply:** when we use `yield` and `wait_on_message`
  together, this is because either the order of execution is important
  or because we need some important information in reply (more on this
  later) before we can continue.  XUDD's coroutine nature makes this
  fairly easy.

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




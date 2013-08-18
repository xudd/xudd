=============
XUDD Tutorial
=============

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

This was a lot of explaination for a small amount of code!  But don't
worry, we covered a lot of ground here.


Building a simple room
======================

Now let's build the room for our droids to go in:

.. code-block:: python

    class WarehouseRoom(Actor):
        """
        A room full of robots.
        """
        def __init__(self, hive, id):
            super(WarehouseRoom, self).__init__(hive, id)
            self.droids = []
    
            self.message_routing.update(
                {"register_droid": self.register_droid,
                 "list_droids": self.list_droids})
    
        def register_droid(self, message):
            self.droids.append(message.body['droid_id'])

        def list_droids(self, message):
            message.reply(
                {"droid_ids": self.droids})
    

A lot of this should look familiar.  We added an attribute to keep
track of droids and a couple of methods for registering and listing
droids, but that's about it.

The `register_droid` method expects a parameter in its body of
`droid_id` which tells it which droid is being hooked up here, and it
adds it to its own list.

The `list_droids` method does something interesting: it uses
`message.reply()`.  This is a lazy tool to make replying to messages
easy.  XUDD comes with a number of tools related to replying and
auto-replying... see :ref:`replying_to_messages` for details.  As you
might have guessed, the first parameter to `message.reply` is the body
of the response (we already know who the recipient is, and XUDD simply
marks the directive of a reply as "reply"... usually it doesn't matter
because it's passed to a coroutine-in-waiting anyway).  We'll come
back to `list_droids` later when we build our SecurityRobot.

Building the worker droids
==========================

Now to add the droids!

.. code-block:: python

    class Droid(Actor):
        """
        A droid that may or may not be infected!
    
        What will happen?  Stay tuned!
        """
        def __init__(self, hive, id, room, infected=False):
            super(Droid, self).__init__(hive, id)
            self.infected = infected
            self.hp = 50
            self.room = room
    
            self.message_routing.update(
                {"infection_expose": self.infection_expose,
                 "get_shot": self.get_shot,
                 "register_with_room": self.register_with_room})
    
        def register_with_room(self, message):
            yield self.wait_on_message(
                to=self.room,
                directive="register_droid",
                body={"droid_id": self.id})
    
        def infection_expose(self, message):
            message.reply(
                {"is_infected": self.infected})
    
        def get_shot(self, message):
            damage = random.randrange(0, 60)
            self.hp -= damage
            alive = self.hp > 0
    
            message.reply(
                body={
                    "hp_left": self.hp,
                    "damage_taken": damage,
                    "alive": alive})
    
            if not alive:
                self.hive.remove_actor(self.id)

As you can see, the droid accepts some constructor arguments about its
room, its id, and whether or not it's infected and keeps track of
these states itself.

`register_with_room` should be fairly obvious by now in how it works.
The only surprising thing is possibly that this message yields on a
reply, but the room's "register_droid" method that we built earlier
never explicitly replies!  How does this work?  Again, XUDD includes
some smart behavior so that messages which "expect" replies should
generally get one assuming the other actor handles their
message... even if it doesn't bother to construct an explicit reply!
See :ref:`replying_to_messages` for details.

Other than that, the only new thing here is the `hive.remove_actor()`
component of the `get_shot` method.  Yes, it does exactly what it
sounds like... it takes that actor off the hive.


Building the security robot
===========================

Now that we've gone through the above, we should have all the
information we need to understand the `SecurityRobot` class!

.. code-block:: python

    ALIVE_FORMAT = "Droid %s shot; taken %s damage. Still alive... %s hp left."
    DEAD_FORMAT = "Droid %s shot; taken %s damage. Terminated."
    
    
    class SecurityRobot(Actor):
        """
        Security robot... designed to seek out and destroy infected droids.
        """
        def __init__(self, hive, id):
            super(SecurityRobot, self).__init__(hive, id)
    
            # The room we're currently in
            self.room = None
    
            self.message_routing.update(
                {"begin_mission": self.begin_mission})
    
        def __droid_status_format(self, shot_response):
            if shot_response.body["alive"]:
                return ALIVE_FORMAT % (
                    shot_response.from_id,
                    shot_response.body["damage_taken"],
                    shot_response.body["hp_left"])
            else:
                return DEAD_FORMAT % (
                    shot_response.from_id,
                    shot_response.body["damage_taken"])
    
        def begin_mission(self, message):
            self.room = message.body['room']
    
            print("Entering room %s..." % self.room)
    
            # Find all the droids in this room and exterminate the
            # infected ones.
            response = yield self.wait_on_message(
                to=self.room,
                directive="list_droids")
            for droid_id in response.body["droid_ids"]:
                response = yield self.wait_on_message(
                    to=droid_id,
                    directive="infection_expose")
    
                # If the droid is clean, let the overseer know and move on.
                if not response.body["is_infected"]:
                    print("%s is clean... moving on." % droid_id)
                    continue
    
                # Let the overseer know we found an infected droid
                # and are engaging
                print("%s found to be infected... taking out" % droid_id)
    
                # Keep firing till it's dead.
                infected_droid_alive = True
                while infected_droid_alive:
                    response = yield self.wait_on_message(
                        to=droid_id,
                        directive="get_shot")
    
                    # Relay the droid status
                    print(self.__droid_status_format(response))
    
                    infected_droid_alive = response.body["alive"]
    
            # Good job everyone! Shut down the operation.
            print("Mission accomplished.")
            self.hive.send_shutdown()

While complex looking, there's very little here we haven't seen before
already, though there are a couple of things!  A quick summary of the
behavior of begin_mission:

- It starts out pulling the room it is supposed to operate in based
  off of the room supplied in the message argument's body.
- It then sends a message to that room asking for a list of all droids
  within said room.
- It then checks each droid in the returned list:
  - First it sees if the droid is infected (this is a bit abstract of
    course anyway; presume the SecurityRobot is sending some code that
    exposes that information if you like to think of this as a story.
    Anyway, in the actual code, the droids just return a boolean in
    their response.
  - If the droid is clean, it moves on to the next one.  Otherwise...
  - The SecurityRobot, having confirmed that this robot is a threat,
    begins firing shots.  Messages are exchanged confirming how much
    damage is taken and whether or not the droid is still alive.  The
    SecurityRobot fires at the droid until it's confirmed to be dead.
- Once that's all done, the SecurityRobot declares "mission accomplished"
  and shuts down the hive.  Simulation over!

So!  Lots of code, but most of it familiar.  There are two new things though!

Previously when we wrote code, we might have yielded on reply just
to confirm that the message we sent was handled before we continued.
In this case, we actually need some data.  You may notice that
there's a new format here:

.. code-block:: python

    response = yield self.wait_on_message(
        to=recipient
        directive="some_directive")

Any time that a coroutine is resumed after being suspended with a
yield, that's because the actor received a message "in_reply_to" the
original outgoing message's message id.  Since we're getting a message
back, we can of course look at that message... hence the `response`
being assigned to the left of the yield.  This is another Message
object, just like the message argument passed in at the start of the
message handler.

This means that if you need to write complex asynchronous logic that
needs message passed around back and forth, writing such code looks
nearly as simple as normal method calling.  It's just that this time,
it's encapsulated in message passing!  But imagine trying to
accomplish this method above with callbacks... it would require
splitting between a lot of callbacks.  Nested inline or not, that can
get pretty confusing.  With XUDD, it's easy!

The last thing that's new is the `self.hive.send_shutdown()` call.
Yes, this does exactly what it sounds like... it shuts down the Hive.
Simulation over!


Okay!  Let's run this thing!
============================

Okay, whew!  That was a lot of code, and a lot of explaining!  What
does it actually look like when we run it?  It's mostly what you'd
expect::

    $ python xudd/demos/simple_robotscanner.py 
    Entering room 6pjMdqWIQKGrELiAAcmwwQ...
    iHrqJnTmT_yEmzQxQuA2uA is clean... moving on.
    QTqPLAsnSq2VFIbF0EGPrw found to be infected... taking out
    Droid QTqPLAsnSq2VFIbF0EGPrw shot; taken 42 damage. Still alive... 8 hp left.
    Droid QTqPLAsnSq2VFIbF0EGPrw shot; taken 33 damage. Terminated.
    ATaO3FQzTZmAv6zOvlB3LQ is clean... moving on.
    Ays2zH70TXCwA7FTkZKGug found to be infected... taking out
    Droid Ays2zH70TXCwA7FTkZKGug shot; taken 31 damage. Still alive... 19 hp left.
    Droid Ays2zH70TXCwA7FTkZKGug shot; taken 11 damage. Still alive... 8 hp left.
    Droid Ays2zH70TXCwA7FTkZKGug shot; taken 34 damage. Terminated.
    qrKnae_7QF237HVZiO-gKw found to be infected... taking out
    Droid qrKnae_7QF237HVZiO-gKw shot; taken 14 damage. Still alive... 36 hp left.
    Droid qrKnae_7QF237HVZiO-gKw shot; taken 54 damage. Terminated.
    cMrc96qGRzWP9CtY4wh70A found to be infected... taking out
    Droid cMrc96qGRzWP9CtY4wh70A shot; taken 48 damage. Still alive... 2 hp left.
    Droid cMrc96qGRzWP9CtY4wh70A shot; taken 15 damage. Terminated.
    gB4LFt3IRk-rfL8U2TUPnQ is clean... moving on.
    SIvh6l24TIKSH7y3M1MXDQ found to be infected... taking out
    Droid SIvh6l24TIKSH7y3M1MXDQ shot; taken 38 damage. Still alive... 12 hp left.
    Droid SIvh6l24TIKSH7y3M1MXDQ shot; taken 40 damage. Terminated.
    nunaOJWNQVK2Ya9oB3UI8Q found to be infected... taking out
    Droid nunaOJWNQVK2Ya9oB3UI8Q shot; taken 40 damage. Still alive... 10 hp left.
    Droid nunaOJWNQVK2Ya9oB3UI8Q shot; taken 12 damage. Terminated.
    2JPFYDhpQ-ijOehrwfgIEA found to be infected... taking out
    Droid 2JPFYDhpQ-ijOehrwfgIEA shot; taken 33 damage. Still alive... 17 hp left.
    Droid 2JPFYDhpQ-ijOehrwfgIEA shot; taken 35 damage. Terminated.
    JwIDRV2eS5mAdIX_s9zbdA is clean... moving on.
    Kg07A6hCRMC3eFHE4eDcvA found to be infected... taking out
    Droid Kg07A6hCRMC3eFHE4eDcvA shot; taken 36 damage. Still alive... 14 hp left.
    Droid Kg07A6hCRMC3eFHE4eDcvA shot; taken 21 damage. Terminated.
    TxMl7_-9S5OGsNDcJ0reYw is clean... moving on.
    Mission accomplished.

Pretty cool eh?  If you made it this far, nice work!  That was a lot
of explaining above, but you now the basics to get up and running
coding in XUDD.

Where to go from here
=====================

If you want to see the completed demo, this demo is included with XUDD.
Check out `xudd/demos/simple_robotscanner.py`.

If you want to look at a slightly more complex version, there's also
`xudd/demos/robotscanner.py` which has several extra layers: multiple
rooms, sending feedback back to the Overseer, etc.  `robotscanner.py`
is the first program ever written in XUDD, and was written before the
actual system was completed with very few modifications.  We're happy
to say that the initial demo worked with very few tweaks after the
initial pieces of the engine fell into place... this is partly because
XUDD's design is so simple!  The above may seem like a lot of code,
but we hope you'll find that XUDD's implementation of the actor model
is straightforward, easy to understand, and comfortable to code in.

If you're looking for more code examples, there's some more in
`xudd/demos/` as well.

And of course, if you're ready to start learning more and doing more
coding, you should move on with reading this manual.

Good luck, and have fun!

.. _core-design:

===========
Core design
===========

High level overview
===================

Summary of actors, messages, and hives
--------------------------------------

This document focuses on XUDD's core design.  XUDD follows the actor
model.  The high level of this is that 

There are three essential components to XUDD's design:

- **Actors:** Actors are encapsulations of some functionality.  They
  run independently of each other and manage their own resources.

  Actors do not directly interfere with each others resources, but
  they have mechanisms, via message passing, to get properties of
  each other, request changes, or some other actions.  Actors can
  also spawn other actors via their relationship with their Hive.
  Actors do not get direct access to other actors as objects, but
  instead just get references to their ids.  This is a feature: in
  theory this means that actors can just as easily communicate with
  an actor as if it is local as if it were over the network.

  In XUDD's design, Actors are generally not "always
  running"... instead, they are woken up as needed to process
  messages.  (The exception to this being "Dedicated Actors"; more on
  this later.)

- **Messages:** As said, actors communicate via message passing.
  Messages are easy to understand: like email, they have information
  about who the message is from, instructions on who the message can
  go to, as well as a body of information (in this case, a
  dictionary/hashtable).

  They also contain some other information, such as "directives" that
  specify what action the receiving actor should take (assuming they
  know how to handle such things), and can inform the receiving actor
  that they are waiting on a response (more on this and coroutines
  later).

  Messages also include tooling so they can be serialized and sent
  between processes or over a network.

- **The Hive:** Every actor is associated with a "Hive", which
  manages a set of actors.  The Hive is responsible for passing
  messages from actor to actor.  For standard actors, the Hive also
  handles "waking actors up" and handling their execution of tasks.
  (More on this later, since that wording is possibly confusing.)

  Actors do not get direct access to the Hive, but instead have a
  "HiveProxy" object.  They use this to send messages from actor to
  actor, initializing new actors, or requesting shutdown of the hive
  and all actors.


These concepts are expanded on later in this document.  Additional
features/components that are planned as part of XUDD's design (some of
these are yet to be implemented):

- **Inter-hive messaging:** 
- **Dedicated actors:**
- **Actor "event" subscriptions:**
- **Property API:**
- **Actor serialization:**

Tying it all together
---------------------

So, the above explains the relationships between actors, messaging,
and hives.  

::

  ACTOR AND HIVE BASICS

    .--.     .--.     .--. 
   ( o_o)   ( =_=)   (@_@ )
   ,'--',   ,'--',   ,'--',     
   |  A |   |  B |   | C  |
   '----'   '----'   '----'
    .  ^     .  ^     .  ^
    |  |     |  |     |  |
  [HP] |   [HP] |   [HP] |
    |  |     |  |     |  |
    V  '     V  '     V  '
  .------------------------.
  |         HIVE           |
  '------------------------'

Here we have the basic relationship between a hive and three of its
actors, A B and C.  Each one has its own unique id, shared by no other
actor on the hive.  You can see that there are also relationships
between an actor on the hive.  The hive has direct access to an actor,
but actors don't have direct access to the hive... they have to go
through a HiveProxy.  There's good reason for this: hives may have
more methods than should be exposed to actors.  In fact, it's entirely
possible for an actor to be hooked up to a hive that operates very
differently than the "basic" hive that XUDD ships with.  By using the
HiveProxy, the actor doesn't actually need to know anything about how
the Hive works: as long as it uses the HiveProxy methods, those
operate just fine.

You can see how this works in code:

.. todo:: Add this code


Actors
======

Instantiating actors
--------------------

Instantiating an actor is easy.  You can use a reference to the hive
to actually initialize an actor, like so:

.. code-block:: python

    hive = Hive()

    # Create an actor with no additional parameters
    evil_bot = hive.create_actor(
        EvilRobot)

    # Create an actor with specific arguments and keyword arguments
    # in this case, the first argument is the BattleBot's infantry rank
    minion_bot = hive.create_actor(
        BattleBot, "minion",
        weapons=["pokey stick"])

    # We can also assign an explicit id, as long as it's unique, and not "hive"
    # (that's reserved for the hive)
    admiral_bot = hive.create_actor(
        BattleBot, "admiral",
        weapons=["missiles", "spears", "deathray"],
        id="admiral_robo")

In each case, the value returned by hive.create_actor is not the actor
itself, but an id (a unicode string) that the actor can later be
messaged with.

The core properties of an actor
-------------------------------

Technically, an actor is only *required* to have the following properties:

1. It should accept two positional arguments: hive, and id.  (It may
   accept more arguments and keyword arguments during construction
   than this, but it *must* accept these as the first two arguments!)
  - **hive:** A HiveProxy object.  This is what the actor uses to
    communicate back to the Hive itself.  (Note: this isn't the same
    thing as the hive itself... it's a proxy object.  Actors shouldn't
    be able to access all the properties and methods of their hive.
    The HiveProxy provides a universal API.)
  - **id:** The id of the actor.  The actor need not supply these
    manually, it will be provided for it by the hive (and possibly by
    whatever initializes the actor).

2. It should have a method called `handle_message`.  Accepts a single
   argument, "message", which is a :ref:`message object <message_objects>`.  
   It should examine the `directive` and other parameters (such as
   `in_reply_to`) to determine how to most appropriately handle the message.

   The default actor provides a robust `handle_message` implementation
   that handles passing messages off to various
   :ref:`message handlers <handling_messages>`, permitting message handlers
   to "suspend" themselves via coroutines while they
   :ref:`yield in wait for replies <yielding_for_replies>`, as well as
   features such as automatically
   :ref:`replying to messages <replying_to_messages>`.
   Your actor does not have to use this logic, though it's recommended
   that if you do deviate from the patterns in the basic actor's
   `handle_message`, do so with care!  There are safeguards there to make
   sure that actors waiting on replies are less likely to keep
   coroutines in waiting forever in case your actor doesn't make an
   explicit reply!

.. _handling_messages:

Handling messages
-----------------

The default behavior for actors is to pass off messages to a message
handler method like so:

.. code-block:: python

    class RascallyRabbit(Actor):
        def __init__(self, hive, id):
            super(Overseer, self).__init__(hive, id)
    
            self.message_routing.update(
                {"do_tricks": self.do_tricks})
    
        def do_tricks(self, message):
            trick_hunter(message.from_id)

In the above example, if our "RascallyRabbit" gets a message with the
directive "do_tricks", that message will be executed by the
`do_tricks` method.

But messages and handling messages is a whole big topic, so let's
examine that below.


Messages
========

A bit on messages
-----------------

Messages

.. _message_objects:

The message object
~~~~~~~~~~~~~~~~~~



.. autoclass:: xudd.message.Message




Sending messages from actor to actor
------------------------------------


Message queues and the two types of actors
------------------------------------------

Basic actors
~~~~~~~~~~~~

.. todo:: Document how each actor is "woken up" as messages come in

Dedicated actors
~~~~~~~~~~~~~~~~

.. _yielding_for_replies:

Yielding for replies
--------------------

.. _replying_to_messages:

Replying to messages
--------------------

Explicitly replying
~~~~~~~~~~~~~~~~~~~

The auto-reply mechanism
~~~~~~~~~~~~~~~~~~~~~~~~

Deferring your reply
~~~~~~~~~~~~~~~~~~~~


Hives
=====

Hive-level overview
-------------------

The hive is itself an actor!
----------------------------

If your mind just exploded, that's okay.  Take a moment to allow it to
reassemble.  Minds have a way of being able to do that.

The way this works is a bit tricky to think about, but the cool


Variants on the standard Hive
-----------------------------


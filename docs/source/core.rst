===========
Core design
===========

High level overview
===================

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
  actor, intializing new actors, or requesting shutdown of the hive
  and all actors.

These concepts are expanded on later in this document.  Additional
features/components that are planned as part of XUDD's design (some of
these are yet to be implemented):

- **Inter-hive messaging:** 
- **Dedicated actors:**
- **Actor "event" subscriptions:**
- **Property API:**
- **Actor serialization:**

Detailed design
===============


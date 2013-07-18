XUDD: A Python Actor Model System
=================================

<pre>
  FROM THE DARKNESS, OLD GODS AROSE TO
    BRING NEW ORDER TO THE WORLD.
    BEHOLD, ALL SHALL SUBMIT TO...
 
   .-   .-   -. ..  .. .---.  .---.     -.
   \ \  \ \ / // |  | \| .- \ | .- \   / /
 /\ \ \  \ ' / | |  | || | \ || | \ | / / /\
 \/ /_/  / . \ \ \__/ /| |_/ .| |_/ . \_\ \/
        \_/ \_/ '____' '.___/ '.___/
           _                __              
         /  .        ___   /  \
        / /o \    .-'   './ /o\_
       /.- \o \.-/ oooo--o\/ /  \
            \O/  \  .-----.\/ /o\\
            /' /\ \  ^^^^^   / \o\\
           / ./\o          _/   \o\\
          / /   '---______/      \_\'
          '                        '
</pre>

<pre>
"I have seen the future... and the future is XUDD!"
  -- Acolyte of the Cult of XUDD

"The greatest threat to our children since Dungeons and Dragons."
  -- Somebody's Relative

"It's an asyncronous actor model system for Python... I don't
 understand what this has to do with chaotic deities, or why it's
 called XUDD."
  -- Someone reading this document
</pre>


Join the cult of XUDD
---------------------

We're on IRC: #xudd on irc.freenode.net


The short of it
---------------

XUDD is an asynchronous actor model framework for python.  It's
designed so that you can write asynchronous code that feels easy and
synchronous, thanks to some clever use of coroutines.

XUDD has some pretty big goals.  If everything goes well, the code you
write will be easily scalable so that asynchronous code is as easily
single process as it could be multi-process, or even multi-machine.

In XUDD, you wrap your code in actors.  You can become very
fine-grained about this, or have actors take over some very large
jobs.  Actors are controlled by "hives".  In the not-too-distant
future, we hope to have inter-hive-communication (which is where the
multi-process and multi-machine stuff comes in).

XUDD is designed with plans for various uses:
 - More modern web application systems (but with drop-in integration
   with old WSGI applications), but not just HTTP: built-in tooling
   for integrating WebSockets and task handling (a-la Celery)
 - Writing multiplayer games like MUD systems or MMORPGs.  Sure, why
   not?  The actor model is perfect for this.
 - Distributed data crunching.

Of couse, a lot of this is speculative.  I'm not sure if we'll
actually acheive all that... for now this is a lot of theory. :) Right
now we're mostly just laying down the infrastructure.  Interested?  We
could use your help.


Why?
----

Twisted and Node.js are cool, but frankly, I have a hard time
following code that's broken into a billion tiny event'y functions.
Basically, eventually I feel like you're fighting the Flying Spagetti
Monster of code.  Within the cult of XUDD we hope to banish Flying
Spagetti Monster code and raise old, chaotic gods of the actor model
and have them lord over our processing.  Yesssss....

Besides, I think the actor model is pretty cool, and we don't have a
very good general purpose free software implementation out there as
far as I could tell.


Who's behind all this?
----------------------

The main author of this is Christopher Allan Webber (who's also
writing this document).  Initial collaboration on some of the core
XUDD ideas with Tamas Kemenczy.  Many other peoples' ideas taken as
inspiration.  See AUTHORS.txt.


What does XUDD stand for?
-------------------------

Originally, XUDD was designed for a game system, and this stood for
Extensible User Dungeon Design.  However, that never ended up happening.

Instead, XUDD now stands for a programming cult which hopes to revive
the eXtra Universal Destruction Deity.


What license is it under?
-------------------------

XUDD and its core code is released under the Apache License v2.

Several extensions are planned which may be under different, but
compatible licenses.


GitHub? Really??
----------------

Some people who know me (Chris Webber) know I'm against centralized
systems, so the choice of GitHub might be surprising here.

It's a problem.  In the meanwhile, I don't have time to set up another
issue tracker, testing server, etc.  I'd like to see improvements in
alternatives, and deployability of alternatives, especially one that
supports proper federation and an issue tracker.  (Maybe one could be
built with XUDD?)

That's a separate conversation though.

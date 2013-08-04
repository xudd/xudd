from __future__ import print_function

import logging
from collections import deque
from itertools import count

from xudd import PY2

from xudd.message import Message
from xudd.tools import base64_uuid4

_log = logging.getLogger(__name__)


class Hive(object):
    """
    Hive handles all actors and the passing of messages between them.

    Inter-hive communication may exist in the future, it doesn't yet ;)
    """
    def __init__(self):
        super(Hive, self).__init__()

        # Which actors this hive is managing
        self._actor_registry = {}

        # Messages to be processed
        self._message_queue = deque()

        # This is actions for ourself to take, such as checking if an
        # actor should be re-queued, and queueing messages to an actor
        self.hive_action_queue = deque()

        # Set this to True to break the current loop
        self.should_stop = False

        # Objects related to generating unique ids for messages
        self.message_uuid = base64_uuid4()
        self.message_counter = count()

    def register_actor(self, actor):
        """
        Register an actor on the hive
        """
        self._actor_registry[actor.id] = actor

    def remove_actor(self, actor_id):
        """
        Remove an actor from the hive
        """
        self._actor_registry.pop(actor_id)

    def send_message(self, to, directive,
                     from_id=None,
                     body=None, in_reply_to=None, id=None,
                     wants_reply=None):
        """
        API for sending a message to an actor.

        Note, not the same as queueing a message which is a more low-level
        action.  This also constructs a proper Message object.
        """
        message_id = id or self.gen_message_id()
        message = Message(
            to=to, directive=directive, from_id=from_id, body=body,
            in_reply_to=in_reply_to, id=message_id, wants_reply=wants_reply)

        _log.debug('send_message: {0}'.format(message))

        self._message_queue.append(message)
        return message_id

    def run(self):
        """
        Run the hive's main loop.
        """
        while not self.should_stop:
            # self._process_hive_actions()
            self._process_messages()

    def _process_messages(self):
        """
        Process however many messages are currently on the queue.
        """
        # Note: the reason we don't run through all messages till exhaustion
        #   is so that the run() loop has an opportunity to process other hive
        #   actions after we finish going through these present messages
        for i in range(len(self._message_queue)):
            message = self._message_queue.popleft()
            try:
                actor = self._actor_registry[message.to]
            except IndexError:
                # For some reason this actor wasn't found, so we may need to
                # inform the original sender
                _log.warning('recipient not found for message: {0}'.format(
                    message))

                self.return_to_sender(message)

            # Maybe not the most opportune place to attach this
            message.hive_proxy = actor.hive

            # TODO: More error handling here! ;)
            actor.handle_message(message)

    def return_to_sender(self, message, directive="error.no_such_actor"):
        """
        Message could not be delivered; return to sender
        (if they've requested a reply, that is.)
        """
        # If this message requests a reply, and the message sender
        # isn't the intended recipient, let them know.
        # (Yeah, actors sometimes message themselves.)
        if message.wants_reply and message.from_id != message.to:
            self.send_message(
                to=message.from_id, directive=directive,
                from_id="hive", in_reply_to=message.id)

    def gen_proxy(self):
        """
        Generate a HiveProxy for an actor.
        """
        return HiveProxy(self)

    def gen_actor_id(self):
        """
        Generate an actor id.
        """
        return base64_uuid4()

    def gen_message_id(self):
        """
        Generate a unique message id.

        Since uuid4s take a bit of time to compose, instead we keep a
        local counter combined with our hive's counter-uuid.
        """
        # This method should be thread safe, I think, without need for a lock:
        #   http://29a.ch/2009/2/20/atomic-get-and-increment-in-python
        if PY2:
            return u"%s:%s" % (self.message_uuid, self.message_counter.next())
        else:
            return u"%s:%s" % (self.message_uuid, self.message_counter.__next__())

    def create_actor(self, actor_class, *args, **kwargs):
        hive_proxy = self.gen_proxy()
        actor_id = kwargs.pop("id", None) or self.gen_actor_id()

        actor = actor_class(
            hive_proxy, actor_id, *args, **kwargs)
        hive_proxy.associate_with_actor(actor)
        self.register_actor(actor)

        return actor_id

    def send_shutdown(self):
        # We should have a more graceful shutdown feature that gives
        # the actors a chance to wrap up business ;)
        self.should_stop = True

### TODO: We may or may not return to this, for now we have nothing
###   that fits upon here.
###   ... note that I HATE commented out blocks of code like this.
###   However, we may be adding it back when dedicated actors reappear,
###   hence it sitting here for the next week or so.
###   THIS WILL NOT STAY COMMENTED OUT LIKE THIS
#
#      def _process_hive_actions(self):
#          for i in range(len(self.hive_action_queue)):
#              try:
#                  action = self.hive_action_queue.popleft()
#              except IndexError:
#                  # no more hive actions to process
#                  # ... this shouldn't happen though?
#                  break
#     
#              action_type = action[0]
#     
#              # The actor just had their stuff processed... see if they
#              # should be put back on the actor queue
#              if action_type == "check_queue_actor":
#                  actor = action[1]
#                  # Should we requeue?
#                  if not len(actor.message_queue) == 0 and \
#                     not actor in self._actors_in_queue:
#                      # Looks like so!
#                      self._actor_queue.append(actor)
#                      self._actors_in_queue.add(actor)
#     
#              elif action_type == "queue_message":
#                  message = action[1]
#                  self.queue_message(message)
#     
#              else:
#                  raise UnknownHiveAction(
#                      "Unknown action: %s" % action_type)
#
# class UnknownHiveAction(Exception): pass


class HiveProxy(object):
    """
    Proxy to the Hive.

    Doesn't expose the entire hive because that could result in
    actors playing with things they shouldn't. :)
    """
    def __init__(self, hive):
        self._hive = hive
        self._actor = None

    def associate_with_actor(self, actor):
        """
        Associate an actor with ourselves
        """
        self._actor = actor

    def send_message(self, to, directive,
                     from_id=None,
                     body=None, in_reply_to=None, id=None,
                     wants_reply=None):
        from_id = from_id or self._actor.id
        return self._hive.send_message(
            to=to, directive=directive, from_id=from_id, body=body,
            in_reply_to=in_reply_to, id=id,
            wants_reply=wants_reply)

    def remove_actor(self, *args, **kwargs):
        return self._hive.remove_actor(*args, **kwargs)

    def create_actor(self, actor_class, *args, **kwargs):
        return self._hive.create_actor(actor_class, *args, **kwargs)

    def send_shutdown(self, *args, **kwargs):
        return self._hive.send_shutdown(*args, **kwargs)

    def gen_message_id(self, *args, **kwargs):
        return self._hive.gen_message_id(*args, **kwargs)

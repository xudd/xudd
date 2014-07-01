from __future__ import print_function

import asyncio
import logging
from itertools import count
import signal

from xudd.message import Message
from xudd.tools import (
    base64_uuid4, is_qualified_id, join_id, split_id,
    import_component)
from xudd.actor import Actor

_log = logging.getLogger(__name__)


class Hive(Actor):
    """
    Hive handles all actors and the passing of messages between them.

    Inter-hive communication may exist in the future, it doesn't yet ;)

    Note: Even though this descends from actor it does not have the
      same invocation pattern... it supplies its own hive proxy (to
      itself!)

    TODO: This docstring sucks ;)
    """
    def __init__(self, hive_id=None, loop=None):
        # id of the hive
        self.hive_id = hive_id or self.gen_actor_id()

        hive_proxy = self.gen_proxy()
        super(Hive, self).__init__(
            id=join_id("hive", self.hive_id),
            hive=hive_proxy)
        hive_proxy.associate_with_actor(self)

        # Which actors this hive is managing
        self._actor_registry = {}

        # Note: can we just trust the user to set the right policy?
        self.loop = loop or asyncio.get_event_loop()

        # Objects related to generating unique ids for messages
        self.message_uuid = base64_uuid4()
        self.message_counter = count()

        # Ambassador registry (for inter-hive-communication)
        self._ambassadors = {}

        # Extend message routing
        self.message_routing.update(
            {"register_ambassador": self.register_ambassador,
             "unregister_ambassador": self.unregister_ambassador,
             "create_actor": self.create_actor_handler})

        # Register ourselves on... ourselves ;)
        self.register_actor(self)


    def register_actor(self, actor):
        """
        Register an actor on the hive
        """
        if actor.local_id in self._actor_registry:
            raise KeyError("Actor with that id already registered")
        elif actor.local_id == "hive" and actor != self:
            # Only the hive itself can get this id!
            raise KeyError("The actor id 'hive' is reserved")

        self._actor_registry[actor.local_id] = actor

    def remove_actor(self, actor_id):
        """
        Remove an actor from the hive
        """
        if is_qualified_id(actor_id):
            actor_id = split_id(actor_id)[0]

        self._actor_registry.pop(actor_id)

    def send_message(self, to, directive,
                     from_id=None,
                     body=None, in_reply_to=None, id=None,
                     wants_reply=None):
        """
        API for sending a message to an actor.

        This also constructs a proper Message object.
        """
        message_id = id or self.gen_message_id()
        message = Message(
            to=to,
            from_id=from_id,
            directive=directive, body=body,
            in_reply_to=in_reply_to, id=message_id, wants_reply=wants_reply)

        _log.debug("send_message: %s", message)

        self.loop.call_soon(self._process_message, message)
        return message_id

    def run(self):
        """
        Run the hive's main loop.
        """
        self.loop.add_signal_handler(signal.SIGINT, self.send_shutdown)
        self.loop.add_signal_handler(signal.SIGTERM, self.send_shutdown)
        self.loop.run_forever()


    def _process_message(self, message):
        # Route appropriately here
        actor_id, hive_id = split_id(message.to)

        ## Is the actor local?  Send it!
        if hive_id == self.hive_id:
            try:
                actor = self._actor_registry[actor_id]
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

        ## Looks like the actor must be remote, forward it!
        else:
            # Get the associated ambassador
            ## TODO: error handling if hive doesn't exist ;)
            ambassador_id = self._ambassadors[hive_id]
            ambassador = self._actor_registry[ambassador_id]

            # repackage the message for sending
            repackaged_message = self._repackage_message_for_forwarding(
                message, ambassador)

            # send it off!
            ambassador.handle_message(repackaged_message)


    def _repackage_message_for_forwarding(self, message, ambassador):
        """
        Repackage a message for forwarding

        Doesn't attach the hive_proxy... do that in the parent of this method?
        (TODO: Revisit that)
        """
        return Message(
            to=ambassador.id,
            directive="forward_message",
            from_id=self.id,
            id=self.gen_message_id(),
            body={
                "to": message.to,
                "directive": message.directive,
                "from_id": message.from_id,
                "id": message.id,
                "body": message.body,
                "in_reply_to": message.in_reply_to,
                "wants_reply": message.wants_reply})

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
        return u"%s:%s" % (self.message_uuid, self.message_counter.__next__())

    def create_actor(self, actor_class, *args, **kwargs):
        hive_proxy = self.gen_proxy()
        actor_id = join_id(
            kwargs.pop("id", None) or self.gen_actor_id(),
            self.hive_id)

        actor = actor_class(
            hive_proxy, actor_id, *args, **kwargs)
        hive_proxy.associate_with_actor(actor)
        self.register_actor(actor)

        return actor_id

    def send_shutdown(self):
        # We should have a more graceful shutdown feature that gives
        # the actors a chance to wrap up business ;)
        self.loop.stop()

    #############################
    # Common hive message routing
    #############################
    def register_ambassador(self, message):
        """
        Register this actor as being the ambassador for some specific hive id
        """
        from_actor_id, from_hive_id = split_id(message.from_id)
        # Make sure this actor is from our hive
        assert from_hive_id == self.hive_id or from_hive_id is None
        self._ambassadors[message.body["hive_id"]] = from_actor_id

    def unregister_ambassador(self, message):
        """
        Unregister this actor as being the ambassador for some specific hive id
        """
        from_actor_id, from_hive_id = split_id(message.from_id)
        assert from_hive_id == self.hive_id or from_hive_id is None
        old_ambassador_id = self._ambassadors.pop(message.body["hive_id"])
        # Make sure this actor is really the one it said it was
        # (though this only possibly could help find bugs)
        assert old_ambassador_id == from_actor_id

    # NOTE: If we eventually get to the point where we don't
    # necessarily trust outside hives, THIS MUST BE MOVED TO A MIXIN.
    def create_actor_handler(self, message):
        """
        Handling create_actor, from an actor's message.

        Useful for spawning actors remotely over inter-hive communication.
        """
        actor_class = message.body['class']
        actor_args = message.body.get('args', [])
        actor_kwargs = message.body.get('kwargs', {})

        actor_class = import_component(actor_class)
        actor_id = self.create_actor(actor_class, *actor_args, **actor_kwargs)
        message.reply({'actor_id': actor_id})


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

    @property
    def hive_id(self):
        return self._hive.hive_id


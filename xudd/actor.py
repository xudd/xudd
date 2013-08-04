from functools import wraps

from types import GeneratorType

import logging


_log = logging.getLogger(__name__)


############
# decorators
############

def autoreply(func):
    """
    Automatically reply to a message if not handled in a handle_message
    method.  Replies in the most minimal way possible.
    """
    @wraps(func)
    def wrapper(self, message):
        result = func(self, message)

        if message.needs_reply():
            message.reply()

        return result

    return wrapper


####################
# Main actor classes
####################


class Actor(object):
    """
    Basic XUDD actor.
    """
    def __init__(self, hive, id):
        self.hive = hive
        self.id = id

        # Routing of messages to handler functions
        self.message_routing = {}

        # Registry on coroutines that are currently waiting for a response
        self._waiting_coroutines = {}

    @autoreply
    def handle_message(self, message):
        """
        Handle a message being sent to this actor.
        """
        # If this message is continuing a coroutine-in-waiting, we'll
        # handle that.
        if message.in_reply_to is not None \
           and message.in_reply_to in self._waiting_coroutines:
            coroutine = self._waiting_coroutines.pop(message.in_reply_to)

            # Send this message reply to this coroutine
            try:
                message_id = coroutine.send(message)
            except StopIteration:
                # And our job is done
                return

            # since the coroutine returned a message_id that was sent,
            # we should both add this message's id to the registry
            self._waiting_coroutines[message_id] = coroutine
            return

        # Otherwise, this is a new message to handle.
        # TODO: send back a warning message if this is an unhandled directive?
        message_handler = self.message_routing[message.directive]

        result = message_handler(message)

        # If this is a coroutine, then we should handle putting its
        # results into the coroutine registry
        if isinstance(result, GeneratorType):
            coroutine = result
            try:
                message_id = result.send(None)
            except StopIteration:
                # Guess this coroutine ended without any yields
                return None

            # since the coroutine returned a message_id that was sent,
            # we should both add this message's id to the registry
            # ... yes this is the same code as above
            self._waiting_coroutines[message_id] = coroutine
            return

    def send_message(self, *args, **kwargs):
        return self.hive.send_message(*args, **kwargs)

    def wait_on_message(self, to, directive, from_id=None,
                        id=None, body=None, in_reply_to=None):
        """
        Send a message that we'll wait for a reply to.
        """
        return self.hive.send_message(
            to, directive,
            from_id=from_id,
            body=body, in_reply_to=in_reply_to, id=id,
            wants_reply=True)

    def wait_on_self(self):
        """
        Send a message that's actually just going to reply to itself!
        Useful for while loops.
        """
        # Kinda evil.  This message is going to reply to itself, so
        # it's actually generating its own id ahead of time...
        this_message_id = self.hive.gen_message_id()

        return self.hive.send_message(
            to=self.id, directive="self_reply",
            from_id=self.id,
            id=this_message_id, in_reply_to=this_message_id,
            # Okay, I know this is surprising...
            #
            # But since this message actually replies to itself, we
            # don't want to trigger the auto-reply behavior!
            # it is, by definition, already replying!
            wants_reply=False)


class ActorProxy(object):
    def __init__(self, actor_id):
        self.id = actor_id


##########################################################
# Useful decorators (possibly in defining your own actors)
##########################################################

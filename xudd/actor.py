from types import GeneratorType

class Actor(object):
    """
    Basic XUDD actor.
    """
    def __init__(self, hive, id):
        self.hive = hive
        self.id = id

        # Actors SHOULD NOT TOUCH their own message queue, generally.
        # Let a worker thread do it.
        # There may be exceptions, but those will be outlined later ;)
        self.message_queue = hive.gen_message_queue()

        # Routing of messages to handler functions
        self.message_routing = {}

        # Registry on coroutines that are currently waiting for a response
        self._waiting_coroutines = {}


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
            message_id = result.send(None)

            # since the coroutine returned a message_id that was sent,
            # we should both add this message's id to the registry
            # ... yes this is the same code as above
            self._waiting_coroutines[message_id] = coroutine
            return

    def wait_on_message(self, to, directive, from_id=None,
                        id=None, body=None, in_reply_to=None):
        return self.hive.send_message(
            to, directive,
            from_id=from_id,
            body=body, in_reply_to=in_reply_to, id=id,
            wants_reply=True)


class ActorProxy(object):
    def __init__(self, actor_id):
        self.id = actor_id

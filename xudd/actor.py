from types import GeneratorType

class Actor(object):
    """
    Basic XUDD actor.
    """
    def __init__(self, hive):
        self.hive = hive

        self.message_routing = {}

        # Registry on coroutines that are currently waiting for a response
        self._waiting_coroutines = {}

    def handle_message(self, message):
        # If this message is continuing a coroutine-in-waiting, we'll
        # handle that.
        if message.reply_to is not None \
           and message.reply_to in self._waiting_coroutines:
            coroutine = self._waiting_coroutines.pop(message.reply_to)

            # Send this message reply to this coroutine
            try:
                message_to_send = coroutine.send(message)
            except StopIteration:
                # And our job is done
                return

            # since the coroutine returned a message to be yielded, we
            # should both add this message's id to the registry
            message_id = self.hive.send_message(message_to_send)
            self._waiting_coroutines[message_id] = coroutine
            return

        # Otherwise, this is a new message to handle.
        # TODO: send back a warning message if this is an unhandled directive?
        message_handler = self.message_routing[message["directive"]]

        result = message_handler(message)
        if isinstance(result, GeneratorType):
            coroutine = result
            message_to_send = result.send(None)

            # since the coroutine returned a message to be yielded, we
            # should both add this message's id to the registry
            # ... yes this is the same code as above
            message_id = self.hive.send_message(message_to_send)
            self._waiting_coroutines[message_id] = coroutine
            return
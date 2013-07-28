import json

class Message(object):
    def __init__(self, to, directive, from_id, id, body=None, in_reply_to=None,
                 wants_reply=False, hive_proxy=None):
        self.to = to
        self.directive = directive
        self.from_id = from_id
        self.body = body or {}
        self.id = id
        self.in_reply_to = in_reply_to
        self.wants_reply = wants_reply

        self.replied = False
        self.deferred_reply = False
        self.hive_proxy = hive_proxy

    def __repr__(self):
        return u"<{cls} #{id} {inreply}to={to} from={from_id}>".format(
            cls=self.__class__.__name__,
            inreply='in-reply-to={in_reply_to} '.format(
                in_reply_to=self.in_reply_to) if self.in_reply_to else '',
            to=self.to,
            from_id=self.from_id,
            id=self.id)

    ###############
    # Reply methods
    ###############

    def reply(self, body=None, directive=u"reply", wants_reply=False):
        """
        Send a reply to this message.

        This also marks the flag that we were replied to properly.
        """
        # I guess we should make hive_proxy mandatory?? or something?
        # definitely mandatory to use this
        assert self.hive_proxy is not None

        self.hive_proxy.send_message(
            to=self.from_id,
            directive=directive,
            wants_reply=wants_reply,
            in_reply_to=self.id,
            body=body)
            
        # Yup, we were replied to
        self.replied = True

    def defer_reply(self):
        """
        Mark that this message isn't replied to now, but will be
        replied to later
        """
        self.deferred_reply = True

    def needs_reply(self):
        """
        See if we still need a reply.

        Returns True or False based on the value of
          self.needs_reply, self.deferred_reply, and self.replied
        """
        return self.wants_reply and not (self.deferred_reply or self.replied)

    #######################################
    # Serializing and deserializing methods
    #######################################

    def to_dict(self):
        message = {
            "to": self.to,
            "directive": self.directive,
            "from_id": self.from_id,
            "id": self.id,
            "body": self.body,
            "wants_reply": self.wants_reply}
        if self.in_reply_to:
            message["in_reply_to"] = self.in_reply_to

        return message

    @classmethod
    def from_dict(cls, dict_message):
        return cls(**dict_message)

    def serialize(self):
        return serialize_message_msgpack(self)

    @classmethod
    def from_serialized(self, serialized_message):
        """
        Returns a new Message instance based on a serialized message
        """
        return serialize_message_msgpack(serialized_message)


#########################################
# Serializing and deserializing functions
#########################################


try:
    # not sure if this belongs here either
    import msgpack

    MSGPACK_ENABLED = True
    def serialize_message_msgpack(message):
        return msgpack.packb(message.to_dict())

    def deserialize_message_msgpack(msgpack_message):
        # TODO: recursively decode to unicode
        return Message.from_dict(msgpack.unpackb(msgpack_message))

except ImportError:
    def serialize_message_msgpack(message):
        raise ImportError("msgpack not installed it seems")


def serialize_message_json(message):
    # TODO
    pass


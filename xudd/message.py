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

    def __repr__(self):
        return u"<{cls} #{id} {inreply}to={to} from={from_id}>".format(
            cls=self.__class__.__name__,
            inreply='in-reply-to={in_reply_to} '.format(
                in_reply_to=self.in_reply_to) if self.in_reply_to else '',
            to=self.to,
            from_id=self.from_id,
            id=self.id)

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

    def reply(self, directive, body=None, wants_reply=None):
        self.replied = True
        return Message

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


###############################
# Serializing and deserializing
###############################


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


import json

class Message(object):
    def __init__(self, to, directive, from_id, id, body=None, in_reply_to=None,
                 wants_reply=False):
        self.to = to
        self.directive = directive
        self.from_id = from_id
        self.body = body or {}
        self.id = id
        self.in_reply_to = in_reply_to
        self.wants_reply = wants_reply

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


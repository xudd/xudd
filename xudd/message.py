import json

class Message(object):
    def __init__(self, to, from_id, body, id, reply_to=None):
        self.to = to
        self.from_id = from_id
        self.body = body
        self.id = id
        self.reply_to = reply_to

    def to_dict(self):
        message = {
            "to": self.to,
            "from": self.from_id,
            "id": self.id,
            "body": self.body}
        if self.reply_to:
            message["reply_to"] = self.reply_to

        return message

    @classmethod
    def from_dict(cls, dict_message):
        return cls(**dict_message)



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



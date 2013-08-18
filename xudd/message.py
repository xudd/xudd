import json

class Message(object):
    """Encapsulation of message data.

    This is what's actually passed to an actor's `handle_message`
    method.  While messages can actually be serialized into json or
    msgpack data, (and methods for that are provided,) this is the
    standard representation for passing around messages in XUDD
    itself.

    Usually, however, actors themselves do not construct Message
    objects: these are instead constructed by the Hive itself.  Actors
    send off messages using their HiveProxy.send_message() method.

    **Args:**

    - **to:** the id of the receiving actor

    - **directive:** what kind of action or request we're making of
      the receiving actor.  Usually this is some kind of useful
      instruction or request.  For example, we might be communicating
      with a Dragon actor, and we might give it the directive
      "breathe_fire", which a dragon actor knows how to handle.
      However, if we're just replying to messages, frequently this
      directive is simply "reply".

      In the future, there will also be a standardized set of common
      "error" directives :)
    - **from_id:** the id of the actor sending this message
    - **id:** the id of this message itself.  Usually constructed by the
      Hive itself (but available to the actor sending the message also,
      often used to track "waiting on replies" for coroutines-in-waiting)
    - **body:** a dictionary of data; the payload of the message.
      (if None, will be converted to an empty dict.)
      This can be anything, with a couple of caveats:

      - If there's any possibility of sending this across the wire via
        inter-hive communication, the contents of "body" ABSOLUTELY
        MUST be json encodeable.
      - If the message is just being sent for local actor to local
        actor, it's acceptable to pass along whatever, but keep in
        mind that you are effectively breaking any possibility of inter-hive
        communication between these actors!
      - If you are sending along ANY mutable structures, your actor
        must NEVER ACCESS THOSE OBJECTS AGAIN.  Not for reading, not
        for writing.  If you do otherwise, consider yourself breaking
        the rules, and you are on THIN ICE.  This includes basic
        structures, such as lists.  If you have any doubt, consider
        using copy.deepcopy() on objects you're passing into here.
      - "sanitize" options (with some performance pentalties) may be
        added in the future that will force-transform into json or
        msgpack and back, but those don't exist yet.

    - **in_reply_to:** The message id of a previous message that we're
      responding to.  This may be used by the actor we're sending this to
      for waking back up coroutines that are awaiting this response.
    - **wants_reply:** Informs the actor receiving this that we want
      some kind of response.  In general, actors will respect this; if
      a message requests a response, an actor absolutely should
      provide one, one way or another.  The plus side is that we have
      some tooling built in to make this easy.
      See :ref:`replying-to-messages` for details.
    - **hive_proxy:** In order for the auto-replying tools to work, a
      hive_proxy must be constructed, which generally is the same
      hive_proxy the receiving actor has.  When constructing a Message
      object, you don't necessarily have to pass this in when
      initializing the object, but you should attach this to the
      message.hive_proxy object before passing to the message queue of
      the actor.

    """
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
        return u"<{cls} #{id} {directive} {inreply}to={to} from={from_id}>".format(
            cls=self.__class__.__name__,
            directive=self.directive,
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


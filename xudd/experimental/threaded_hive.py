from __future__ import print_function

import uuid
from threading import Thread, Lock
from itertools import count

from xudd.hive import HiveProxy

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

from xudd.message import Message


class ActorMessageQueue(object):
    """
    The "message_queue" object (technically a queue and a lock)
    that actors get with this hive pattern.
    """
    def __init__(self):
        self.queue = Queue()
        self.lock = Lock()


class HiveWorker(Thread):
    """
    A worker thread that gives life to actors, allowing them to process
    messages.
    """
    def __init__(self, hive, actor_queue, max_messages=5):
        """
        Args:
         - actor_queue: queue of actors to be processed at present
         - max_messages: maximum number of messages to process per actor
        """
        Thread.__init__(self)
        self.hive = hive
        self.actor_queue = actor_queue
        self.max_messages = max_messages

        self.should_stop = False

    def run(self):
        while not self.should_stop:
            self.process_actor()

    def stop(self):
        self.should_stop = True

    def process_actor(self):
        """
        Take an actor off the queue and process its messages... if
        there's anything to process
        """
        # Get an actor from the actor queue
        #
        try:
            actor = self.actor_queue.get(block=True, timeout=1)
        except Empty:
            # We didn't do anything this round, oh well
            return False

        # Process messages from this actor
        messages_processed = 0
        while self.max_messages is None \
              or messages_processed < self.max_messages:
            # Get a message off the message queue
            # (I don't think we need to lock while pulling one off the stack,
            #  but doesn't hurt?)
            with actor.message_queue.lock:
                try:
                    message = actor.message_queue.queue.get(block=False)
                except Empty:
                    # No messages on the queue anyway, might as well break out
                    # from this
                    break

            actor.handle_message(message)
            messages_processed += 1

        # Request checking if actor should be requeued with hive
        self.hive.request_possibly_requeue_actor(actor)


class Hive(Thread):
    """
    Hive handles all actors and the passing of messages between them.

    Inter-hive communication may exist in the future, it doesn't yet ;)
    """
    def __init__(self, num_workers=5):
        super(Hive, self).__init__()

        # NO locking on this presently, though maybe we should?
        # At the very least, one *should not* iterate through this dictionary
        # ... wouldn't be hard to set up a lock if we need it
        self._actor_registry = {}

        # Actor queue
        self._actor_queue = Queue()

        self.num_workers = num_workers
        self._workers = []

        # This is actions for ourself to take, such as checking if an
        # actor should be re-queued, and queueing messages to an actor
        self.hive_action_queue = Queue()

        self.should_stop = False

        # Objects related to generating unique ids for messages
        self.message_uuid = str(uuid.uuid4())

        self.message_counter = count()

    def _init_and_start_workers(self):
        for i in range(self.num_workers):
            worker = HiveWorker(self, self._actor_queue)
            self._workers.append(worker)
            worker.start()

    def register_actor(self, actor):
        self._actor_registry[actor.id] = actor

    def remove_actor(self, actor_id):
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
        self.hive_action_queue.put(
            ("queue_message", message))
        return message_id

    def request_possibly_requeue_actor(self, actor):
        self.hive_action_queue.put(
            ("check_queue_actor", actor))

    def queue_message(self, message):
        """
        Queue a message to its appropriate actor.
        """
        try:
            actor = self._actor_registry[message.to]
        except KeyError:
            # TODO:
            #   In the future, if this fails, we should send a message back to
            #   the original sender informing them of such
            print(
                "Wouldn't it be nice if we handled sending "
                "messages to an actor that didn't exist more gracefully?")
            return False

        # --- lock during this to avoid race condition of actor ---
        #     with messages not appearing on actor_queue
        with actor.message_queue.lock:
            actor.message_queue.queue.put(message)

        self.request_possibly_requeue_actor(actor)

    def run(self):
        try:
            self._init_and_start_workers()
            self.workloop()
        except:
            raise
        finally:
            self.stop_workers()

    def queue_actor(self, actor):
        """
        Queue an actor... it's got messages to be processed!
        """
        self._actor_queue.put(actor)

    def gen_message_queue(self):
        return ActorMessageQueue()

    def gen_proxy(self):
        return HiveProxy(self)

    def workloop(self):
        # ... should we convert the hive to an actor that processes
        # its own messages? ;)

        # Process actions
        while not self.should_stop:
            try:
                # see the comment in HiveWorker's process_actor to see
                # why this is
                action = self.hive_action_queue.get(block=True, timeout=1)
            except Empty:
                continue

            action_type = action[0]

            # The actor just had their stuff processed... see if they
            # should be put back on the actor queue
            if action_type == "check_queue_actor":
                actor = action[1]
                with actor.message_queue.lock:
                    # Should we requeue?
                    if not actor.message_queue.queue.empty():
                        # Looks like so!
                        self.queue_actor(actor)

            elif action_type == "queue_message":
                message = action[1]
                self.queue_message(message)

            else:
                raise UnknownHiveAction(
                    "Unknown action: %s" % action_type)

    def stop_workers(self):
        for worker in self._workers:
            worker.should_stop = True

    def gen_actor_id(self):
        """
        Generate an actor id.
        """
        return str(uuid.uuid4())

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


class UnknownHiveAction(Exception): pass



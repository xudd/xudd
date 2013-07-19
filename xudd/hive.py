from threading import Thread, Lock

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty


class ActorWrapper(object):
    """
    Wrapper object for an actor as well as the messages it currently needs to
    process.
    """
    def __init__(self, actor):
        self.actor = actor
        self.message_queue = Queue()
        self.message_lock = Lock()


class ActorQueue(object):
    """
    Wrapper object handling the queue of actors that currently have messages to
    be processed.
    """
    def __init__(self):
        self.queue = Queue()
        self.actors_in_queue = set()
        self.actors_in_queue_lock = Lock()


class HiveWorker(Thread):
    """
    A worker thread that gives life to actors, allowing them to process
    messages.
    """
    def __init__(self, actor_queue, max_messages=5, wait_timeout=1):
        """
        Args:
         - actor_queue: queue of actors to be processed at present
         - max_messages: maximum number of messages to process per actor
         - wait_timeout: amount of time to block without getting a
           message before we give up (this way we can still stop if
           useful)
        """
        super(HiveWorker, self).__init__(self)
        self.should_stop = False
        self.actor_queue = actor_queue
        self.wait_timeout = wait_timeout
        self.max_messages = max_messages

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
            wrapped_actor = self.actor_queue.queue.get(
                block=True, timeout=self.wait_timeout)
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
            with wrapped_actor.message_lock:
                try:
                    message = wrapped_actor.message_queue.get(block=False)
                except Empty:
                    # No messages on the queue anyway, might as well break out
                    # from this
                    break

            wrapped_actor.actor.handle_message(message)
            messages_processed += 1

        # Put the actor back on the queue, if appropriate
        # --- lock during this to avoid race condition of actor ---
        #     with messages not appearing on actor_queue
        #
        #     Lock both:
        #      - the actor's message queue
        #      - the actors_in_queue lock
        with wrapped_actor.message_lock, self.actor_queue.actors_in_queue_lock:
            if not wrapped_actor.message_queue.empty():
                self.actor_queue.queue.put(wrapped_actor)
            else:
                self.actor_queue.actors_in_queue.pop(wrapped_actor)


class Hive(object):
    """
    Hive handles all actors and the passing of messages between them.

    Inter-hive communication may exist in the future, it doesn't yet ;)
    """
    def __init__(self, num_workers=5):
        # NO locking on this presently, though maybe we should?
        # At the very least, one *should not* iterate through this dictionary
        # ... wouldn't be hard to set up a lock if we need it
        self.__actor_registry = {}

        # Actor queue
        self.__actor_queue = ActorQueue()

        self.__workers = []
        self.__init_workers()

    def __init_workers(self):
        for i in range(num_workers):
            pass

    def start_workers(self):
        for worker in self.__workers:
            worker.run()

    def register_actor(self, actor):
        pass

    def remove_actor(self, actor_id):
        pass

    def send_message(self, message_things_here):
        """
        API for sending a message to an actor.

        Note, not the same as queueing a message which is a more low-level
        action.  This also constructs a proper Message object.
        """
        pass

    def queue_message(self, message):
        """
        Queue a message to its appropriate actor.
        """
        try:
            wrapped_actor = self.__actor_registry[message.to]
        except KeyError:
            # TODO:
            #   In the future, if this fails, we should send a message back to
            #   the original sender informing them of such
            print (
                "Wouldn't it be nice if we handled sending "
                "messages to an actor that didn't exist more gracefully?")
            return False
        
        # --- lock during this to avoid race condition of actor ---
        #     with messages not appearing on actor_queue
        #
        #     Lock both:
        #      - the actor's message queue
        #      - the actors_in_queue lock
        with wrapped_actor.message_lock, self.actor_queue.actors_in_queue_lock:
            wrapped_actor.message_queue.put(message)
            # Add the wrapped actor, if it's not in that set already
            self.actors_in_queue.add(wrapped_actor)

    def workloop(self):
        pass


class HiveProxy(object):
    def __init__(self, actor, hive):
        self.__actor = actor
        self.__hive = hive

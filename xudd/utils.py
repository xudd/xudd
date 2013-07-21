from __future__ import print_function

from threading import Lock

from collections import deque

try:
    from queue import Empty
except ImportError:
    from Queue import Empty


class UniqueQueue(object):
    """
    A queue with only unique actors; used for inserting actors.
    """
    def __init__(self):
        self._queue = deque()
        self._actors_in_queue = set()
        self._queue_lock = Lock()

    def put(self, actor):
        """
        Put an item on the queue, if it isn't already there.

        If it's already there, no big deal.
        """
        with self._queue_lock:
            if not actor in self._actors_in_queue:
                self._queue.append(actor)
                self._actors_in_queue.add(actor)

    def get(self):
        """
        Get an item off the queue.

        Raises Empty if there's no more actors left of the queue.
        """
        try:
            with self._queue_lock:
                actor = self._queue.popleft()
                actor.message_queue.forbid_requeue.set()
                self._actors_in_queue.remove(actor)
                return actor
        except IndexError:
            raise Empty("No actors left in queue")

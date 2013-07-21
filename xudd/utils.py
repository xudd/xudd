from __future__ import print_function

from threading import Lock

from collections import deque

try:
    from queue import Empty
except ImportError:
    from Queue import Empty


class UniqueQueue(object):
    """
    A queue with only unique items; used for inserting actors.
    """
    def __init__(self):
        self._queue = deque()
        self._items_in_queue = set()
        self._queue_lock = Lock()

    def put(self, item):
        """
        Put an item on the queue, if it isn't already there.

        If it's already there, no big deal.
        """
        with self._queue_lock:
            if not item in self._items_in_queue:
                self._queue.append(item)
                self._items_in_queue.add(item)

    def get(self):
        """
        Get an item off the queue.

        Raises Empty if there's no more items left of the queue.
        """
        try:
            with self._queue_lock:
                item = self._queue.popleft()
                self._items_in_queue.remove(item)
                return item
        except IndexError:
            raise Empty("No items left in queue")

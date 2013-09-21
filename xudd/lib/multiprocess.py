from multiprocessing import Process, Queue

from xudd.hive import Hive
from xudd.actor import Actor
from xudd.tools import base64_uuid4


def spawn_multiprocess_hive(hive_id):
    pass


class MultiProcessAmbassador(Actor):
    def __init__(self, hive, id):
        super(MultiProcessAmbassador, self).__init__(hive, id)

    def setup(self):
        # Spawn the remote hive
        self.remote_hive_id = base64_uuid4()
        self.to_hive_queue = Queue()
        self.from_hive_queue = Queue()
        self.remote_hive = spawn_multiprocess_hive(
            self.remote_hive_id,
            self.to_hive_queue,
            self.from_hive_queue)

        # Declare ourselves the ambassador for this hive
        self.send_message(
            to="hive",
            directive="register_ambassador",
            body={
                "hive_id": self.remote_hive_id})

class MultiProcessHive(Hive):
    def __init__(self, hive_id, receive_queue, send_queue):
        super(MultiProcessHive, self).__init__(
            hive_id=hive_id)
        self.receive_queue = receive_queue
        self.send_queue = send_queue

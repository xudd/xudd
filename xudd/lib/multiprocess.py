from multiprocessing import Process, Queue

from xudd.hive import Hive
from xudd.actor import Actor
from xudd.tools import base64_uuid4


def spawn_multiprocess_hive(hive_id, to_hive_queue, from_hive_queue):
    hive = MultiProcessHive(hive_id, to_hive_queue, from_hive_queue)
    hive.run()


class MultiProcessAmbassador(Actor):
    def __init__(self, hive, id):
        super(MultiProcessAmbassador, self).__init__(hive, id)
        self.message_routing.update(
            {"get_remote_hive_id": self.get_remote_hive_id,
             "setup": self.setup})

    def setup(self, message):
        # Spawn the remote hive
        self.remote_hive_id = base64_uuid4()
        self.to_hive_queue = Queue()
        self.from_hive_queue = Queue()
        self.multiproces_hive_proc = Process(
            target=spawn_multiprocess_hive,
            args=(
                self.remote_hive_id,
                self.to_hive_queue,
                self.from_hive_queue))
        self.multiproces_hive_proc.start()

        # Declare ourselves the ambassador for this hive
        self.send_message(
            to="hive",
            directive="register_ambassador",
            body={
                "hive_id": self.remote_hive_id})

    def get_remote_hive_id(self, message):
        message.reply({"hive_id": self.remote_hive_id})


class MultiProcessHive(Hive):
    def __init__(self, hive_id, receive_queue, send_queue):
        super(MultiProcessHive, self).__init__(
            hive_id=hive_id)
        self.receive_queue = receive_queue
        self.send_queue = send_queue

    def _flush_receive_queue(self):
        queue_len = self.receive_queue.qsize()
        for i in range(queue_len):
            # do we need exception handling here?
            item = self.receive_queue.get()
            pass

    def run(self):
        while not self.should_stop:
            self._flush_receive_queue()
            self._process_messages()

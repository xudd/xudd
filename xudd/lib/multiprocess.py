from multiprocessing import Process, Queue

from xudd.hive import Hive
from xudd.actor import Actor
from xudd.tools import base64_uuid4, join_id

import json


def spawn_multiprocess_hive(hive_id, to_hive_queue, from_hive_queue):
    hive = MultiProcessHive(hive_id, to_hive_queue, from_hive_queue)
    hive.run()


## We should be doing these via multiple inheritance, but in the meanwhile...
# class ForwarderActor(Actor):
    

def forward_message_method(self, message):
    """
    Forward message to the subprocess
    """
    self.send_queue.put(json.dumps(message.body))


def _flush_receive_queue(self):
    queue_len = self.receive_queue.qsize()
    for i in range(queue_len):
        # do we need exception handling here?
        encoded_message = self.receive_queue.get()
        message_dict = json.loads(encoded_message)
        # TODO: less hokey version of this sending a message stuff
        self.send_message(**message_dict)


class MultiProcessAmbassador(Actor):
    forward_message = forward_message_method
    _flush_receive_queue = _flush_receive_queue

    def __init__(self, hive, id):
        super(MultiProcessAmbassador, self).__init__(hive, id)
        self.message_routing.update(
            {"get_remote_hive_id": self.get_remote_hive_id,
             "setup": self.setup,
             "forward_message": self.forward_message,
             "check_message_loop": self.check_message_loop})

    def setup(self, message):
        # Spawn the remote hive
        self.remote_hive_id = base64_uuid4()
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.multiproces_hive_proc = Process(
            target=spawn_multiprocess_hive,
            args=(
                self.remote_hive_id,
                # The opposite of our send and receive queue!
                self.send_queue,
                self.receive_queue))
        self.multiproces_hive_proc.start()

        # Declare ourselves the ambassador for this hive
        self.send_message(
            to="hive",
            directive="register_ambassador",
            body={
                "hive_id": self.remote_hive_id})

        # Set up the message-checking loop
        self.send_message(
            to=self.id,
            directive="check_message_loop")

        # Tell the child hive to connect back to us
        yield self.wait_on_message(
            to=join_id("hive", self.remote_hive_id),
            directive="connect_back",
            body={"parent_hive_id": self.hive.hive_id})

    def get_remote_hive_id(self, message):
        message.reply({"hive_id": self.remote_hive_id})

    def check_message_loop(self, message):
        """
        Begin looping to check to see if there are messages to send
        back
        """
        self._flush_receive_queue()
        self.send_message(
            to=self.id,
            directive="check_message_loop")


class MultiProcessHive(Hive):
    forward_message = forward_message_method
    _flush_receive_queue = _flush_receive_queue

    def __init__(self, hive_id, receive_queue, send_queue):
        super(MultiProcessHive, self).__init__(
            hive_id=hive_id)
        self.receive_queue = receive_queue
        self.send_queue = send_queue

        self.message_routing.update(
            {"connect_back": self.connect_back,
             "forward_message": self.forward_message,
             "remote_shutdown": self.remote_shutdown,
             "remote_shutdown_step2": self.remote_shutdown_step2})

    def run(self):
        while not self.should_stop:
            self._flush_receive_queue()
            self._process_messages()

    def connect_back(self, message):
        """
        Set up our ambassadorial connection to the parent process
        """
        self.hive.send_message(
            to=self.id,
            directive="register_ambassador",
            body={
                "hive_id": message.body["parent_hive_id"]})

    ### Waiiiit, why have a 2-step shutdown process?
    # The reason is that the parent process needs to receive the
    # "confirmation" that we shut down.  So we need to autoreply and
    # send such a message.  But if we stop our loop, we won't send
    # that message.
    #
    # So we allow the autoreply, then kick off another step to
    # actually shut down our loop.  A goofy hack, but it works!
    # ... I know that doesn't make much sense; trust me ;)
    def remote_shutdown(self, message):
        self.hive.send_message(
            to=self.id,
            directive="remote_shutdown_step2")

    def remote_shutdown_step2(self, message):
        self.should_stop = True

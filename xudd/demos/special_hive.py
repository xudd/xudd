"""
This demo proves that hives are themselves now actors... and even subclassable!
"""

from __future__ import print_function

from xudd.hive import Hive
from xudd.actor import Actor
from xudd.tools import join_id


class SpecialHive(Hive):
    """
    A hive with an extra message handler on it!
    """
    def __init__(self, *args, **kwargs):
        super(SpecialHive, self).__init__(*args, **kwargs)

        self.message_routing.update(
            {"be_fanboyed": self.be_fanboyed})

    def be_fanboyed(self, message):
        """
        This actor responds confidently, asserting that it too
        is just an actor, but is the hive indeed.
        """
        message.reply(
            body={
                "is_hive": True,
                "vocal_tone": "confident",
                "words_of_wisdom": "You know I too am just an actor of sorts"})


class FanBoy(Actor):
    """
    This fanboy is obsessed with the fact that it has a hive!

    All it wants in its brief lifetime before it shuts down is to
    hear back from the hive.  Some words of wisdom would be a bonus!
    """
    def __init__(self, hive, id):
        super(FanBoy, self).__init__(hive, id)
        self.message_routing.update(
            {"nerd_out_to_hive": self.nerd_out_to_hive})

    def nerd_out_to_hive(self, message):
        response = yield self.wait_on_message(
            to=join_id("hive", self.hive.hive_id),
            directive="be_fanboyed")

        assert response.body['is_hive'] == True
        assert response.body['vocal_tone'] == 'confident'
        print("Omg!  The hive wrote back to me!  They're SO CONFIDENT... <3")
        print("And look!  They included a message:")
        print('  "%s"' % response.body["words_of_wisdom"])
        self.hive.send_shutdown()


def main():
    hive = SpecialHive()
    fanboy = hive.create_actor(FanBoy)
    hive.send_message(
        to=fanboy,
        directive="nerd_out_to_hive")

    hive.run()


if __name__ == "__main__":
    main()

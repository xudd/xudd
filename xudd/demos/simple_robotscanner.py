"""Robot Scanner XUDD test demo... simplified.

This is like xudd/demos/robotscanner.py but simplified considerably...
there's only one room, and any print statements happen inline rather
than being passed to the overseer.

If you want to see a much more complex demo, see robotscanner.py.
Also see the docstring of that; this is pretty much the same idea, but
with one room. ;)
"""


from __future__ import print_function
import random

from xudd.hive import Hive
from xudd.actor import Actor


def droid_list(num_clean, num_infected):
    """
    Create a list of (shuffled) clean droids and infected droids
    """
    droids = [False] * num_clean + [True] * num_infected
    random.shuffle(droids)
    return droids
    

class Overseer(Actor):
    """
    Actor that initializes the world of this demo and starts the mission.
    """
    def __init__(self, hive, id):
        super(Overseer, self).__init__(hive, id)

        self.message_routing.update(
            {"init_world": self.init_world})

    def init_world(self, message):
        """
        Initialize the world we're operating in for this demo.
        """
        # Create room and droids
        room = self.hive.create_actor(WarehouseRoom)
        
        for is_droid_clean in droid_list(5, 8):
            droid = self.hive.create_actor(
                Droid, infected=is_droid_clean, room=room)
            yield self.wait_on_message(
                to=droid,
                directive="register_with_room")

        # Add security robot
        security_robot = self.hive.create_actor(SecurityRobot)

        # Tell the security robot to begin their mission
        self.hive.send_message(
            to=security_robot,
            directive="begin_mission",
            body={"room": room})


class WarehouseRoom(Actor):
    """
    A room full of robots.
    """
    def __init__(self, hive, id):
        super(WarehouseRoom, self).__init__(hive, id)
        self.droids = []

        self.message_routing.update(
            {"register_droid": self.register_droid,
             "list_droids": self.list_droids})

    def register_droid(self, message):
        self.droids.append(message.body['droid_id'])

    def list_droids(self, message):
        message.reply(
            {"droid_ids": self.droids})


class Droid(Actor):
    """
    A droid that may or may not be infected!

    What will happen?  Stay tuned!
    """
    def __init__(self, hive, id, room, infected=False):
        super(Droid, self).__init__(hive, id)
        self.infected = infected
        self.hp = 50
        self.room = room

        self.message_routing.update(
            {"infection_expose": self.infection_expose,
             "get_shot": self.get_shot,
             "register_with_room": self.register_with_room})

    def register_with_room(self, message):
        yield self.wait_on_message(
            to=self.room,
            directive="register_droid",
            body={"droid_id": self.id})

    def infection_expose(self, message):
        message.reply(
            {"is_infected": self.infected})

    def get_shot(self, message):
        damage = random.randrange(0, 60)
        self.hp -= damage
        alive = self.hp > 0

        message.reply(
            body={
                "hp_left": self.hp,
                "damage_taken": damage,
                "alive": alive})

        if not alive:
            self.hive.remove_actor(self.id)


ALIVE_FORMAT = "Droid %s shot; taken %s damage. Still alive... %s hp left."
DEAD_FORMAT = "Droid %s shot; taken %s damage. Terminated."


class SecurityRobot(Actor):
    """
    Security robot... designed to seek out and destroy infected droids.
    """
    def __init__(self, hive, id):
        super(SecurityRobot, self).__init__(hive, id)

        # The room we're currently in
        self.room = None

        self.message_routing.update(
            {"begin_mission": self.begin_mission})

    def __droid_status_format(self, shot_response):
        if shot_response.body["alive"]:
            return ALIVE_FORMAT % (
                shot_response.from_id,
                shot_response.body["damage_taken"],
                shot_response.body["hp_left"])
        else:
            return DEAD_FORMAT % (
                shot_response.from_id,
                shot_response.body["damage_taken"])

    def begin_mission(self, message):
        self.room = message.body['room']

        print("Entering room %s..." % self.room)

        # Find all the droids in this room and exterminate the
        # infected ones.
        response = yield self.wait_on_message(
            to=self.room,
            directive="list_droids")
        for droid_id in response.body["droid_ids"]:
            response = yield self.wait_on_message(
                to=droid_id,
                directive="infection_expose")

            # If the droid is clean, let the overseer know and move on.
            if not response.body["is_infected"]:
                print("%s is clean... moving on." % droid_id)
                continue

            # Let the overseer know we found an infected droid
            # and are engaging
            print("%s found to be infected... taking out" % droid_id)

            # Keep firing till it's dead.
            infected_droid_alive = True
            while infected_droid_alive:
                response = yield self.wait_on_message(
                    to=droid_id,
                    directive="get_shot")

                # Relay the droid status
                print(self.__droid_status_format(response))

                infected_droid_alive = response.body["alive"]

        # Good job everyone! Shut down the operation.
        print("Mission accomplished.")
        self.hive.send_shutdown()


def main():
    # Create the hive
    hive = Hive()

    # Add overseer, who populates the world and runs the simulation
    overseer_id = hive.create_actor(Overseer, id="overseer")
    hive.send_message(
        to=overseer_id,
        directive="init_world")

    # Actually initialize the world
    hive.run()


if __name__ == "__main__":
    main()

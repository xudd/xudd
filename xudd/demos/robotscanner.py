"""Robot Scanner XUDD test demo.

Here's the premise.  There's a warehouse full of droids, some
infected, and some not.  The SecurityRobot is being sent in to clean
up the mess.  It's capable of sending a message that infected droids
are susceptible to responding in a predictable way.  Once it has
identified that a droid is infected, it shoots it full of holes till
the droid is terminated.  The SecurityRobot goes from room to room
till things are cleared out.

Overseeing the operation is the "overseer".  The security robot keeps
the overseer up to date on its progress as it goes.  (For this demo,
the overseer is also responsible for initializing the world and
reporting info back to the user.)
"""


from __future__ import print_function
import random
import logging

from xudd.hive import Hive
from xudd.actor import Actor
from xudd.tools import join_id

_log = logging.getLogger(__name__)

# List of room tuples of (clean_droids, infected_droids)

ROOM_STRUCTURE = [
    (3, 1),
    (0, 2),
    (8, 5),
    (5, 0),
    (2, 1)]


class Overseer(Actor):
    """
    Actor that initializes the world of this demo, starts the mission,
    and sends information about what's going on back to the user.
    """
    def __init__(self, hive, id):
        super(Overseer, self).__init__(hive, id)

        self.message_routing.update(
            {"init_world": self.init_world,
             "transmission": self.transmission})

    def init_world(self, message):
        """
        Initialize the world we're operating in for this demo.
        """
        # DEBUG
        _log.debug('Creating puny world')

        # Add rooms and droids
        last_room = None
        first_room = None

        for clean_droids, infected_droids in ROOM_STRUCTURE:
            room = self.hive.create_actor(WarehouseRoom)

            if last_room:
                self.hive.send_message(
                    to=last_room,
                    directive="set_next_room",
                    body={"id": room})
                self.hive.send_message(
                    to=room,
                    directive="set_previous_room",
                    body={"id": last_room})

            for droid_num in range(clean_droids):
                droid = self.hive.create_actor(
                    Droid, infected=False, room=room)
                _log.debug('New droid created')
                yield self.wait_on_message(
                    to=droid,
                    directive="register_with_room")
                _log.debug('I guess this never really happens')

            for droid_num in range(infected_droids):
                droid = self.hive.create_actor(
                    Droid, infected=True, room=room)
                yield self.wait_on_message(
                    to=droid,
                    directive="register_with_room")

            last_room = room
            if first_room == None:
                first_room = room

        # Add security robot
        security_robot = self.hive.create_actor(SecurityRobot)

        # Tell the security robot to begin their mission
        self.hive.send_message(
            to=security_robot,
            directive="begin_mission",
            body={
                "starting_room": first_room})

    def transmission(self, message):
        print(message.body['message'])


class WarehouseRoom(Actor):
    """
    A room full of robots.
    """
    def __init__(self, hive, id):
        super(WarehouseRoom, self).__init__(hive, id)
        self.droids = []
        self.next_room = None
        self.previous_room = None

        self.message_routing.update(
            {"set_next_room": self.set_next_room,
             "set_previous_room": self.set_previous_room,
             "get_next_room": self.get_next_room,
             "get_previous_room": self.get_previous_room,
             "register_droid": self.register_droid,
             "list_droids": self.list_droids})


    def set_next_room(self, message):
        self.next_room = message.body['id']

    def set_previous_room(self, message):
        self.previous_room = message.body['id']

    def get_next_room(self, message):
        message.reply(
            {"id": self.next_room})

    def get_previous_room(self, message):
        message.reply(
            {"id": self.previous_room})

    def list_droids(self, message):
        message.reply(
            {"droid_ids": self.droids})

    def register_droid(self, message):
        self.droids.append(message.body['droid_id'])


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
        _log.debug('Droid {0} registering'.format(self.id))
        yield self.wait_on_message(
            to=self.room,
            directive="register_droid",
            body={"droid_id": self.id})

        _log.debug('Registered droid {0}!'.format(self.id))

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
        self.room = message.body['starting_room']

        overseer_id = join_id("overseer", self.hive.hive_id)

        # Walk through all rooms, clearing out infected droids
        while True:
            self.hive.send_message(
                to=overseer_id,
                directive="transmission",
                body={
                    "message": "Entering room %s..." % self.room})

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
                    transmission = (
                        "%s is clean... moving on." % droid_id)
                    self.hive.send_message(
                        to=overseer_id,
                        directive="transmission",
                        body={
                            "message": transmission})
                    continue

                # Let the overseer know we found an infected droid
                # and are engaging
                transmission = (
                    "%s found to be infected... taking out" % droid_id)
                self.hive.send_message(
                    to=overseer_id,
                    directive="transmission",
                    body={
                        "message": transmission})

                # Keep firing till it's dead.
                infected_droid_alive = True
                while infected_droid_alive:
                    response = yield self.wait_on_message(
                        to=droid_id,
                        directive="get_shot")

                    # Relay the droid status
                    droid_status = self.__droid_status_format(response)

                    self.hive.send_message(
                        to=overseer_id,
                        directive="transmission",
                        body={
                            "message": droid_status})

                    infected_droid_alive = response.body["alive"]

            # switch to next room, if there is one
            response = yield self.wait_on_message(
                to=self.room,
                directive="get_next_room")
            next_room = response.body["id"]
            if next_room:
                self.room = next_room
            else:
                # We're done scanning rooms finally
                break

        # Good job everyone! Shut down the operation.
        yield self.wait_on_message(
            to=overseer_id,
            directive="transmission",
            body={
                "message": "Mission accomplished."})
        self.hive.send_shutdown()


def main():
    # Set up logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.WARNING)

    # Invoke the destruction deity
    hive = Hive()

    # Add overseer, who populates the world and reports things
    overseer_id = hive.create_actor(Overseer, id="overseer")
    hive.send_message(
        to=overseer_id,
        directive="init_world")

    hive.run()


if __name__ == "__main__":
    main()

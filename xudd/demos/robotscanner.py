from __future__ import print_function

from xudd.hive import Hive
from xudd.actor import Actor

# List of room tuples of (clean_droids, infected_droids)

ROOM_STRUCTURE = [
    (3, 1),
    (0, 2),
    (8, 5),
    (5, 0),
    (2, 1)]


class Overseer(Actor):
    def __init__(self, *args, **kwargs):
        super(Overseer, self).__init__(*args, **kwargs)

        self.message_routing.extend(
            {"init_world": self.init_world,
             "transmission": self.transmission,
             "compile_and_shutdown": self.compile_and_shutdown})

    def init_world(self):
        # Add rooms and droids
        last_room = None
        first_room = None

        for clean_droids, infected_droids in ROOM_STRUCTURE:
            room = WarehouseRoom(self.hive)

            if last_room:
                self.hive.send_message(
                    to=last_room.id,
                    directive="set_next_room",
                    body={"id": room.id})
                self.hive.send_message(
                    to=room.id,
                    directive="set_previous_room",
                    body={"id": last_room.id})

            for droid_num in range(clean_droids):
                droid = Droid(self.hive, infected=False, room=room.id)
                yield self.wait_on_message(
                    to=droid.id,
                    directive="register_with_room")

            for droid_num in range(infected_droids):
                droid = Droid(self.hive, infected=True, room=room.id)
                yield self.wait_on_message(
                    to=droid.id,
                    directive="register_with_room")

            last_room = room
            if first_room == None:
                first_room = room

        # Add security robot
        security_robot = SecurityRobot(self.hive)

        # Tell the security robot to begin their mission
        self.hive.send_message(
            to=security_robot.id,
            directive="begin_mission",
            body={
                "starting_room": first_room.id})

    def transmission(self, message):
        print_function(message.body['message'])


class WarehouseRoom(Actor):
    def __init__(self, *args, **kwargs):
        super(WarehouseRoom, self).__init__(*args, **kwargs)
        self.droids = []
        self.next_room = None
        self.previous_room = None

    def set_next_room(self, message):
        pass

    def set_previous_room(self, message):
        pass

    def register_droid(self, message):
        self.droids.append(message.body['droid_id'])


class Droid(Actor):
    pass


class SecurityRobot(Actor):
    pass


def main():
    hive = Hive()

    # Add overseer, who populates the world and reports things
    overseer = Overseer(hive, id="overseer")
    hive.send_message(
        to="overseer",
        directive="init_world")

    hive.workloop()

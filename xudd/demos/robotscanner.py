from xudd.hive import Hive
from xudd.actor import Actor

class SecurityRobot(Actor):
    pass


class Overseer(Actor):
    def init_world(self):
        # Add rooms and droids
        last_room = None
        first_room = None

        for clean_droids, infected_droids in ROOM_STRUCTURE:
            room = WarehouseRoom(self.hive)

            if last_room:
                last_room.next_room = room.id
                room.previous_room = last_room.id

            for droid_num in range(clean_droids):
                droid = Droid(self.hive, infected=False, room=room.id)
                result = yield self.wait_on_message(
                    to=droid.id,
                    directive="register_with_room")

            for droid_num in range(infected_droids):
                droid = Droid(self.hive, infected=True, room=room.id)
                result = yield self.wait_on_message(
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

    def compile_and_shutdown(self):
        pass


class WarehouseRoom(Actor):
    pass

class Droid(Actor):
    pass


# List of room tuples of (clean_droids, infected_droids)

ROOM_STRUCTURE = [
    (3, 1),
    (0, 2),
    (8, 5),
    (5, 0),
    (2, 1)]


def main():
    hive = Hive()

    # Add overseer, who populates the world and reports things
    overseer = Overseer(hive, id="overseer")
    hive.send_message(
        to="overseer",
        directive="init_world")

    hive.workloop()

from __future__ import print_function

import argparse
from itertools import count
import random

from xudd.hive import Hive
from xudd.actor import Actor


class Student(Actor):
    def __init__(self, hive, id):
        super(Student, self).__init__(hive, id)
        self.message_routing.update(
            {"bother_professor": self.bother_professor,
             "avada_kedavra": self.avada_kedavraed})

        self.dead = False

    def bother_professor(self, message):
        while not self.dead:
            print("%s: Bother bother bother!" % self.id)
            yield self.send_message(
                to=message.body["target"],
                directive="be_bothered",
                body={
                    "noise": "Bother bother bother!"})

    def avada_kedavraed(self, message):
        """
        This kills the student.
        """
        print("%s says: AHHHHHH!!!! I'm dead!" % self.id)
        self.dead = True
        # self.hive.send_shutdown()


COMPLAINTS = ["Hey!", "Stop that!", "Ooof!"]

class Professor(Actor):
    def __init__(self, hive, id):
        super(Professor, self).__init__(hive, id)

        self.message_routing.update(
            {"be_bothered": self.be_bothered})
        self.being_bothered = set()


    def be_bothered(self, message):
        self.being_bothered.add(message.from_id)
        message.reply(
            body={"noise": "Hey! Stop it!"})
        print("%s: %s" % (self.id, random.choice(COMPLAINTS)))

        if len(self.being_bothered) > 1:
            print("%s: AVADA KEDAVRA!" % self.id)
            for target in self.being_bothered:
                self.hive.send_message(
                    to=target,
                    directive="avada_kedavra")

        self.being_bothered.remove(message.from_id)
            

STUDENTS = [
    ("Harry", count()),
    ("Hermione", count()),
    ("Ron", count())]


def gen_student_name():
    name, counter = random.choice(STUDENTS)
    next = counter.__next__()

    return "%s-%s" % (name, next)


def main():
    parser = argparse.ArgumentParser(
        description="Potter Puppet Pals simulator")
    parser.add_argument(
        "-s", "--students",
        help="Number of students",
        default=5, type=int)
    parser.add_argument(
        "-w", "--workers",
        help="How many worker threads running in the hive",
        default=5, type=int)

    args = parser.parse_args()

    hive = Hive()

    snape = hive.create_actor(
        Professor, id="snape")

    for i in range(args.students):
        student = hive.create_actor(
            Student, id=gen_student_name())
        hive.send_message(
            to=student,
            directive="bother_professor",
            body={
                "target": snape})

    hive.run()


if __name__ == "__main__":
    main()

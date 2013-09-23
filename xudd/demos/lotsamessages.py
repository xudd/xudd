"""
"""
from __future__ import print_function

import argparse

from xudd.tools import join_id
from xudd.hive import Hive
from xudd.actor import Actor
from xudd.lib.multiprocess import MultiProcessAmbassador


class SuccessTracker(object):
    def __init__(self):
        self.success = False


def worker_allocation(jobs, workers):
    """
    Return jobs allocated to workers.  Lazy implementation.

    Given an iterable of jobs to be processed, and an iterable of
    available workers, it lines 'em up!
    """
    worker_len = len(workers)
    assert worker_len != 0
    current_worker = 0

    allocation = []

    for job in jobs:
        allocation.append((job, workers[current_worker]))

        current_worker += 1
        if current_worker >= worker_len:
            current_worker = 0

    return allocation


class DepartmentChair(Actor):
    """
    Actor that initializes the world of this demo, starts the mission,
    and sends information about what's going on back to the user.
    """
    def __init__(self, hive, id, num_worker_processes=0):
        super(DepartmentChair, self).__init__(hive, id)

        self.message_routing.update(
            {"oversee_experiments": self.oversee_experiments,
             "experiment_is_done": self.experiment_is_done,
             "setup_worker_processes": self.setup_worker_processes})
        self.experiments_in_progress = set()
        self.success_tracker = None
        self.num_worker_processes = num_worker_processes
        # we set this up in setup()
        self.worker_hives = []

    def setup_worker_processes(self, message):
        """
        Set up all our worker hives, if they aren't already.

        Note, if self.num_worker_processes is 0, we just set our own hive
        as the worker hive.
        """
        if self.worker_hives:
            # already set up!
            return

        if self.num_worker_processes > 0:
            # set up worker processes, record hive ids
            for i in range(self.num_worker_processes):
                # Create the delegate
                ambassador = self.hive.create_actor(MultiProcessAmbassador)
                response = yield self.wait_on_message(
                    to=ambassador,
                    directive="get_remote_hive_id")

                self.worker_hives.append(response.body["hive_id"])
        else:
            self.worker_hives = [self.hive.hive_id]

    def oversee_experiments(self, message):
        yield self.wait_on_message(
            to=self.id,
            directive="setup_worker_processes")

        num_experiments = message.body['num_experiments']
        num_steps = message.body['num_steps']

        if message.body.get('success_tracker'):
            self.success_tracker = message.body['success_tracker']

        print("Starting %s experiments with %s steps each" % (
            num_experiments, num_steps))

        allocation = worker_allocation(
            self.worker_hives, range(num_experiments))
        for i, hive_id in allocation:
            response = yield self.wait_on_message(
                to=join_id("hive", hive_id),
                directive="create_actor",
                body={
                    "class": "xudd.demos.lotsamessages:Professor"})
            professor = response.body['actor_id']

            response = yield self.wait_on_message(
                to=join_id("hive", hive_id),
                directive="create_actor",
                body={
                    "class": "xudd.demos.lotsamessages:Assistant"})
            assistant = response.body['actor_id']
            self.experiments_in_progress.add(professor)
            self.hive.send_message(
                to=professor,
                directive="run_experiments",
                body={
                    "assistant_id": assistant,
                    "numtimes": num_steps})
            
    def experiment_is_done(self, message):
        self.experiments_in_progress.remove(message.from_id)
        print("%s experiment is done" % message.from_id)
        if len(self.experiments_in_progress) == 0:
            print(
                "Last experiment message (%s) received from (%s), shutting down" % (
                    message.id, message.from_id))

            if self.success_tracker is not None:
                self.success_tracker.success = True

            self.hive.send_shutdown()


class Professor(Actor):
    def __init__(self, hive, id):
        super(Professor, self).__init__(hive, id)

        self.message_routing.update(
            {"run_experiments": self.run_experiments})

    def run_experiments(self, message):
        """Run an experiment... but really, this means asking your assistant
        to constantly do run stupid errands...
        """
        assistant = message.body['assistant_id']

        for i in range(message.body['numtimes']):
            yield self.wait_on_message(
                to=assistant,
                directive="run_errand")

        self.hive.send_message(
            to=message.from_id,
            directive="experiment_is_done")


class Assistant(Actor):
    def __init__(self, hive, id):
        super(Assistant, self).__init__(hive, id)

        self.message_routing.update(
            {"run_errand": self.run_errand})

    def run_errand(self, message):
        message.reply(
            {"did_your_grunt_work": True})


DEFAULT_NUM_EXPERIMENTS = 20
DEFAULT_NUM_STEPS = 5000


def main(num_experiments=DEFAULT_NUM_STEPS, num_steps=DEFAULT_NUM_STEPS,
         subprocesses=None):
    """
    Returns True if the experiment was a success.
    """
    success_tracker = SuccessTracker()

    hive = Hive()

    department_chair = hive.create_actor(
        DepartmentChair)

    hive.send_message(
        to=department_chair,
        directive="oversee_experiments",
        body={
            "num_experiments": num_experiments,
            "num_steps": num_steps,
            "success_tracker": success_tracker})

    hive.run()

    return success_tracker.success


def cli():
    parser = argparse.ArgumentParser(
        description="Lots of Messages experiment")
    parser.add_argument(
        "-e", "--experiments",
        help="Number of experiments to run",
        default=DEFAULT_NUM_EXPERIMENTS, type=int)
    parser.add_argument(
        "-s", "--steps",
        help="Number of steps each experiment should require",
        default=DEFAULT_NUM_STEPS, type=int)
    parser.add_argument(
        "-p", "--subprocesses",
        help="Number of multiprocess subprocesses to run these tasks",
        default=0, type=int)

    args = parser.parse_args()
    main(args.experiments, args.steps, args.subprocesses)


if __name__ == "__main__":
    cli()

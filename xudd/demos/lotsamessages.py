from xudd.hive import Hive
from xudd.actor import Actor

class DepartmentChair(Actor):
    """
    Actor that initializes the world of this demo, starts the mission,
    and sends information about what's going on back to the user.
    """
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)

        self.message_routing.update(
            {"oversee_experiments": self.oversee_experiments,
             "experiment_is_done": self.experiment_is_done})
        self.waiting_on_experiments = set()

    def oversee_experiments(self, message):
        for i in range(20):
            professor = self.hive.create_actor(Professor)
            assistant = self.hive.create_actor(Assistant)
            self.experiments_in_progress.add(professor)
            self.hive.send_message(
                to=professor,
                directive="run_experiments",
                body={
                    "assistant_id": assistant,
                    "numtimes": 1000})
            
    def experiment_is_done(self, message):
        self.experiments_in_progress.remove(message.from_id)
        print("%s experiment is done" % message.from_id)
        if len(self.experiments_in_progress) == 0:
            self.hive.send_shutdown()


class Professor(Actor):
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)

        self.message_routing.update(
            {"run_experiments": self.run_experiments})

    def run_experiment(self, message):
        """Run an errand... but really, this means asking your assistant
        to constantly do run stupid errands...
        """
        assistant = message.body['assistant_id']

        for i in range(message.body['numtimes']):
            yield self.wait_on_message(
                to=assistant,
                directive="run_errand")


class Assistant(Actor):
    def __init__(self, hive, id):
        super(self.__class__, self).__init__(hive, id)

        self.message_routing.update(
            {"run_errand": self.run_errand})

    def run_errand(self, message):
        self.hive.send_message(
            to=message.from_id,
            directive="result",
            in_reply_to=message.id,
            body={
                "did_your_grunt_work": True})


def main():
    hive = Hive(num_workers=5)

    department_chair = hive.create_actor(
        DepartmentChair)

    hive.send_message(
        to=department_chair,
        directive="oversee_experiments")

    hive.run()


if __name__ == "__main__":
    main()

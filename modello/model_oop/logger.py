import timeit
from datetime import timedelta, datetime

from salabim import Component


class Logger(Component):
    simulation: "Simulation"
    wait_time: int
    start_time: float
    last_time: float

    # noinspection PyMethodOverriding
    def setup(self, simulation: "Simulation", wait_time: int):
        self.simulation = simulation
        self.wait_time = wait_time
        self.start_time = timeit.default_timer()
        self.last_time = timeit.default_timer()

    def process(self):
        while True:
            now = self.simulation.env.now()
            duration = timeit.default_timer() - self.last_time
            self.last_time = timeit.default_timer()
            delta = timedelta(seconds=self.last_time - self.start_time)
            remaining_time = timedelta(seconds=duration * (self.simulation.duration - now))
            eta = remaining_time + datetime.now()
            self.simulation.log(f"day: {now:3}", "-",
                                "elapsed time:", str(delta).split(".")[0], "-",
                                f"day duration: {round(duration):3} sec", "-",
                                "ETA:", str(eta).split(".")[0],
                                f"(remaining time {str(remaining_time).split('.')[0]})")
            yield self.hold(self.wait_time)

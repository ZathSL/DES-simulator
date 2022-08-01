import multiprocessing

from model_oop.simulation import Simulation
from stats import calc_mdc_distribution_stats, calc_hospitalization_type_stats, calc_beds_stats
from mutations import increase_all_beds_percent


def run_simulation(run: int, duration: int, name: str, mutations):
    simulation = Simulation(name=name, run_n=run, duration=duration, mutations=mutations)
    simulation.run()


def test(runs: range, duration: int, name: str, mutations, stats: bool):
    if mutations is None:
        mutations = []
    for run in runs:
        run_simulation(run, duration, name, mutations)
    if stats:
        calc_stats(name, len(runs))


def test_parallel(runs: range, duration: int, name: str, mutations):
    if mutations is None:
        mutations = []
    for run in runs:
        multiprocessing.Process(target=run_simulation, args=(run, duration, name, mutations)).start()


def calc_stats(name: str, runs: int):
    calc_beds_stats(name, runs)
    calc_hospitalization_type_stats(name, runs)
    calc_mdc_distribution_stats(name, runs)


if __name__ == "__main__":
    # test(range(0, 1), 3, "test", None, False)
    # test(runs=range(0, 25), duration=360, name="all_beds_increment_5perc", mutations=None, stats=False)
    # test(runs=range(0, 25), duration=360, mutations=increase_all_beds_percent(5), name="increase_all_beds_5_percent", stats=True)
    calc_stats("base", 25)
    # test(runs=range(0, 1), duration=360, mutations=change_convalescence_avg_time(14), name="test_convalescence_avg_time_14", stats=False)
    # base_test(runs=2, duration=1, mutations=increase_all_beds_percent(5), name="increase_all_beds_5_percent")
    # base_test(runs=2, duration=1, mutations=increase_all_beds_percent(10), name="increase_all_beds_10_percent")
    # base_test(runs=2, duration=1, mutations=decrease_all_beds_percent(5), name="decrease_all_beds_5_percent")
    # base_test(runs=2, duration=1, mutations=decrease_all_beds_percent(10), name="decrease_all_beds_10_percent")
    # base_test(runs=2, duration=1, mutations=delete_5_smallest_structures(), name="delete_5_smallest_structures")
    # base_test(runs=2, duration=1, mutations=delete_5_biggest_structures(), name="delete_5_biggest_structures")

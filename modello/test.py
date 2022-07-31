import shutil
import multiprocessing
from model import simulation
from stats import calc_mdc_distribution_stats, calc_hospitalization_type_stats, calc_beds_stats
from util import CodeTimer


def test(runs: range, duration: int, name: str, mutations=None, stats=True):
    if mutations is None:
        mutations = []

    # shutil.rmtree(f"../statistiche/{name}", ignore_errors=True)
    for i in runs:
        simulation(trace=False, sim_time_days=duration, animate=False, speed=10, mutations=mutations,
                   statistics_dir=f"../statistiche/{name}/runs/{i}/", random_seed=i)
    if stats:
        calc_stats(name, len(runs))


def calc_stats(name: str, runs: int):
    calc_beds_stats(name, runs)
    calc_hospitalization_type_stats(name, runs)
    calc_mdc_distribution_stats(name, runs)


if __name__ == "__main__":
    multiprocessing.Process(target=test, args=(range(6, 8), 1, "base", None, False)).start()
    multiprocessing.Process(target=test, args=(range(8, 10), 1, "base", None, False)).start()
    # multiprocessing.Process(target=test, args=(range(4, 5), 365, "base", None, False)).start()
    # test(runs=range(0, 2), duration=365, name="base", mutations=None, stats=False)

    # test(runs=range(2), duration=1, name="base")  # test veloce
    # test(runs=range(0, 10), duration=365, name="base", stats=False)
    # test(runs=range(10, 20), duration=365, name="base", stats=False)
    # calc_stats("base", 20)
    # base_test(runs=2, duration=1, mutations=increase_all_beds_percent(5), name="increase_all_beds_5_percent")
    # base_test(runs=2, duration=1, mutations=increase_all_beds_percent(10), name="increase_all_beds_10_percent")
    # base_test(runs=2, duration=1, mutations=decrease_all_beds_percent(5), name="decrease_all_beds_5_percent")
    # base_test(runs=2, duration=1, mutations=decrease_all_beds_percent(10), name="decrease_all_beds_10_percent")
    # base_test(runs=2, duration=1, mutations=delete_5_smallest_structures(), name="delete_5_smallest_structures")
    # base_test(runs=2, duration=1, mutations=delete_5_biggest_structures(), name="delete_5_biggest_structures")

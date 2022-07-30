import shutil

from model import simulation
from modello.stats import calc_mdc_distribution_stats, calc_hospitalization_type_stats, calc_beds_stats
from util import CodeTimer


def test(runs: int, duration: int, name: str, mutations=None):
    if mutations is None:
        mutations = []
    shutil.rmtree(f"../statistiche/{name}", ignore_errors=True)
    for i in range(runs):
        simulation(trace=False, sim_time_days=duration, animate=False, speed=10, mutations=mutations,
                   statistics_dir=f"../statistiche/{name}/runs/{i}/", random_seed=i)
    calc_beds_stats(name, runs)
    calc_hospitalization_type_stats(name, runs)
    calc_mdc_distribution_stats(name, runs)


if __name__ == "__main__":
    with CodeTimer():
        test(runs=2, duration=1, name="base")
        # base_test(runs=2, duration=1, mutations=mutations_example(), name="mutations_example")
        # base_test(runs=2, duration=1, mutations=increase_all_beds_percent(5), name="increase_all_beds_5_percent")
        # base_test(runs=2, duration=1, mutations=increase_all_beds_percent(10), name="increase_all_beds_10_percent")
        # base_test(runs=2, duration=1, mutations=decrease_all_beds_percent(5), name="decrease_all_beds_5_percent")
        # base_test(runs=2, duration=1, mutations=decrease_all_beds_percent(10), name="decrease_all_beds_10_percent")
        # base_test(runs=2, duration=1, mutations=delete_5_smallest_structures(), name="delete_5_smallest_structures")
        # base_test(runs=2, duration=1, mutations=delete_5_biggest_structures(), name="delete_5_biggest_structures")

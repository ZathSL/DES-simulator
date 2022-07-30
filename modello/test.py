from model import simulation
from modello.stats import calc_mdc_distributions, calc_hospitalization_type_distributions, calc_beds_stats
from util import CodeTimer


def base_test(runs: int, duration: int, name: str, mutations=None):
    if mutations is None:
        mutations = []
    for i in range(runs):
        simulation(trace=False, sim_time_days=duration, animate=False, speed=10, mutations=mutations,
                   statistics_dir=f"../statistiche/{name}/runs/{i}/", random_seed=i)
    calc_beds_stats(name, runs)
    calc_hospitalization_type_distributions(name, runs)
    calc_mdc_distributions(name, runs)


if __name__ == "__main__":
    with CodeTimer():
        base_test(runs=10, duration=1, name="base_test")
        # base_test(runs=10, duration=1, mutations=mutations_example(), name="mutations_example")
        # base_test(runs=10, duration=1, mutations=increase_all_beds_percent(5), name="increase_all_beds_5_percent")
        # base_test(runs=10, duration=1, mutations=increase_all_beds_percent(10), name="increase_all_beds_10_percent")
        # base_test(runs=10, duration=1, mutations=decrease_all_beds_percent(5), name="decrease_all_beds_5_percent")
        # base_test(runs=10, duration=1, mutations=decrease_all_beds_percent(10), name="decrease_all_beds_10_percent")
        # base_test(runs=10, duration=1, mutations=delete_5_smallest_structures(), name="delete_5_smallest_structures")
        # base_test(runs=10, duration=1, mutations=delete_5_biggest_structures(), name="delete_5_biggest_structures")

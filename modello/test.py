import inspect
import os
import shutil

import pandas as pd

from model import simulation, Mutation
from util import CodeTimer


def test_main():
    logfile = False  # open("sim_trace.log", "w")
    sim_time_days = 365
    animate = False
    speed = 10
    mutations = []
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_main2():
    logfile = False  # open("sim_trace.log", "w")
    sim_time_days = 2
    animate = False
    speed = 10
    mutations = []
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_mutations_example():
    logfile = False  # open("sim_trace.log", "w")
    sim_time_days = 365
    animate = False
    speed = 10
    mutations = [  # mutazioni di esempio, l'ordine delle mutazioni conta
        Mutation(type="structure", id="030070-00", ops={"delete": True}),  # elimina la struttura
        Mutation(type="structure", id="030017-00", ops={"beds": 10}),  # imposta i letti della struttura a 10
        Mutation(type="structure", id="030038-00", ops={"beds": 0.50}),  # riduce i letti della struttura del 50%
        Mutation(type="structure", id="*", ops={"beds": 1.10}),  # aumenta i letti di tutte le strutture del 10%
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_delete_5_biggest_structures():
    logfile = False
    sim_time_days = 365
    animate = False
    speed = 15
    mutations = [
        Mutation(type="structure", id="030901-01", ops={"delete": True}),
        Mutation(type="structure", id="030905-00", ops={"delete": True}),
        Mutation(type="structure", id="030906-00", ops={"delete": True}),
        Mutation(type="structure", id="030913-00", ops={"delete": True}),
        Mutation(type="structure", id="030924-00", ops={"delete": True}),
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_delete_5_smallest_structures():
    logfile = False
    sim_time_days = 365
    animate = False
    speed = 10
    mutations = [
        Mutation(type="structure", id="030070-00", ops={"delete": True}),
        Mutation(type="structure", id="030071-00", ops={"delete": True}),
        Mutation(type="structure", id="030071-01", ops={"delete": True}),
        Mutation(type="structure", id="030075-00", ops={"delete": True}),
        Mutation(type="structure", id="030079-00", ops={"delete": True})
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_decrease_all_beds_10():
    logfile = False
    sim_time_days = 365
    animate = False
    speed = 15
    mutations = [
        Mutation(type="structure", id="*", ops={"beds": 0.90})
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_increase_all_beds_10():
    logfile = False
    sim_time_days = 365
    animate = False
    speed = 15
    mutations = [
        Mutation(type="structure", id="*", ops={"beds": 1.10})
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_decrease_all_beds_5():
    logfile = False
    sim_time_days = 365
    animate = False
    speed = 15
    mutations = [
        Mutation(type="structure", id="*", ops={"beds": 0.95})
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_increase_all_beds_5():
    logfile = False
    sim_time_days = 365
    animate = False
    speed = 15
    mutations = [
        Mutation(type="structure", id="*", ops={"beds": 1.05})
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_change_convalescence_avg_time():
    logfile = False
    sim_time_days = 1
    animate = False
    speed = 15
    mutations = [
        Mutation(type="parameter", id="convalescence_avg_time", ops={"value": 15}),
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_mdc_distributions():
    sim_time_days = 1  # FIXME: incrementare
    mdc_stats = []
    for i in range(3):  # FIXME: incrementare
        simulation(trace=False, sim_time_days=sim_time_days, animate=False, speed=10, mutations=[],
                   statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/", random_seed="*")
        csv = pd.read_csv(
            "../statistiche/" + inspect.currentframe().f_code.co_name + "/number_patient_mdc.csv")
        mdc_stats.append(csv)
        shutil.rmtree("../statistiche/" + inspect.currentframe().f_code.co_name)
    frame = pd.DataFrame(list(map(lambda x: x["FREQUENCY"].to_numpy(), mdc_stats)))
    mean = frame.mean()  # FIXME: da migliorare
    os.makedirs("../statistiche/" + inspect.currentframe().f_code.co_name)
    mean.to_csv("../statistiche/" + inspect.currentframe().f_code.co_name + "/number_patient_mdc_mean.csv")


if __name__ == "__main__":
    with CodeTimer():
        # test_main()
        test_main2()
        # test_mutations_example()
        # test_delete_5_biggest_structures()
        # test_delete_5_smallest_structures()
        # test_decrease_all_beds_10()
        # test_increase_all_beds_10()
        # test_decrease_all_beds_5()
        # test_increase_all_beds_5()
        # test_change_convalescence_avg_time()
        # test_mdc_distributions()
        # p1 = multiprocessing.Process(name='delete_5_biggest', target=test_delete_5_smallest_structures())
        # p2 = multiprocessing.Process(name='delete_5_smallest', target=test_delete_5_smallest_structures())
        # p1.start()
        # p2.start()

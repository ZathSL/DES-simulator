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
    sim_time_days = 365
    animate = False
    speed = 15
    mutations = [
        Mutation(type="parameter", id="convalescence_avg_time", ops={"value": 15}),
    ]
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed, mutations=mutations,
               statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/")


def test_mdc_distributions():
    sim_time_days = 30
    mdc_stats = []
    for i in range(10):
        simulation(trace=False, sim_time_days=sim_time_days, animate=False, speed=10, mutations=[],
                   statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + "/", random_seed=i)
        csv = pd.read_csv("../statistiche/" + inspect.currentframe().f_code.co_name + "/number_patient_mdc.csv",
                          keep_default_na=False, dtype={"MDC": str}, index_col="MDC")
        mdc_stats.append(csv)
        shutil.rmtree("../statistiche/" + inspect.currentframe().f_code.co_name)
    frame = pd.concat((df["FREQUENCY"].rename(str(i)) for i, df in enumerate(mdc_stats)), axis=1)
    mean = frame.transpose().mean()
    mean /= mean.sum()
    mean.rename("FREQUENCY", inplace=True)
    os.makedirs("../statistiche/" + inspect.currentframe().f_code.co_name)
    mean.to_csv("../statistiche/" + inspect.currentframe().f_code.co_name + "/number_patient_mdc_mean.csv",
                float_format="%.15f", encoding="utf-8")
    original = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False,
                           dtype={"CODICE MDC": str}, index_col="CODICE MDC")
    original = original["FREQUENZA"]
    pearson = mean.corr(original, method="pearson")
    spearman = mean.corr(original, method="spearman")
    kendall = mean.corr(original, method="kendall")
    with open("../statistiche/" + inspect.currentframe().f_code.co_name + "/correlation.txt", "w") as f:
        f.write("Pearson: " + str(pearson) + "\n")
        f.write("Spearman: " + str(spearman) + "\n")
        f.write("Kendall: " + str(kendall) + "\n")


def test_hospitalization_type_distributions():
    sim_time_days = 30
    mdc_stats = []
    for i in range(10):
        simulation(trace=False, sim_time_days=sim_time_days, animate=False, speed=10, mutations=[],
                   statistics_dir="../statistiche/" + inspect.currentframe().f_code.co_name + f"/{i}/", random_seed=i)
        csv = pd.read_csv("../statistiche/" + inspect.currentframe().f_code.co_name + f"/{i}/type_patients_treated.csv",
                          keep_default_na=False, index_col="STRUTTURA")
        mdc_stats.append(csv)
    frame_ds = pd.concat((df["RICOVERI DS"].rename(str(i)) for i, df in enumerate(mdc_stats)), axis=1)
    frame_dh = pd.concat((df["RICOVERI DH"].rename(str(i)) for i, df in enumerate(mdc_stats)), axis=1)
    frame_do = pd.concat((df["RICOVERI DO"].rename(str(i)) for i, df in enumerate(mdc_stats)), axis=1)
    mean_ds = frame_ds.transpose().mean().rename("RICOVERI DS")
    mean_dh = frame_dh.transpose().mean().rename("RICOVERI DH")
    mean_do = frame_do.transpose().mean().rename("RICOVERI DO")
    concat = pd.concat([mean_ds, mean_dh, mean_do], axis=1)
    concat.to_csv("../statistiche/" + inspect.currentframe().f_code.co_name + "/type_patients_treated_mean.csv",
                  float_format="%.15f", encoding="utf-8")
    original = pd.read_csv("../distribuzioni/empiriche/TipologieAccessi/TipologieAccessiDistribution.csv",
                           keep_default_na=False, dtype={"CODICE MDC": str}, index_col="CODICE MDC")
    original["RICOVERI DS"] *= original["TOTALE RICOVERI"]
    original["RICOVERI DH"] *= original["TOTALE RICOVERI"]
    original["RICOVERI DO"] *= original["TOTALE RICOVERI"]
    with open("../statistiche/" + inspect.currentframe().f_code.co_name + "/correlation.txt", "w") as f:
        for df, col in zip([mean_ds, mean_dh, mean_do], ["RICOVERI DS", "RICOVERI DH", "RICOVERI DO"]):
            f.write(col + ":\n")
            f.write("\tPearson: " + str(df.corr(original[col], method="pearson")) + "\n")
            f.write("\tSpearman: " + str(df.corr(original[col], method="spearman")) + "\n")
            f.write("\tKendall: " + str(df.corr(original[col], method="kendall")) + "\n")
            f.write("\n")


if __name__ == "__main__":
    with CodeTimer():
        # test_main()
        # test_mutations_example()
        # test_delete_5_biggest_structures()
        # test_delete_5_smallest_structures()
        # test_decrease_all_beds_10()
        # test_increase_all_beds_10()
        # test_decrease_all_beds_5()
        # test_increase_all_beds_5()
        # test_change_convalescence_avg_time()
        # test_mdc_distributions()
        # test_hospitalization_type_distributions()
        # p1 = multiprocessing.Process(name='delete_5_biggest', target=test_delete_5_smallest_structures())
        # p2 = multiprocessing.Process(name='delete_5_smallest', target=test_delete_5_smallest_structures())
        # p1.start()
        # p2.start()
        pass

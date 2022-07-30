import numpy as np
import pandas as pd

from model import simulation, Mutation
from util import CodeTimer


def test_mutations_example():
    return [  # mutazioni di esempio, l'ordine delle mutazioni conta
        Mutation(type="structure", id="030070-00", ops={"delete": True}),  # elimina la struttura
        Mutation(type="structure", id="030017-00", ops={"beds": 10}),  # imposta i letti della struttura a 10
        Mutation(type="structure", id="030038-00", ops={"beds": 0.50}),  # riduce i letti della struttura del 50%
        Mutation(type="structure", id="*", ops={"beds": 1.10}),  # aumenta i letti di tutte le strutture del 10%
    ]


def test_delete_5_biggest_structures():
    return [
        Mutation(type="structure", id="030901-01", ops={"delete": True}),
        Mutation(type="structure", id="030905-00", ops={"delete": True}),
        Mutation(type="structure", id="030906-00", ops={"delete": True}),
        Mutation(type="structure", id="030913-00", ops={"delete": True}),
        Mutation(type="structure", id="030924-00", ops={"delete": True}),
    ]


def test_delete_5_smallest_structures():
    return [
        Mutation(type="structure", id="030070-00", ops={"delete": True}),
        Mutation(type="structure", id="030071-00", ops={"delete": True}),
        Mutation(type="structure", id="030071-01", ops={"delete": True}),
        Mutation(type="structure", id="030075-00", ops={"delete": True}),
        Mutation(type="structure", id="030079-00", ops={"delete": True})
    ]


def test_decrease_all_beds_percent(percent: float):
    return [
        Mutation(type="structure", id="*", ops={"beds": 1.0 - percent / 100}),
    ]


def test_increase_all_beds_percent(percent: float):
    return [
        Mutation(type="structure", id="*", ops={"beds": 1.0 + percent / 100}),
    ]


def test_change_convalescence_avg_time(time: int):
    return [
        Mutation(type="parameter", id="convalescence_avg_time", ops={"value": time}),
    ]


def calc_mdc_distributions(name: str, runs: int):
    stats = []
    for i in range(runs):
        csv = pd.read_csv(f"../statistiche/{name}/runs/{i}/number_patient_mdc.csv", keep_default_na=False,
                          dtype={"MDC": str}, index_col="MDC")
        stats.append(csv)
    frame = pd.concat((df["FREQUENCY"].rename(str(i)) for i, df in enumerate(stats)), axis=1)
    mean = frame.transpose().mean()
    mean /= mean.sum()
    mean.rename("FREQUENCY", inplace=True)
    mean.to_csv(f"../statistiche/{name}/number_patient_mdc_mean.csv", float_format="%.15f", encoding="utf-8")
    original = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False,
                           dtype={"CODICE MDC": str}, index_col="CODICE MDC")
    original = original["FREQUENZA"]
    pearson = mean.corr(original, method="pearson")
    spearman = mean.corr(original, method="spearman")
    kendall = mean.corr(original, method="kendall")
    with open(f"../statistiche/{name}/correlation.txt", "w") as f:
        f.write("Pearson: " + str(pearson) + "\n")
        f.write("Spearman: " + str(spearman) + "\n")
        f.write("Kendall: " + str(kendall) + "\n")


def calc_hospitalization_type_distributions(name: str, runs: int):
    stats = []
    for i in range(runs):
        csv = pd.read_csv(f"../statistiche/{name}/runs/{i}/type_patients_treated.csv", keep_default_na=False,
                          index_col="STRUTTURA")
        stats.append(csv)
    dfs = []
    for key in stats[0].columns:
        df = pd.concat((df[key].rename(str(i)) for i, df in enumerate(stats)), axis=1)
        df = df.transpose()
        df_mean = df.mean().rename(key + "_MEDIA")
        df_var = df.var().rename(key + "_VARIANZA")
        df_lower_conf = (df_mean - (0.8159 * (np.sqrt(df_var / runs)))).rename(key + "_INTERVALLO CONFIDENZA INFERIORE")
        df_upper_conf = (df_mean + (0.8159 * (np.sqrt(df_var / runs)))).rename(key + "_INTERVALLO CONFIDENZA SUPERIORE")
        df = pd.concat([df_mean, df_var, df_lower_conf, df_upper_conf], axis=1)
        dfs.append(df)
    concat = pd.concat(dfs, axis=1)
    concat.sort_index(inplace=True)
    concat.to_csv(f"../statistiche/{name}/type_patients_treated_mean.csv", float_format="%.15f", encoding="utf-8")
    original = pd.read_csv("../distribuzioni/empiriche/Strutture/StruttureDistribution.csv", keep_default_na=False,
                           dtype={"CODICE STRUTTURA DI RICOVERO": str}, index_col="CODICE STRUTTURA DI RICOVERO")
    with open(f"../statistiche/{name}/correlation.txt", "w") as f:
        for col in ["RICOVERI DS", "RICOVERI DH", "RICOVERI DO"]:
            pearson = concat[col + "_MEDIA"].corr(original[col], method="pearson")
            spearman = concat[col + "_MEDIA"].corr(original[col], method="spearman")
            kendall = concat[col + "_MEDIA"].corr(original[col], method="kendall")
            f.write(f"{col}:\n")
            f.write(f"\tPearson: {pearson}\n")
            f.write(f"\tSpearman: {spearman}\n")
            f.write(f"\tKendall: {kendall}\n")
            f.write("\n")


def calc_beds_stats(name: str, runs: int):
    stats: list[pd.DataFrame] = []
    for i in range(runs):
        csv = pd.read_csv(f"../statistiche/{name}/runs/{i}/stats_beds.csv", keep_default_na=False,
                          index_col="VARIABILE CALCOLATA").transpose()
        stats.append(csv)
    dfs = []
    for key in stats[0].columns:
        df = pd.concat((df[key].rename(str(i)).astype(float) for i, df in enumerate(stats)), axis=1)
        df = df.transpose().mean().rename(key)
        dfs.append(df)
    frame = pd.concat(dfs, axis=1).transpose()
    frame.index.name = "VARIABILE CALCOLATA"
    frame["INTERVALLO CONFIDENZA INFERIORE"] = frame["MEDIA"] - (0.8159 * (np.sqrt(frame["VARIANZA"] / runs)))
    frame["INTERVALLO CONFIDENZA SUPERIORE"] = frame["MEDIA"] + (0.8159 * (np.sqrt(frame["VARIANZA"] / runs)))
    frame.to_csv(f"../statistiche/{name}/stats_beds_mean.csv", float_format="%.15f", encoding="utf-8")


def base_test(runs: int, sim_time_days: int, name: str, mutations=None):
    if mutations is None:
        mutations = []
    for i in range(runs):
        simulation(trace=False, sim_time_days=sim_time_days, animate=False, speed=10, mutations=mutations,
                   statistics_dir=f"../statistiche/{name}/runs/{i}/", random_seed=i)
    calc_beds_stats(name, runs)
    calc_hospitalization_type_distributions(name, runs)
    calc_mdc_distributions(name, runs)


if __name__ == "__main__":
    with CodeTimer():
        base_test(runs=10, sim_time_days=1, name="base_test")
        # base_test(runs=10, sim_time_days=1, mutations=test_mutations_example(), name="test_mutations_example")
        # base_test(runs=10, sim_time_days=1, mutations=test_increase_all_beds_percent(5), name="test_increase_all_beds_5_percent")
        # base_test(runs=10, sim_time_days=1, mutations=test_increase_all_beds_percent(10), name="test_increase_all_beds_10_percent")
        # base_test(runs=10, sim_time_days=1, mutations=test_decrease_all_beds_percent(5), name="test_decrease_all_beds_5_percent")
        # base_test(runs=10, sim_time_days=1, mutations=test_decrease_all_beds_percent(10), name="test_decrease_all_beds_10_percent")
        # base_test(runs=10, sim_time_days=1, mutations=test_delete_5_smallest_structures(), name="test_delete_5_smallest_structures")#
        # base_test(runs=10, sim_time_days=1, mutations=test_delete_5_biggest_structures(), name="test_delete_5_biggest_structures")

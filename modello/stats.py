import pandas as pd
from numpy import sqrt


def calc_mdc_distribution_stats(name: str, runs: int):
    stats = []
    for i in range(runs):
        csv = pd.read_csv(f"../statistiche/{name}/runs/{i}/number_patient_mdc.csv", keep_default_na=False,
                          dtype={"MDC": str}, index_col="MDC")
        stats.append(csv)
    frame = pd.concat((df["FREQUENCY"].rename(str(i)) for i, df in enumerate(stats)), axis=1)
    mean = frame.transpose().mean()
    mean /= mean.sum()
    mean.rename("FREQUENCY", inplace=True)
    mean.to_csv(f"../statistiche/{name}/mdc_distribution_mean.csv", float_format="%.15f", encoding="utf-8")
    original = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False,
                           dtype={"CODICE MDC": str}, index_col="CODICE MDC")
    original = original["FREQUENZA"]
    pearson = mean.corr(original, method="pearson")
    spearman = mean.corr(original, method="spearman")
    kendall = mean.corr(original, method="kendall")
    with open(f"../statistiche/{name}/mdc_distribution_correlation.txt", "w") as f:
        f.write("Pearson: " + str(pearson) + "\n")
        f.write("Spearman: " + str(spearman) + "\n")
        f.write("Kendall: " + str(kendall) + "\n")


def calc_hospitalization_type_stats(name: str, runs: int):
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
        df_std = df.std().rename(key + "_STD")
        df_lower_conf = (df_mean - (0.8159 * (sqrt(df_var / runs)))).rename(key + "_INTERVALLO CONFIDENZA INFERIORE")
        df_upper_conf = (df_mean + (0.8159 * (sqrt(df_var / runs)))).rename(key + "_INTERVALLO CONFIDENZA SUPERIORE")
        df = pd.concat([df_mean, df_var, df_std, df_lower_conf, df_upper_conf], axis=1)
        dfs.append(df)
    concat = pd.concat(dfs, axis=1)
    concat.sort_index(inplace=True)
    concat.to_csv(f"../statistiche/{name}/hospitalization_type_patients_treated_mean.csv", float_format="%.15f",
                  encoding="utf-8")
    concat.mean().to_csv(f"../statistiche/{name}/hospitalization_type_patients_treated_mean_mean.csv", header=False,
                         float_format="%.15f", encoding="utf-8")
    original = pd.read_csv("../distribuzioni/empiriche/Strutture/StruttureDistribution.csv", keep_default_na=False,
                           dtype={"CODICE STRUTTURA DI RICOVERO": str}, index_col="CODICE STRUTTURA DI RICOVERO")
    with open(f"../statistiche/{name}/hospitalization_type_patients_treated_correlation.txt", "w") as f:
        for col in ["RICOVERI DS", "RICOVERI DH", "RICOVERI DO", "TOTALE RICOVERI"]:
            pearson = concat[col + "_MEDIA"].corr(original[col], method="pearson")
            spearman = concat[col + "_MEDIA"].corr(original[col], method="spearman")
            kendall = concat[col + "_MEDIA"].corr(original[col], method="kendall")
            f.write(f"{col}:\n")
            f.write(f"\tPearson: {pearson}\n")
            f.write(f"\tSpearman: {spearman}\n")
            f.write(f"\tKendall: {kendall}\n")
            f.write("\n")


def calc_beds_stats(name: str, runs: int):
    calc_beds_stat(name, runs, "requesters")
    calc_beds_stat(name, runs, "claimers")


def calc_beds_stat(name: str, runs: int, stat_name: str):
    stats: list[pd.DataFrame] = []
    for i in range(runs):
        csv = pd.read_csv(f"../statistiche/{name}/runs/{i}/stats_beds_{stat_name}.csv", keep_default_na=False,
                          index_col="STRUTTURA")
        stats.append(csv)
    frame = pd.concat((df["MEDIA"].rename(f"RUN {i}").astype(float) for i, df in enumerate(stats)), axis=1)
    frame["MEDIA"], frame["VARIANZA"], frame["STD"] = frame.mean(axis=1), frame.var(axis=1), frame.std(axis=1)
    frame["INTERVALLO CONFIDENZA INFERIORE"] = frame["MEDIA"] - (0.8159 * (sqrt(frame["VARIANZA"] / runs)))
    frame["INTERVALLO CONFIDENZA SUPERIORE"] = frame["MEDIA"] + (0.8159 * (sqrt(frame["VARIANZA"] / runs)))
    frame.to_csv(f"../statistiche/{name}/stats_beds_{stat_name}_mean.csv", float_format="%.15f", encoding="utf-8")

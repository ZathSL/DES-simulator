import os
from os import path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['figure.figsize'] = (50, 20)
matplotlib.style.use('ggplot')
cwd = path.dirname(path.abspath(__file__))


def get_dataset(*columns: str):
    df = pd.read_csv("../../../dataset/Dataset_SDO_Regione_Lombardia.csv", dtype=str)
    df = df[["CODICE MDC", "DESCRIZIONE MDC", *columns]]
    missing = df["CODICE MDC"].isna()
    df.loc[missing, "CODICE MDC"] = df.loc[missing, "DESCRIZIONE MDC"].map({
        "MDC NON APPLICABILE": "NA",
        "PREMDC (DRG SENZA SPECIFICA MDC)": "PR",
    })
    mdcs = df[["CODICE MDC", "DESCRIZIONE MDC"]].value_counts(sort=False).to_frame("count") \
        .reset_index(level="DESCRIZIONE MDC").drop("#").sort_index().reset_index().drop("count", axis=1)
    return df, mdcs


def aggr_data(data: pd.DataFrame):
    data = data.value_counts(sort=False).to_frame("CONTEGGIO")
    data = data.reset_index()
    data = data.groupby(["CODICE STRUTTURA DI RICOVERO"], as_index=False).agg({
        "CODICE STRUTTURA DI RICOVERO": "last",
        "DESCRIZIONE STRUTTURA DI RICOVERO": "last",
        "CONTEGGIO": "sum",
    })
    data = data.set_index("CODICE STRUTTURA DI RICOVERO").sort_index()
    data["FREQUENZA"] = data["CONTEGGIO"] / data["CONTEGGIO"].sum()
    data.to_csv(path.join(cwd, "StruttureDistribution.csv"), float_format="%.15f", encoding="utf-8")


def plot_data(data: pd.DataFrame, mdc: str, descrizione_mdc: str):
    data = data.value_counts(sort=False).to_frame("CONTEGGIO")
    data = data.reset_index()
    data = data.groupby(["CODICE STRUTTURA DI RICOVERO"], as_index=False).agg({
        "CODICE STRUTTURA DI RICOVERO": "last",
        "DESCRIZIONE STRUTTURA DI RICOVERO": "last",
        "CONTEGGIO": "sum",
    })
    data = data.set_index("CODICE STRUTTURA DI RICOVERO").sort_index()
    freq = data["FREQUENZA"] = data["CONTEGGIO"] / data["CONTEGGIO"].sum()

    os.makedirs(f"MDC_{mdc}", exist_ok=True)
    # Display
    fig, ax = plt.subplots(1, 1)
    freq.plot(kind='bar', ax=ax)
    ax.set_title(f"Distribuzione tra le strutture dell\'MDC {mdc} ({descrizione_mdc})")
    ax.set_xlabel("CODICE STRUTTURA DI RICOVERO")
    ax.set_ylabel("Frequenza")
    plt.savefig(path.join(cwd, f"MDC_{mdc}", "StruttureDistribution.jpg"))

    # Display2
    fig, ax = plt.subplots(1, 1)
    ax.set_yscale('log')
    freq.plot(kind='bar', ax=ax)
    ax.set_title(f"Distribuzione tra le strutture dell\'MDC {mdc} ({descrizione_mdc})")
    ax.set_xlabel("CODICE STRUTTURA DI RICOVERO")
    ax.set_ylabel("Frequenza")
    plt.savefig(path.join(cwd, f"MDC_{mdc}", "StruttureDistributionLOG.jpg"))

    # Export CSV
    data.to_csv(path.join(cwd, f"MDC_{mdc}", "StruttureDistribution.csv"), float_format="%.15f", encoding="utf-8")


def main():
    df, mdcs = get_dataset("CODICE STRUTTURA DI RICOVERO", "DESCRIZIONE STRUTTURA DI RICOVERO")
    aggr_data(df.drop(["CODICE MDC", "DESCRIZIONE MDC"], axis=1))
    for i, mdc in mdcs.iterrows():
        codice, descrizione = mdc["CODICE MDC"], mdc["DESCRIZIONE MDC"]
        print(i + 1, codice, descrizione)
        df_mdc = df[df["CODICE MDC"] == codice].drop(["CODICE MDC", "DESCRIZIONE MDC"], axis=1)
        plot_data(df_mdc, codice, descrizione)


if __name__ == '__main__':
    main()

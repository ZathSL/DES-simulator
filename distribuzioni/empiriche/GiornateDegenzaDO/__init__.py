import os
from os import path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams['figure.figsize'] = (50, 20)
matplotlib.style.use('ggplot')
cwd = path.dirname(path.abspath(__file__))


def get_dataset(*columns: str):
    df = pd.read_csv("../../fitted/Number_Hospitalization_DS/Dataset_SDO_Regione_Lombardia.csv", dtype={
        "CODICE MDC": str,
        "DESCRIZIONE MDC": str,
    })
    df = df[["CODICE MDC", "DESCRIZIONE MDC", *columns]]
    missing = df["CODICE MDC"].isna()
    df.loc[missing, "CODICE MDC"] = df.loc[missing, "DESCRIZIONE MDC"].map({
        "MDC NON APPLICABILE": "NA",
        "PREMDC (DRG SENZA SPECIFICA MDC)": "PR",
    })
    mdcs = df[["CODICE MDC", "DESCRIZIONE MDC"]].value_counts(sort=False).to_frame("count") \
        .reset_index(level="DESCRIZIONE MDC").drop("#").sort_index().reset_index().drop("count", axis=1)
    return df, mdcs


def plot_data(data: pd.DataFrame, mdc: str, descrizione_mdc: str):
    data["GIORNATE PER RICOVERO DO"] = data["GIORNATE DEGENZA DO"] / data["RICOVERI DO"]
    data.drop(["GIORNATE DEGENZA DO", "RICOVERI DO"], axis=1, inplace=True)
    bins = int(data["GIORNATE PER RICOVERO DO"].max())
    export = np.histogram(data["GIORNATE PER RICOVERO DO"], bins=bins, density=True, range=(0, bins))
    export = pd.DataFrame(export[0], columns=["FREQUENZA"])
    export.index.name = "GIORNATE PER RICOVERO DO"

    os.makedirs(f"MDC_{mdc}", exist_ok=True)
    # Display
    fig, ax = plt.subplots(1, 1)
    data.plot(kind="hist", bins=bins, ax=ax)
    ax.set_title(f"Distribuzione delle giornate di degenza per i ricoveri DO dell'MDC {mdc} ({descrizione_mdc})")
    ax.set_xlabel("GIORNATE PER RICOVERO DO")
    ax.set_ylabel("Conteggio")
    plt.savefig(path.join(cwd, f"MDC_{mdc}", f"GiornateDegenzaDO-{mdc}.jpg"))

    # Display LOG
    fig, ax = plt.subplots(1, 1)
    ax.set_yscale('log')
    data.plot(kind="hist", bins=bins, ax=ax)
    ax.set_title(f"Distribuzione delle giornate di degenza per i ricoveri DO dell'MDC {mdc} ({descrizione_mdc})")
    ax.set_xlabel("GIORNATE PER RICOVERO DO")
    ax.set_ylabel("Conteggio")
    plt.savefig(path.join(cwd, f"MDC_{mdc}", f"GiornateDegenzaDO-{mdc}-LOG.jpg"))

    # Display LOG LOG
    fig, ax = plt.subplots(1, 1)
    ax.set_yscale('log')
    ax.set_xscale('log')
    data.plot(kind="hist", bins=bins, ax=ax)
    ax.set_title(f"Distribuzione delle giornate di degenza per i ricoveri DO dell'MDC {mdc} ({descrizione_mdc})")
    ax.set_xlabel("GIORNATE PER RICOVERO DO")
    ax.set_ylabel("Conteggio")
    plt.savefig(path.join(cwd, f"MDC_{mdc}", f"GiornateDegenzaDO-{mdc}-LOGLOG.jpg"))

    # Export CSV
    export.to_csv(path.join(cwd, f"MDC_{mdc}", f"GiornateDegenzaDO-{mdc}.csv"), float_format="%.15f", encoding="utf-8")


def main():
    df, mdcs = get_dataset("GIORNATE DEGENZA DO", "RICOVERI DO")
    for i, mdc in mdcs.iterrows():
        codice, descrizione = mdc["CODICE MDC"], mdc["DESCRIZIONE MDC"]
        print(i + 1, codice, descrizione)
        df_mdc = df[df["CODICE MDC"] == codice].drop(["CODICE MDC", "DESCRIZIONE MDC"], axis=1)
        plot_data(df_mdc, codice, descrizione)


if __name__ == '__main__':
    main()

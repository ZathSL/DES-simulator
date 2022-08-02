import os
from os import path

import pandas as pd

cwd = path.dirname(path.abspath(__file__))


def get_dataset(*columns: str):
    df = pd.read_csv("../../../dataset/Dataset_SDO_Regione_Lombardia.csv", dtype={
        "CODICE MDC": str,
        "DESCRIZIONE MDC": str,
        "CODICE STRUTTURA DI RICOVERO": str,
        "DESCRIZIONE STRUTTURA DI RICOVERO": str,
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
    data = data.groupby(["CODICE STRUTTURA DI RICOVERO"], as_index=False).agg({
        "CODICE STRUTTURA DI RICOVERO": "last",
        "DESCRIZIONE STRUTTURA DI RICOVERO": "last",
        "TOTALE RICOVERI": "sum",
        "RICOVERI DO": "sum",
        "RICOVERI DH": "sum",
        "RICOVERI DS": "sum",
    })
    data = data.set_index("CODICE STRUTTURA DI RICOVERO").sort_index()
    data["RICOVERI DO"] /= data["TOTALE RICOVERI"]
    data["RICOVERI DH"] /= data["TOTALE RICOVERI"]
    data["RICOVERI DS"] /= data["TOTALE RICOVERI"]

    os.makedirs(f"MDC_{mdc}", exist_ok=True)
    # Export CSV
    data.to_csv(path.join(cwd, f"MDC_{mdc}", "TipologieAccessiDistribution.csv"), float_format="%.15f",
                encoding="utf-8")


def main():
    df, mdcs = get_dataset("CODICE STRUTTURA DI RICOVERO", "DESCRIZIONE STRUTTURA DI RICOVERO", "RICOVERI DO",
                           "RICOVERI DH", "RICOVERI DS")
    df["TOTALE RICOVERI"] = df["RICOVERI DO"] + df["RICOVERI DH"] + df["RICOVERI DS"]
    for i, mdc in mdcs.iterrows():
        codice, descrizione = mdc["CODICE MDC"], mdc["DESCRIZIONE MDC"]
        print(i + 1, codice, descrizione)
        df_mdc = df[df["CODICE MDC"] == codice].drop(["CODICE MDC", "DESCRIZIONE MDC"], axis=1)
        plot_data(df_mdc, codice, descrizione)


if __name__ == "__main__":
    main()

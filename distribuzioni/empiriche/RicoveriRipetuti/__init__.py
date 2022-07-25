import pandas as pd


def get_dataset(*columns: str):
    df = pd.read_csv("../../../dataset/Dataset_SDO_Regione_Lombardia.csv", dtype={
        "CODICE MDC": str,
        "DESCRIZIONE MDC": str,
    })
    df = df[["CODICE MDC", "DESCRIZIONE MDC", *columns]]
    missing = df["CODICE MDC"].isna()
    df.loc[missing, "CODICE MDC"] = df.loc[missing, "DESCRIZIONE MDC"].map({
        "MDC NON APPLICABILE": "NA",
        "PREMDC (DRG SENZA SPECIFICA MDC)": "PR",
    })
    return df


def plot_data(data: pd.DataFrame):
    data = data.loc[(data["RICOVERI DO"] > 0) & (data["GIORNATE DEGENZA DO"] > 1), :].copy()
    data["TOTALE ACCESSI"] = data["RICOVERI DO"] + data["ACCESSI DH"] + data["ACCESSI DS"]
    data.drop(["GIORNATE DEGENZA DO", "RICOVERI DO", "ACCESSI DH", "ACCESSI DS"], axis=1, inplace=True)
    data = data.groupby(["CODICE MDC"], as_index=False).agg({
        "CODICE MDC": "last",
        "DESCRIZIONE MDC": "last",
        "TOTALE ACCESSI": "sum",
        "RICOVERI RIPETUTI": "sum",
    })
    data = data.set_index("CODICE MDC").drop("#").sort_index()
    data["PROBABILITA RICOVERI RIPETUTI"] = data["RICOVERI RIPETUTI"] / data["TOTALE ACCESSI"]

    # Export CSV
    data.to_csv("RicoveriRipetutiDistribution.csv", float_format="%.15f", encoding="utf-8")


def main():
    df = get_dataset("RICOVERI DO", "ACCESSI DH", "ACCESSI DS", "GIORNATE DEGENZA DO", "RICOVERI RIPETUTI")
    plot_data(df)


if __name__ == '__main__':
    main()

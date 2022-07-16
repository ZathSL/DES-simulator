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
    data["VISITE DH"] = data["ACCESSI DH"] - data["RICOVERI DH"]
    data["VISITE DS"] = data["ACCESSI DS"] - data["RICOVERI DS"]
    data["TOTALE ACCESSI"] = data["RICOVERI DO"] + data["ACCESSI DH"] + data["ACCESSI DS"]
    data.drop(columns=["ACCESSI DH", "ACCESSI DS"], inplace=True)
    data = data.groupby(["CODICE MDC"], as_index=False).agg({
        "CODICE MDC": "last",
        "DESCRIZIONE MDC": "last",
        "RICOVERI DO": "sum",
        "RICOVERI DH": "sum",
        "RICOVERI DS": "sum",
        "VISITE DH": "sum",
        "VISITE DS": "sum",
        "TOTALE ACCESSI": "sum",
    })
    data["RICOVERI DO"] /= data["TOTALE ACCESSI"]
    data["RICOVERI DH"] /= data["TOTALE ACCESSI"]
    data["RICOVERI DS"] /= data["TOTALE ACCESSI"]
    data["VISITE DH"] /= data["TOTALE ACCESSI"]
    data["VISITE DS"] /= data["TOTALE ACCESSI"]
    data = data.set_index("CODICE MDC").drop("#").sort_index()

    # Export CSV
    data.to_csv("TipologieAccessiDistribution.csv", float_format="%.15f", encoding="utf-8")


def main():
    df = get_dataset("RICOVERI DO", "RICOVERI DH", "RICOVERI DS", "ACCESSI DH", "ACCESSI DS")
    plot_data(df)


if __name__ == '__main__':
    main()

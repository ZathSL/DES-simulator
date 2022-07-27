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
    data["TOTALE RICOVERI"] = data["RICOVERI DO"] + data["RICOVERI DH"] + data["RICOVERI DS"]
    data = data.groupby(["CODICE MDC"], as_index=False).agg({
        "CODICE MDC": "last",
        "DESCRIZIONE MDC": "last",
        "RICOVERI DO": "sum",
        "RICOVERI DH": "sum",
        "RICOVERI DS": "sum",
        "TOTALE RICOVERI": "sum",
    })
    data = data.set_index("CODICE MDC").drop("#").sort_index()
    data["RICOVERI DO"] /= data["TOTALE RICOVERI"]
    data["RICOVERI DH"] /= data["TOTALE RICOVERI"]
    data["RICOVERI DS"] /= data["TOTALE RICOVERI"]
    data.drop("TOTALE RICOVERI", axis=1, inplace=True)

    # Export CSV
    data.to_csv("TipologieAccessiDistribution.csv", float_format="%.15f", encoding="utf-8")


def main():
    df = get_dataset("RICOVERI DO", "RICOVERI DH", "RICOVERI DS")
    plot_data(df)


if __name__ == "__main__":
    main()

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
    data = data.groupby(["CODICE MDC"], as_index=False).agg({
        "CODICE MDC": "last",
        "DESCRIZIONE MDC": "last",
        "ACCESSI DH": "sum",
        "ACCESSI DS": "sum",
        "RICOVERI DH": "sum",
        "RICOVERI DS": "sum",
    })
    data = data.set_index("CODICE MDC").drop("#").sort_index()
    data["ACCESSI PER RICOVERO DH"] = data["ACCESSI DH"] / data["RICOVERI DH"]
    data["ACCESSI PER RICOVERO DS"] = data["ACCESSI DS"] / data["RICOVERI DS"]
    data.fillna(0, inplace=True)
    # Export CSV
    data.to_csv("AccessiPerRicoveroDistribution.csv", float_format="%.15f", encoding="utf-8")


def main():
    df = get_dataset("ACCESSI DH", "RICOVERI DH", "ACCESSI DS", "RICOVERI DS")
    plot_data(df)


if __name__ == '__main__':
    main()

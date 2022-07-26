import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['figure.figsize'] = (12, 8)
matplotlib.style.use('ggplot')


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
    data["TOTALE ACCESSI"] = data["RICOVERI DO"] + data["ACCESSI DH"] + data["ACCESSI DS"]
    data.drop(["RICOVERI DO", "ACCESSI DH", "ACCESSI DS"], axis=1, inplace=True)
    data = data.groupby(["CODICE MDC", "DESCRIZIONE MDC", "ANNO"], as_index=False).agg({
        "TOTALE ACCESSI": "sum",
    })
    data = data.groupby(["CODICE MDC", "DESCRIZIONE MDC"], as_index=False).agg({
        "TOTALE ACCESSI": "mean",
    })
    data.set_index("CODICE MDC", inplace=True)
    data = data.drop("#").sort_index()
    data.rename(columns={"TOTALE ACCESSI": "ACCESSI PER ANNO"}, inplace=True)
    data["ACCESSI PER GIORNO"] = data["ACCESSI PER ANNO"] / 365.0
    data["INTERARRIVO IN GIORNI"] = 365.0 / data["ACCESSI PER ANNO"]
    freq = data["FREQUENZA"] = data["ACCESSI PER ANNO"] / (data["ACCESSI PER ANNO"].sum())

    # Display
    fig, ax = plt.subplots(1, 1)
    freq.plot(kind='bar', ax=ax)
    ax.set_title("Distribuzione degli MDC")
    ax.set_xlabel("MDC")
    ax.set_ylabel("Frequenza")
    plt.savefig('MDCDistribution.jpg')

    # Display2
    fig, ax = plt.subplots(1, 1)
    ax.set_yscale('log')
    freq.plot(kind='bar', ax=ax)
    ax.set_title("Distribuzione degli MDC")
    ax.set_xlabel("MDC")
    ax.set_ylabel("Frequenza")
    plt.savefig('MDCDistributionLOG.jpg')

    # Export CSV
    data.to_csv("MDCDistribution.csv", float_format="%.15f", encoding="utf-8")


def main():
    df = get_dataset("ANNO", "RICOVERI DO", "ACCESSI DH", "ACCESSI DS")
    plot_data(df)


if __name__ == '__main__':
    main()

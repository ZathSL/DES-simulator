import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['figure.figsize'] = (12, 8)
matplotlib.style.use('ggplot')


def get_dataset():
    df = pd.read_csv("../../dataset/Dataset_SDO_Regione_Lombardia.csv", dtype=str)
    df = df[["ANNO", "CODICE MDC", "DESCRIZIONE MDC"]]
    missing = df["CODICE MDC"].isna()
    df.loc[missing, "CODICE MDC"] = df.loc[missing, "DESCRIZIONE MDC"].map({
        "MDC NON APPLICABILE": "NA",
        "PREMDC (DRG SENZA SPECIFICA MDC)": "PR",
    })
    return df


def plot_data(data: pd.DataFrame):
    data = data.value_counts(sort=False, dropna=False).to_frame("CONTEGGIO").reset_index()
    data = data.groupby("CODICE MDC", as_index=False).agg({
        "ANNO": "last",
        "CODICE MDC": "last",
        "DESCRIZIONE MDC": "last",
        "CONTEGGIO": "mean",
    })
    data = data.set_index("CODICE MDC").drop(columns="ANNO").drop("#").sort_index()
    data.rename(columns={"CONTEGGIO": "CONTEGGIO PER ANNO"}, inplace=True)
    data["CONTEGGIO PER GIORNO"] = data["CONTEGGIO PER ANNO"] / 365.0
    freq = data["FREQUENZA"] = data["CONTEGGIO PER ANNO"] / data["CONTEGGIO PER ANNO"].sum()

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
    df = get_dataset()
    plot_data(df)


if __name__ == '__main__':
    main()

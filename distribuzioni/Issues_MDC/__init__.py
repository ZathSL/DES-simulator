import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['figure.figsize'] = (12, 8)
matplotlib.style.use('ggplot')


def get_dataset():
    df = pd.read_csv("../../dataset/Dataset_SDO_Regione_Lombardia.csv", dtype=str)
    df = df[["CODICE MDC", "DESCRIZIONE MDC"]]
    missing = df["CODICE MDC"].isna()
    df.loc[missing, "CODICE MDC"] = df.loc[missing, "DESCRIZIONE MDC"].map({
        "MDC NON APPLICABILE": "NA",
        "PREMDC (DRG SENZA SPECIFICA MDC)": "PR",
    })
    return df


def plot_data(data: pd.DataFrame):
    data = data.value_counts(sort=False, dropna=False).to_frame("CONTEGGIO")
    data = data.reset_index(level="DESCRIZIONE MDC").drop("#").sort_index()
    freq = data["FREQUENZA"] = data["CONTEGGIO"] / data["CONTEGGIO"].sum()
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

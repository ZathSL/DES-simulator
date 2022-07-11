import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['figure.figsize'] = (12, 8)
matplotlib.style.use('ggplot')


def get_dataset():
    df = pd.read_csv("../../dataset/Dataset_SDO_Regione_Lombardia.csv", dtype=str)
    df = df[["CODICE MDC", "DESCRIZIONE MDC"]].astype("string").fillna("NA")
    return df


def plot_data(data: pd.DataFrame):
    data = data.value_counts(sort=False).to_frame("count").reset_index(level="DESCRIZIONE MDC").drop(
        "#").sort_index().reset_index()
    data = data.groupby(["DESCRIZIONE MDC"], as_index=False).agg({
        "CODICE MDC": "last",
        "DESCRIZIONE MDC": "last",
        "count": "sum",
    })
    data = data.set_index("CODICE MDC").sort_index()
    data.to_csv("MDCDistribution.csv")
    codes = data["count"]
    # Display
    fig, ax = plt.subplots(1, 1)
    codes.plot(kind='bar', ax=ax)
    ax.set_title('MDC distribution')
    ax.set_xlabel('MDC')
    ax.set_ylabel('Frequency')
    plt.savefig('MDCDistribution.jpg')

    # Display2
    fig, ax = plt.subplots(1, 1)
    ax.set_yscale('log')
    codes.plot(kind='bar', ax=ax)
    ax.set_title('MDC distribution')
    ax.set_xlabel('MDC')
    ax.set_ylabel('Frequency')
    plt.savefig('MDCDistributionLOG.jpg')

    # Export CSV
    data.to_csv("MDCDistribution.csv")


def main():
    df = get_dataset()
    plot_data(df)


if __name__ == '__main__':
    main()

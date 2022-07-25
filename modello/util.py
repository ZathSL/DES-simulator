import pandas as pd
from salabim import Pdf


def get_TipologieAccessi_distributions():
    csv_type = pd.read_csv("../distribuzioni/empiriche/TipologieAccessi/TipologieAccessiDistribution.csv",
                           keep_default_na=False)
    return {
        row["CODICE MDC"]: Pdf(("DO", "DH", "DS"), (row["RICOVERI DO"], row["ACCESSI DH"], row["ACCESSI DS"]))
        for _, row in csv_type.iterrows()
    }


def get_RicoveriRipetuti_distributions():
    csv = pd.read_csv("../distribuzioni/empiriche/RicoveriRipetuti/RicoveriRipetutiDistribution.csv",
                      keep_default_na=False)
    csv.set_index("CODICE MDC", inplace=True)
    return csv["PROBABILITA RICOVERI RIPETUTI"].to_dict()


def get_NumeroAccessi_media():
    csv = pd.read_csv("../distribuzioni/empiriche/TipologieAccessi/TipologieAccessiDistribution2.csv",
                      keep_default_na=False)
    csv.set_index("Codice Mdc", inplace=True)
    return csv["Proporzione accessi"].to_dict()


def get_GiornateDegenzaDO_distributions(codici_mdc):
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/GiornateDegenzaDO/MDC_{mdc}/GiornateDegenzaDO-{mdc}.csv",
                         keep_default_na=False)
        for mdc in codici_mdc
    }
    return {
        mdc: Pdf(csv["GIORNATE PER RICOVERO DO"].to_numpy(), csv["FREQUENZA"].to_numpy())
        for mdc, csv in csvs.items()
    }


def get_Strutture_distributions(codici_mdc):
    strutture = {}
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/Strutture/MDC_{mdc}/StruttureDistribution.csv",
                         keep_default_na=False)
        for mdc in codici_mdc
    }
    for mdc, csv in csvs.items():
        strutture.update({
            row["CODICE STRUTTURA DI RICOVERO"]: row["DESCRIZIONE STRUTTURA DI RICOVERO"]
            for _, row in csv.iterrows()
        })
    distributions = {
        mdc: Pdf(csv["CODICE STRUTTURA DI RICOVERO"].to_numpy(), csv["FREQUENZA"].to_numpy())
        for mdc, csv in csvs.items()
    }
    return distributions, strutture

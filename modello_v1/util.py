import pandas as pd
from salabim import Pdf


def get_TipologieAccessi_distributions():
    csv_type = pd.read_csv("../distribuzioni/empiriche/TipologieAccessi/TipologieAccessiDistribution.csv",
                           keep_default_na=False)
    return {
        row["CODICE MDC"]: Pdf(("DO", "DH", "DS"), (row["RICOVERI DO"], row["ACCESSI DH"], row["ACCESSI DS"]))
        for _, row in csv_type.iterrows()
    }


def get_NumeroAccessi_media():
    dict_from_csv = pd.read_csv("../distribuzioni/empiriche/TipologieAccessi/TipologieAccessiDistribution2.csv", delimiter=";", header=None, index_col=0).to_dict()
    dict_from_csv[8].pop('Codice Mdc', None)
    dict_from_csv[8]['NA'] = dict_from_csv[8]['N']
    dict_from_csv[8].pop('N', None)
    return dict_from_csv[8]


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

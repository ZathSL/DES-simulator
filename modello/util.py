import timeit
from datetime import timedelta
from threading import Thread
from time import sleep

import pandas as pd
from salabim import Pdf


def get_mdc_data() -> tuple[list[str], dict[str, str]]:
    csv_mdc = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False)
    codici_mdc = list(csv_mdc["CODICE MDC"].to_numpy())
    info_mdc = dict(zip(codici_mdc, csv_mdc["DESCRIZIONE MDC"].to_numpy()))
    return codici_mdc, info_mdc


def get_beds_info() -> dict[str, int]:
    info_beds = pd.read_csv("../dataset/Letti_per_struttura_sanitaria_completo.csv", keep_default_na=False)
    info_beds.set_index("CODICE STRUTTURA DI RICOVERO", inplace=True)
    return info_beds["LETTI"].to_dict()


def get_iat_distribution() -> dict[str, float]:
    csv = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv",
                      keep_default_na=False)
    csv.set_index("CODICE MDC", inplace=True)
    return csv["INTERARRIVO IN GIORNI"].astype(float).to_dict()


def get_TipologieAccessi_distributions() -> dict[str, Pdf]:
    csv_type = pd.read_csv("../distribuzioni/empiriche/TipologieAccessi/TipologieAccessiDistribution.csv",
                           keep_default_na=False)
    return {
        row["CODICE MDC"]: Pdf(("DO", "DH", "DS"), (row["RICOVERI DO"], row["RICOVERI DH"], row["RICOVERI DS"]))
        for _, row in csv_type.iterrows()
    }


def get_RicoveriRipetuti_distributions() -> dict[str, float]:
    csv = pd.read_csv("../distribuzioni/empiriche/RicoveriRipetuti/RicoveriRipetutiDistribution.csv",
                      keep_default_na=False)
    csv.set_index("CODICE MDC", inplace=True)
    return csv["PROBABILITA RICOVERI RIPETUTI"].to_dict()


def get_AccessiPerRicovero_distributions() -> tuple[dict[str, float], dict[str, float]]:
    csv = pd.read_csv("../distribuzioni/empiriche/AccessiPerRicovero/AccessiPerRicoveroDistribution.csv",
                      keep_default_na=False)
    csv.set_index("CODICE MDC", inplace=True)
    accessi_dh = csv["ACCESSI PER RICOVERO DH"].to_dict()
    accessi_ds = csv["ACCESSI PER RICOVERO DS"].to_dict()
    return accessi_dh, accessi_ds


def get_GiornateDegenzaDO_distributions(codici_mdc) -> dict[str, Pdf]:
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/GiornateDegenzaDO/MDC_{mdc}/GiornateDegenzaDO-{mdc}.csv",
                         keep_default_na=False)
        for mdc in codici_mdc
    }
    return {
        mdc: Pdf(csv["GIORNATE PER RICOVERO DO"].to_numpy(), csv["FREQUENZA"].to_numpy())
        for mdc, csv in csvs.items()
    }


def get_Strutture_distributions(codici_mdc) -> tuple[dict[str, Pdf], dict[str, str]]:
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


class CodeTimer:
    def __enter__(self):
        self.start = timeit.default_timer()
        self.running = True
        self.thread = Thread(target=self.progress)
        self.thread.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.running = False
        stop = timeit.default_timer()
        print("\rTempo di esecuzione: ", timedelta(seconds=stop - self.start))

    def progress(self):
        while self.running:
            delta = timedelta(seconds=timeit.default_timer() - self.start)
            print("\rTempo di esecuzione: ", str(delta).split(".")[0], end="")
            sleep(1)
            print("\b", end="")

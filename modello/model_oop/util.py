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


def get_hospitalization_type_distributions(codici_mdc: list[str]) -> dict[str, dict[str, Pdf]]:
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/TipologieAccessi/MDC_{mdc}/TipologieAccessiDistribution.csv",
                         keep_default_na=False,
                         dtype={
                             "RICOVERI DO": float,
                             "RICOVERI DH": float,
                             "RICOVERI DS": float,
                             "CODICE STRUTTURA DI RICOVERO": str,
                         })
        for mdc in codici_mdc
    }
    return {
        mdc: {
            row["CODICE STRUTTURA DI RICOVERO"]: Pdf(
                ("DO", "DH", "DS"), (row["RICOVERI DO"], row["RICOVERI DH"], row["RICOVERI DS"])
            )
            for _, row in csv.iterrows()
        }
        for mdc, csv in csvs.items()
    }


def get_repeated_hospitalizations_do_distribution(codici_mdc: list[str]) -> dict[str, dict[str, float]]:
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/RicoveriRipetuti/MDC_{mdc}/RicoveriRipetutiDistribution.csv",
                         keep_default_na=False).set_index("CODICE STRUTTURA DI RICOVERO")
        for mdc in codici_mdc
    }
    return {
        mdc: csv["PROBABILITA RICOVERI RIPETUTI"].to_dict()
        for mdc, csv in csvs.items()
    }


def get_accesses_per_hospitalization_distributions(codici_mdc: list[str]) -> tuple[
    dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/AccessiPerRicovero/MDC_{mdc}/AccessiPerRicoveroDistribution.csv",
                         keep_default_na=False).set_index("CODICE STRUTTURA DI RICOVERO")
        for mdc in codici_mdc
    }
    return {
               mdc: csv["ACCESSI PER RICOVERO DH"].to_dict()
               for mdc, csv in csvs.items()
           }, {
               mdc: csv["ACCESSI PER RICOVERO DS"].to_dict()
               for mdc, csv in csvs.items()
           }


def get_hospitalization_days_do_distributions(codici_mdc: list[str]) -> dict[str, Pdf]:
    csvs = {
        mdc: pd.read_csv(f"../distribuzioni/empiriche/GiornateDegenzaDO/MDC_{mdc}/GiornateDegenzaDO-{mdc}.csv",
                         keep_default_na=False)
        for mdc in codici_mdc
    }
    return {
        mdc: Pdf(csv["GIORNATE PER RICOVERO DO"].to_numpy(), csv["FREQUENZA"].to_numpy())
        for mdc, csv in csvs.items()
    }


def get_structures_distributions(codici_mdc: list[str]) -> tuple[dict[str, Pdf], dict[str, str]]:
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

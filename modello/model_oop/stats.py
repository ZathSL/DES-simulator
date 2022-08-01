import os
from collections import defaultdict
from typing import Callable

import pandas as pd


def calculate_statistics(simulation: "Simulation", directory: str):
    os.makedirs(directory, exist_ok=True)
    # INPUT
    with open(directory + "number_patient_mdc.csv", "wb") as file_number_mdc_csv:
        values = {mdc: simulation.monitor_mdc.value_number_of_entries(mdc) for mdc in simulation.monitor_mdc.values()}
        values = pd.DataFrame.from_dict(values, orient="index", columns=["COUNT"])
        values.index.name = "MDC"
        values["FREQUENCY"] = values["COUNT"] / values["COUNT"].sum()
        values.to_csv(file_number_mdc_csv, float_format="%.15f", encoding="utf-8")

    with open(directory + "histogram_repeat_do.txt", "w") as file_repeat_do:
        for mdc in simulation.iat_mdc:
            file_repeat_do.write("Istogramma numero di ricoveri ripetuti DO per l'MDC " + mdc + ": \n")
            simulation.monitor_repeat_do[mdc].print_histogram(file=file_repeat_do)
            file_repeat_do.write("\n")

    with open(directory + "repeated_recovery_do.csv", "wb") as file_repeated_do_csv:
        dfs = []
        for mdc in simulation.iat_mdc:
            values = {value: simulation.monitor_repeat_do[mdc].value_number_of_entries(value)
                      for value in [True, False]}
            values = pd.DataFrame.from_dict(values, orient="index", columns=["COUNT"])
            values.index.name = "VALORE"
            values.reset_index(inplace=True)
            values["FREQUENCY"] = values["COUNT"] / values["COUNT"].sum()
            values.insert(0, "MDC", mdc)
            values.set_index(["MDC", "VALORE"], inplace=True)
            dfs.append(values)
        df = pd.concat(dfs)
        df.to_csv(file_repeated_do_csv, float_format="%.15f", encoding="utf-8")

    # OUTPUT
    # Numero di pazienti curati in ogni struttura
    with open(directory + "type_patients_treated.csv", "wb") as type_patients_treated:
        data = {key: [value.patients_treated_ds, value.patients_treated_dh, value.patients_treated_do]
                for key, value in simulation.structures.items()}
        df = pd.DataFrame.from_dict(data, orient="index", columns=["RICOVERI DS", "RICOVERI DH", "RICOVERI DO"])
        df.index.name = "STRUTTURA"
        df["TOTALE RICOVERI"] = df["RICOVERI DS"] + df["RICOVERI DH"] + df["RICOVERI DO"]
        df.to_csv(type_patients_treated, float_format="%.15f", encoding="utf-8")

    calc_beds_stats(simulation, directory, "requesters",
                    lambda day_start, period, structure:
                    sum(structure.bed_requesters_counter[day_start:day_start + period]))

    calc_beds_stats(simulation, directory, "claimers",
                    lambda day_start, period, structure:
                    sum(structure.bed_claimers_counter[day_start:day_start + period]))


def calc_beds_stats(simulation: "Simulation", directory: str, stat_name: str,
                    stat_function: Callable[[int, int, "Structure"], float]):
    with open(directory + f"stats_beds_{stat_name}.csv", "wb") as file_stats_beds_iid:
        rows = defaultdict(list)
        period = 2
        day_start = period
        for _ in range(11):
            for structure_id, structure in simulation.structures.items():
                rows[structure_id].append(stat_function(day_start, period, structure))
            day_start += period
        columns = [f"MESE {i}" for i in range(2, 13)]
        df = pd.DataFrame.from_dict(rows, columns=columns, orient="index")
        df.index.name = "STRUTTURA"
        df.fillna(0, inplace=True)
        df["MEDIA"], df["VARIANZA"], df["SQM"] = df.mean(axis=1), df.var(axis=1), df.std(axis=1)
        df.to_csv(file_stats_beds_iid, float_format="%.15f", encoding="utf-8")

import os

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

    with open(directory + "stats_beds.csv", "wb") as file_stats_beds_iid:
        length_requesters_list = ["REQUESTERS"]
        length_claimers_list = ["CLAIMERS"]
        length_stay_requesters_list = ["STAY_REQUESTERS"]
        length_stay_claimers_list = ["STAY_CLAIMERS"]
        day_start = 30
        for _ in range(11):
            sum_requesters = 0
            sum_claimers = 0
            sum_stay_requesters = 0
            sum_stay_claimers = 0
            for key, value in simulation.structures.items():
                sum_requesters += value.beds.requesters().length[day_start:day_start + 30].mean()
                sum_claimers += value.beds.claimers().length[day_start:day_start + 30].mean()
                sum_stay_requesters += value.beds.requesters().length_of_stay[day_start:day_start + 30].mean().real
                sum_stay_claimers += value.beds.claimers().length_of_stay[day_start:day_start + 30].mean().real
            length_requesters_list.append(sum_requesters / len(simulation.structures))
            length_claimers_list.append(sum_claimers / len(simulation.structures))
            length_stay_requesters_list.append(sum_stay_requesters / len(simulation.structures))
            length_stay_claimers_list.append(sum_stay_claimers / len(simulation.structures))
            day_start += 30
        columns = ["VARIABILE CALCOLATA"]
        columns.extend(f"MESE {i}" for i in range(2, 13))
        df = pd.DataFrame([length_requesters_list, length_claimers_list, length_stay_requesters_list,
                           length_stay_claimers_list], columns=columns)
        df.set_index("VARIABILE CALCOLATA", inplace=True)
        df.fillna(0, inplace=True)
        df["MEDIA"], df["VARIANZA"], df["SQM"] = df.mean(axis=1), df.var(axis=1), df.std(axis=1)
        df.to_csv(file_stats_beds_iid, float_format="%.15f", encoding="utf-8")

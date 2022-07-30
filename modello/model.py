import os
from dataclasses import dataclass
from typing import Union, TextIO, Any

import pandas as pd
import salabim as sim
from scipy.stats import bernoulli

from util import get_hospitalization_type_distributions, get_hospitalization_days_do_distributions, \
    get_structures_distributions, get_repeated_hospitalizations_do_distribution, \
    get_accesses_per_hospitalization_distributions, \
    get_iat_distribution, get_mdc_data, get_beds_info

convalescence_avg_time = 7  # giorni

structures: dict[str, "Structure"] = {}

structures_distributions: dict[str, sim.Pdf]
hospitalization_type_distributions: dict[str, sim.Pdf]
hospitalization_days_DO_distributions: dict[str, sim.Pdf]
repeated_hospitalizations_DO_distribution: dict[str, float]
accesses_per_hospitalization_DH_distribution: dict[str, float]
accesses_per_hospitalization_DS_distribution: dict[str, float]

iat_mdc: dict[str, float]
info_structures: dict[str, str]
info_mdc: dict[str, str]
info_beds: dict[str, int]

monitor_mdc: sim.Monitor
monitor_repeat_do: dict[str, sim.Monitor] = {}


class Structure(sim.Component):
    code: str
    name: str
    hospitalization_waiting: sim.Queue
    beds: sim.Resource
    n_beds: int
    patients_treated_dh: int
    patients_treated_ds: int
    patients_treated_do: int

    # noinspection PyMethodOverriding
    def setup(self, code: str, name_s: str, n_beds: int):
        self.hospitalization_waiting = sim.Queue("hospitalization")
        self.beds = sim.Resource("beds", capacity=n_beds)
        self.patients_treated_dh = 0
        self.patients_treated_ds = 0
        self.patients_treated_do = 0
        self.n_beds = n_beds

    def process(self):
        while True:
            while len(self.hospitalization_waiting) <= 0:
                yield self.passivate()
            if len(self.hospitalization_waiting) > 0:
                # patient visit
                patient: Patient = self.hospitalization_waiting.pop()
                if not patient.visited_already:
                    hospitalization_type = hospitalization_type_distributions[patient.mdc].sample()
                    if hospitalization_type == "DS":
                        patient.hospitalization_type = "DS"
                        patient.ds += accesses_per_hospitalization_DS_distribution[patient.mdc]
                    if hospitalization_type == "DH":
                        patient.hospitalization_type = "DH"
                        patient.dh += accesses_per_hospitalization_DH_distribution[patient.mdc]
                    if hospitalization_type == "DO":
                        patient.hospitalization_type = "DO"
                        patient.do = 1
                    patient.visited_already = True
                patient.activate(process="hospitalization")


# patient component
class Patient(sim.Component):
    mdc: str
    mdc_desc: str
    visited_already: bool
    ds: int
    dh: int
    do: int
    days_do: int
    structure: Structure
    hospitalization_type: str

    # noinspection PyMethodOverriding
    def setup(self, mdc: str, mdc_desc: str):
        self.mdc = mdc
        self.visited_already = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.days_do = 0
        self.hospitalization_type = ""
        self.structure = structures[structures_distributions[mdc].sample()]
        monitor_mdc.tally(mdc)  # conto il numero di pazienti per ogni mdc
        self.enter(self.structure.hospitalization_waiting)  # entro nella coda di attesa
        self.structure.activate()

    def hospitalization(self):
        yield self.request(self.structure.beds)
        if self.ds > 0:
            yield self.hold(1)
            self.ds -= 1
        elif self.dh > 0:
            yield self.hold(1)
            self.dh -= 1
        elif self.do > 0:
            # se non ho già generato i giorni di degenza DO, genero il numero di giorni
            if self.days_do == 0:
                self.days_do = hospitalization_days_DO_distributions[self.mdc].sample()
            # finché non ho terminato di scontare tutti i giorni di degenza DO
            while self.days_do > 0:
                self.hold(1)
                self.days_do -= 1
                # se ho ancora giorni di degenza DO da scontare, controllo se devo eseguire dei ricoveri ripetuti
                repeat_result = bernoulli.rvs(size=1, p=repeated_hospitalizations_DO_distribution[self.mdc])
                monitor_repeat_do[self.mdc].tally(repeat_result)
                if self.days_do > 0 and repeat_result == 1:
                    break
            # se ho terminato di scontare tutti i giorni in DO, decremento il numero di ricoveri DO
            if self.days_do <= 0:
                self.do -= 1
        # se ho terminato di scontare tutti i tipi di ricoveri, aggiungo il paziente al numero di pazienti guariti
        if self.ds <= 0 and self.dh <= 0 and self.do <= 0:
            if self.hospitalization_type == "DS":
                self.structure.patients_treated_ds += 1
            elif self.hospitalization_type == "DH":
                self.structure.patients_treated_dh += 1
            elif self.hospitalization_type == "DO":
                self.structure.patients_treated_do += 1
            self.release()
            yield self.cancel()
        else:
            self.release(self.structure.beds)
            # attendo un tempo di convalescenza prima di riaccedere alla struttura
            yield self.hold(sim.Exponential(convalescence_avg_time))
            self.enter(self.structure.hospitalization_waiting)  # entro nella coda di attesa
            yield self.passivate()
        yield self.structure.activate()


def setup():
    global structures_distributions, hospitalization_type_distributions, hospitalization_days_DO_distributions, \
        repeated_hospitalizations_DO_distribution, accesses_per_hospitalization_DH_distribution, \
        accesses_per_hospitalization_DS_distribution, iat_mdc, info_structures, info_mdc, info_beds
    mdc_codes, info_mdc = get_mdc_data()
    info_beds = get_beds_info()
    iat_mdc = get_iat_distribution()
    structures_distributions, info_structures = get_structures_distributions(mdc_codes)
    hospitalization_type_distributions = get_hospitalization_type_distributions()
    hospitalization_days_DO_distributions = get_hospitalization_days_do_distributions(mdc_codes)
    accesses_per_hospitalization_DH_distribution, accesses_per_hospitalization_DS_distribution = \
        get_accesses_per_hospitalization_distributions()
    repeated_hospitalizations_DO_distribution = get_repeated_hospitalizations_do_distribution()


@dataclass
class Mutation:
    type: str
    id: str
    ops: dict[str, Any]


def apply_mutations(mutations: list[Mutation]):
    for mutation in mutations:
        if mutation.type == "structure":
            apply_structure_mutation(mutation.id, mutation.ops)
        elif mutation.type == "parameter":
            apply_parameter_mutation(mutation.id, mutation.ops)
        else:
            raise ValueError("Unknown mutation type: " + mutation.type)


def apply_parameter_mutation(param: str, ops: dict):
    global convalescence_avg_time
    if param == "convalescence_avg_time":
        if "value" in ops:
            convalescence_avg_time = ops["value"]
        else:
            raise ValueError("Missing value in parameter mutation")
    else:
        raise ValueError("Unknown parameter: " + param)


# noinspection PyProtectedMember
def apply_structure_mutation(key: str, ops: dict):
    keys = info_structures.keys() if key == "*" else [key]  # se key è "*" considero tutte le strutture
    for key in keys:
        for op, value in ops.items():
            if op == "delete":  # elimino la struttura
                if key in info_structures:
                    del info_structures[key]
                    del info_beds[key]
                    for _, pdf in structures_distributions.items():
                        try:
                            index = pdf._x.index(key)
                            pdf._x.pop(index)
                            pdf._cum.pop(index)
                        except ValueError:
                            pass
                else:
                    raise ValueError(key + " not found")
            elif op == "beds":  # modifico il numero di letti
                if key in info_structures:
                    if isinstance(value, int):
                        info_beds[key] = value  # imposto il numero di letti
                    elif isinstance(value, float):
                        info_beds[key] = round(value * info_beds[key])  # vario il numero di letti di una percentuale
                    else:
                        raise ValueError("Invalid value for beds")
                else:
                    raise ValueError(key + " not found")
            else:
                raise ValueError("Invalid mutation operation")


def simulation(
        trace: Union[bool, TextIO],
        sim_time_days: int,
        animate: bool,
        speed: float,
        mutations: list[Mutation],
        statistics_dir: str,
        random_seed: Union[int, float, str],
):
    global monitor_mdc
    setup()
    apply_mutations(mutations)

    env = sim.Environment(trace=trace, time_unit="days", random_seed=random_seed)
    env.animate(animate)
    env.speed(speed)
    env.modelname("Simulatore SSR lombardo")

    monitor_mdc = sim.Monitor(name='mdc')
    for mdc, _ in iat_mdc.items():
        monitor_repeat_do[mdc] = sim.Monitor(name='repeat do ' + mdc)

    for code, name in info_structures.items():  # creo le strutture
        if code:
            n_beds = info_beds[code]
            structure = Structure(name="structure." + code, code=code, name_s=name, n_beds=n_beds)
            structures[code] = structure

    for mdc, iat in iat_mdc.items():  # creo i generatori di pazienti
        sim.ComponentGenerator(Patient, generator_name="Patient.generator.mdc-" + mdc, iat=sim.Exponential(iat),
                               mdc=mdc, mdc_desc=info_mdc[mdc])

    env.run(till=sim_time_days)
    calculate_statistics(statistics_dir)


def calculate_statistics(directory: str):
    os.makedirs(directory, exist_ok=True)
    # INPUT
    # Numero di pazienti in entrata per ogni struttura
    with open(directory + "number_patients.txt", "w") as file_number_patient:
        for key, value in structures.items():
            file_number_patient.write("Structure " + key + "\n")
            value.hospitalization_waiting.print_histograms(file=file_number_patient)  # statistiche delle entrate
            file_number_patient.write("\n")

    with open(directory + "number_patient_mdc.csv", "wb") as file_number_mdc_csv:
        values = {mdc: monitor_mdc.value_number_of_entries(mdc) for mdc in monitor_mdc.values()}
        values = pd.DataFrame.from_dict(values, orient="index", columns=["COUNT"])
        values.index.name = "MDC"
        values["FREQUENCY"] = values["COUNT"] / values["COUNT"].sum()
        values.to_csv(file_number_mdc_csv, float_format="%.15f", encoding="utf-8")

    # Numero di ricoveri ripetuti per ogni mdc
    with open(directory + "stats_hospitalization_mdc.txt", "w") as file_stats_hospitalization:
        for mdc in iat_mdc:
            file_stats_hospitalization.write("STATISTICS MDC " + mdc + "\n")
            monitor_repeat_do[mdc].print_histograms(values=True, file=file_stats_hospitalization)
            file_stats_hospitalization.write("\n")

    # OUTPUT
    # Statistiche sui letti in ogni struttura
    with open(directory + "stats_beds.txt", "w") as file_stats_beds:
        for key, value in structures.items():
            file_stats_beds.write("STATISTICS STRUCTURE " + key + "\n")
            value.beds.print_histograms(file=file_stats_beds)

    # Numero di pazienti curati in ogni struttura
    beds_tot = 0
    patient_treated_mean = 0
    length_requesters = 0
    length_claimers = 0
    available_quantity = 0
    claimed_quantity = 0
    occupancy = 0
    with open(directory + "number_patients_treated.txt", "w") as file_number_patients_treated:
        for key, value in structures.items():
            beds_tot += value.n_beds
            patient_treated_mean += (value.patients_treated_ds + value.patients_treated_dh +
                                     value.patients_treated_do) * value.n_beds
            length_requesters += value.beds.requesters().length.mean()
            length_claimers += value.beds.claimers().length.mean()
            available_quantity += value.beds.available_quantity.mean()
            claimed_quantity += value.beds.claimed_quantity.mean()
            occupancy += value.beds.occupancy.mean()
        file_number_patients_treated.write("Media ponderata pazienti guariti: " + str(patient_treated_mean / beds_tot))

    with open(directory + "type_patients_treated.csv", "wb") as type_patients_treated:
        data = {key: [value.patients_treated_ds, value.patients_treated_dh, value.patients_treated_do]
                for key, value in structures.items()}
        df = pd.DataFrame.from_dict(data, orient="index", columns=["RICOVERI DS", "RICOVERI DH", "RICOVERI DO"])
        df.index.name = "STRUTTURA"
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
            for key, value in structures.items():
                sum_requesters += value.beds.requesters().length[day_start:day_start + 30].mean()
                sum_claimers += value.beds.claimers().length[day_start:day_start + 30].mean()
                sum_stay_requesters += value.beds.requesters().length_of_stay[day_start:day_start + 30].mean().real
                sum_stay_claimers += value.beds.claimers().length_of_stay[day_start:day_start + 30].mean().real
            length_requesters_list.append(sum_requesters / len(structures))
            length_claimers_list.append(sum_claimers / len(structures))
            length_stay_requesters_list.append(sum_stay_requesters / len(structures))
            length_stay_claimers_list.append(sum_stay_claimers / len(structures))
            day_start += 30
        columns = ["VARIABILE CALCOLATA"]
        columns.extend(f"MESE {i}" for i in range(2, 13))
        df = pd.DataFrame([length_requesters_list, length_claimers_list, length_stay_requesters_list,
                           length_stay_claimers_list], columns=columns)
        df.set_index("VARIABILE CALCOLATA", inplace=True)
        df.fillna(0, inplace=True)
        df["MEDIA"], df["VARIANZA"] = df.mean(axis=1), df.var(axis=1)
        df.to_csv(file_stats_beds_iid, float_format="%.15f", encoding="utf-8")

    with open(directory + "stats_beds_mean.txt", "w") as file_stats_beds_mean:
        file_stats_beds_mean.write(
            "Length of requesters of beds (sum of mean): " + str((length_requesters / len(structures))) + "\n")
        # file_stats_beds_mean.write("Length of stay in requesters of beds (mean): " + str(length_stay_requesters / beds_tot) + "\n")
        file_stats_beds_mean.write(
            "Length of claimers of beds (sum of mean): " + str(length_claimers / len(structures)) + "\n")
        # file_stats_beds_mean.write("Length of stay in claimers of beds (mean): " + str(length_stay_claimers / beds_tot) + "\n")
        file_stats_beds_mean.write(
            "Length of available quantity of beds (sum of mean): " + str(available_quantity / len(structures)) + "\n")
        file_stats_beds_mean.write(
            "Length of claimed quantity of beds (sum of mean): " + str(claimed_quantity / len(structures)) + "\n")
        file_stats_beds_mean.write(
            "Length of occupancy of beds (sum of mean): " + str(occupancy / len(structures)) + "\n")

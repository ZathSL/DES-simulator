import os
from dataclasses import dataclass
from typing import Union, TextIO, Any

import pandas as pd
import salabim as sim
from scipy.stats import bernoulli

from util import get_TipologieAccessi_distributions, get_GiornateDegenzaDO_distributions, \
    get_Strutture_distributions, get_RicoveriRipetuti_distributions, get_AccessiPerRicovero_distributions, \
    get_iat_distribution, get_mdc_data, get_beds_info

convalescence_avg_time = 7  # giorni

structures: dict[str, "Structure"] = {}

Structures_distributions: dict[str, sim.Pdf]
TypeAccess_distributions: dict[str, sim.Pdf]
DayHospitalizationDO_distributions: dict[str, sim.Pdf]
AccessiPerRicoveroDH_distribution: dict[str, float]
AccessiPerRicoveroDS_distribution: dict[str, float]
RepeatHospitalization_distributions: dict[str, float]

iat_mdc: dict[str, float]
info_structures: dict[str, str]
info_mdc: dict[str, str]
info_beds: dict[str, int]

monitor_mdc: sim.Monitor
monitor_recovery: dict[str, sim.Monitor] = {}
monitor_days_do: dict[str, sim.Monitor] = {}
monitor_repeat_do: dict[str, sim.Monitor] = {}
monitor_beds: dict[str, sim.Monitor] = {}


class Structure(sim.Component):
    code: str
    name: str
    hospitalization_waiting: sim.Queue
    beds: sim.Resource
    n_beds: int
    patients_treated: int

    # noinspection PyMethodOverriding
    def setup(self, code: str, name_s: str, n_beds: int):
        self.hospitalization_waiting = sim.Queue("recovery")
        self.beds = sim.Resource('beds', capacity=n_beds)
        self.patients_treated = 0
        self.n_beds = n_beds

    def process(self):
        while True:
            while len(self.hospitalization_waiting) <= 0:
                yield self.passivate()
            if len(self.hospitalization_waiting) > 0:
                # patient visit
                patient: Patient = self.hospitalization_waiting.pop()
                if not patient.visited_already:
                    type_recovery = TypeAccess_distributions[patient.mdc].sample()
                    monitor_recovery[patient.mdc].tally(type_recovery)
                    if type_recovery == "DS":
                        patient.ds += AccessiPerRicoveroDS_distribution[patient.mdc]
                    if type_recovery == "DH":
                        patient.dh += AccessiPerRicoveroDH_distribution[patient.mdc]
                    if type_recovery == "DO":
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

    # noinspection PyMethodOverriding
    def setup(self, mdc: str, mdc_desc: str):
        self.mdc = mdc
        self.visited_already = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.days_do = 0
        self.structure = structures[Structures_distributions[mdc].sample()]
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
                self.days_do = DayHospitalizationDO_distributions[self.mdc].sample()
                monitor_days_do[self.mdc].tally(self.days_do)
            # finché non ho terminato di scontare tutti i giorni di degenza DO
            while self.days_do > 0:
                self.hold(1)
                self.days_do -= 1
                # se ho ancora giorni di degenza DO da scontare, controllo se devo eseguire dei ricoveri ripetuti
                repeat_result = bernoulli.rvs(size=1, p=RepeatHospitalization_distributions[self.mdc])
                monitor_repeat_do[self.mdc].tally(repeat_result)
                if self.days_do > 0 and repeat_result == 1:
                    break
            # se ho terminato di scontare tutti i giorni in DO, decremento il numero di ricoveri DO
            if self.days_do <= 0:
                self.do -= 1
        # se ho terminato di scontare tutti i tipi di ricoveri, aggiungo il paziente al numero di pazienti guariti
        if self.ds <= 0 and self.dh <= 0 and self.do <= 0:
            self.structure.patients_treated += 1
            self.release()
        else:
            self.release(self.structure.beds)
            # attendo un tempo di convalescenza prima di riaccedere alla struttura
            yield self.hold(sim.Exponential(convalescence_avg_time))
            self.enter(self.structure.hospitalization_waiting)  # entro nella coda di attesa
            yield self.passivate()
        yield self.structure.activate()


def setup():
    global Structures_distributions, TypeAccess_distributions, DayHospitalizationDO_distributions, \
        RepeatHospitalization_distributions, AccessiPerRicoveroDH_distribution, AccessiPerRicoveroDS_distribution, \
        iat_mdc, info_structures, info_mdc, info_beds
    codici_mdc, info_mdc = get_mdc_data()
    info_beds = get_beds_info()
    iat_mdc = get_iat_distribution()
    Structures_distributions, info_structures = get_Strutture_distributions(codici_mdc)
    TypeAccess_distributions = get_TipologieAccessi_distributions()
    DayHospitalizationDO_distributions = get_GiornateDegenzaDO_distributions(codici_mdc)
    AccessiPerRicoveroDH_distribution, AccessiPerRicoveroDS_distribution = get_AccessiPerRicovero_distributions()
    RepeatHospitalization_distributions = get_RicoveriRipetuti_distributions()


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
                    for _, pdf in Structures_distributions.items():
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
        random_seed: Union[int, float, str] = None,
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
        monitor_recovery[mdc] = sim.Monitor(name='recovery ' + mdc)
        monitor_days_do[mdc] = sim.Monitor(name='days do ' + mdc)
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
    with open(directory + "number_patients.txt", "a") as file_number_patient:
        for key, value in structures.items():
            file_number_patient.write("Structure " + key + "\n")
            value.hospitalization_waiting.print_histograms(file=file_number_patient)  # statistiche delle entrate
            file_number_patient.write("\n")

    # Numero di pazienti per ogni mdc
    with open(directory + "number_patient_mdc.txt", "w") as file_number_mdc:
        monitor_mdc.print_histograms(values=True, file=file_number_mdc)

    with open(directory + "number_patient_mdc.csv", "wb") as file_number_mdc_csv:
        values = {mdc: monitor_mdc.value_number_of_entries(mdc) for mdc in monitor_mdc.values()}
        values = pd.DataFrame.from_dict(values, orient="index", columns=["COUNT"])
        values.index.name = "MDC"
        values["FREQUENCY"] = values["COUNT"] / values["COUNT"].sum()
        values.to_csv(file_number_mdc_csv)

    # Numero di ricoveri DS/DH/DO, numero di giorni ricovero DO, numero di ricoveri ripetuti per ogni mdc
    with open(directory + "stats_recovery_mdc.txt", "a") as file_stats_recovery:
        for mdc in iat_mdc:
            file_stats_recovery.write("STATISTICS MDC " + mdc + "\n")
            monitor_recovery[mdc].print_histograms(values=True, file=file_stats_recovery)
            file_stats_recovery.write("\n")
            monitor_days_do[mdc].print_histograms(values=True, file=file_stats_recovery)
            file_stats_recovery.write("\n")
            monitor_repeat_do[mdc].print_histograms(values=True, file=file_stats_recovery)
            file_stats_recovery.write("\n")

    # OUTPUT
    # Statistiche sui letti in ogni struttura
    with open(directory + "stats_beds.txt", "a") as file_stats_beds:
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
    with open(directory + "number_patients_treated.txt", "a") as file_number_patients_treated:
        for key, value in structures.items():
            beds_tot += value.n_beds
            patient_treated_mean += value.patients_treated * value.n_beds
            file_number_patients_treated.write(
                'Numero di pazienti guariti nella struttura ' + key + ': ' + str(value.patients_treated) + "\n")
            length_requesters += value.beds.requesters().length.mean()
            length_claimers += value.beds.claimers().length.mean()
            available_quantity += value.beds.available_quantity.mean()
            claimed_quantity += value.beds.claimed_quantity.mean()
            occupancy += value.beds.occupancy.mean()
        file_number_patients_treated.write("Media ponderata pazienti guariti: " + str(patient_treated_mean / beds_tot))

    with open(directory + "stats_beds_mean.txt", "a") as file_stats_beds_mean:
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

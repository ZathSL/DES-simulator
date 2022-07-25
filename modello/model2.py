import math
import timeit
from datetime import timedelta
from typing import Union, TextIO

import pandas as pd
import salabim as sim

from util import get_TipologieAccessi_distributions, get_GiornateDegenzaDO_distributions, \
    get_Strutture_distributions, get_NumeroAccessi_media

Structures_distributions: dict[str, sim.Pdf]
TypeAccess_distributions: dict[str, sim.Pdf]
DayHospitalizationDO_distributions: dict[str, sim.Pdf]
NumberAccess_mean: dict[str, int]

monitor_mdc: sim.Monitor
monitor_recovery: dict[str, sim.Monitor] = {}
monitor_days_do: dict[str, sim.Monitor] = {}
monitor_treated_patients: sim.Monitor


class Structure(sim.Component):
    code: str
    name: str
    hospitalization_waiting: sim.Queue
    beds: sim.Resource
    n_beds: int
    patient_treated: list
    patient: any

    # noinspection PyMethodOverriding
    def setup(self, code: str, name_s: str, n_beds: int):
        self.hospitalization_waiting = sim.Queue("recovery")
        self.beds = sim.Resource('beds', capacity=n_beds)
        self.patient_treated = []

    def process(self):
        while True:
            while len(self.hospitalization_waiting) == 0:
                yield self.passivate()
            if len(self.hospitalization_waiting) > 0:
                # patient visit
                patient = self.hospitalization_waiting.pop()
                if not patient.visited_already:
                    do = 0
                    ds = 0
                    dh = 0
                    for _ in range(int(NumberAccess_mean[patient.mdc])):
                        type_recovery = TypeAccess_distributions[patient.mdc].sample()
                        monitor_recovery[patient.mdc].tally(type_recovery)  # salvo il numero di ricoveri di ogni tipo
                        if type_recovery == "DS":
                            ds += 1
                        elif type_recovery == "DH":
                            dh += 1
                        elif type_recovery == "DO":
                            do += 1
                        if ds > 0 and dh > 0:
                            if sim.IntUniform(0, 1) == 0:
                                dh = 0
                            else:
                                ds = 0
                    tot_days_do = DayHospitalizationDO_distributions[patient.mdc].sample()
                    monitor_days_do[patient.mdc].tally(tot_days_do)
                    days_do = 0
                    if do != 0:
                        days_do = math.ceil(tot_days_do / do) + 1
                    patient.ds = ds
                    patient.dh = dh
                    patient.do = do
                    patient.days_do = days_do
                    patient.visited_already = True
                patient.activate(process="hospitalization")


structures: dict[str, Structure] = {}


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
        self.structure.hospitalization_waiting.append(self)
        self.structure.activate()

    def hospitalization(self):
        yield self.request(self.structure.beds)
        while self.ds > 0 or self.dh > 0 or self.do > 0:
            if self.ds > 0:
                self.ds -= 1
                yield self.hold(1)
            elif self.dh > 0:
                self.dh -= 1
                yield self.hold(1)
            elif self.do > 0:
                self.do -= 1
                yield self.hold(self.days_do)
            if True:  # TODO: se deve essere fatto un ricovero ripetuto restituisce true e viene messo in coda
                self.release(self.structure.beds)
                self.structure.hospitalization_waiting.append(self)
                break
        if self.ds == 0 and self.dh == 0 and self.do == 0:
            self.structure.patient_treated.append(self)


def setup():
    global Structures_distributions, TypeAccess_distributions, DayHospitalizationDO_distributions, NumberAccess_mean
    csv_mdc = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False)
    info_beds = pd.read_csv("../dataset/Letti_per_struttura_sanitaria_completo.csv", keep_default_na=False)
    info_beds.set_index("CODICE STRUTTURA DI RICOVERO", inplace=True)
    codici_mdc = csv_mdc["CODICE MDC"].to_numpy()
    info_mdc = dict(zip(codici_mdc, csv_mdc["DESCRIZIONE MDC"].to_numpy()))
    iat_mdc = dict(zip(codici_mdc, csv_mdc["INTERARRIVO IN GIORNI"].astype(float).to_numpy()))
    Structures_distributions, info_structures = get_Strutture_distributions(codici_mdc)
    TypeAccess_distributions = get_TipologieAccessi_distributions()
    DayHospitalizationDO_distributions = get_GiornateDegenzaDO_distributions(codici_mdc)
    NumberAccess_mean = get_NumeroAccessi_media()
    return iat_mdc, info_structures, info_mdc, info_beds


def simulation(trace: Union[bool, TextIO], sim_time_days: int, animate: bool, speed: float):
    global structures, monitor_mdc, monitor_recovery, monitor_days_do
    iat_mdc, info_structures, info_mdc, info_beds = setup()
    env = sim.Environment(trace=trace, time_unit="days")

    monitor_mdc = sim.Monitor(name='mdc')
    for mdc in iat_mdc:
        monitor_recovery[mdc] = sim.Monitor(name='recovery ' + mdc)
        monitor_days_do[mdc] = sim.Monitor(name='days do ' + mdc)

    env.animate(animate)
    env.speed(speed)
    env.modelname("Simulatore SSR lombardo - Modello V2")

    for code, name in info_structures.items():
        if code:
            n_beds = info_beds.at[code, "LETTI"]
            structure = Structure(name="structure." + code, code=code, name_s=name, n_beds=n_beds)
            structures[code] = structure

    for mdc, iat in iat_mdc.items():
        sim.ComponentGenerator(Patient, generator_name="Patient.generator.mdc-" + mdc, iat=iat, mdc=mdc,
                               mdc_desc=info_mdc[mdc])
    env.run(till=sim_time_days)
    calculate_statistics(iat_mdc=iat_mdc)


def calculate_statistics(iat_mdc: dict):
    # INPUT
    # Numero di pazienti in entrata per ogni struttura
    for key, value in structures.items():
        value.hospitalization_waiting.print_statistics() # statistiche delle entrate

    # Numero di pazienti per ogni mdc
    monitor_mdc.print_histograms(values=True)

    # Numero di ricoveri DS/DH/DO e numero di giorni ricovero DO per ogni mdc
    for mdc in iat_mdc:
        monitor_recovery[mdc].print_histograms(values=True)
        monitor_days_do[mdc].print_histograms(values=True)

    # OUTPUT
    # Statistiche sui letti in ogni struttura
    for key, value in structures.items():
        print(key)
        value.beds.print_statistics()
    # Numero di pazienti curati in ogni struttura e
    # statistiche sulla permanenza media dei pazienti ricoverati in ogni struttura
    for key, value in structures.items():
        print('Numero di pazienti guariti nella struttura ' + key + ': ' + str(len(value.patient_treated)))


def main():
    start = timeit.default_timer()
    logfile = False  # open("sim_trace.log", "w")
    sim_time_days = 365
    animate = False
    speed = 10
    simulation(trace=logfile, sim_time_days=sim_time_days, animate=animate, speed=speed)
    stop = timeit.default_timer()
    print("Tempo di esecuzione: ", timedelta(seconds=stop - start))


if __name__ == "__main__":
    main()

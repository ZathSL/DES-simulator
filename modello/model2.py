import timeit
from datetime import timedelta
from typing import Union, TextIO
from scipy.stats import bernoulli
import pandas as pd
import salabim as sim

from util import get_TipologieAccessi_distributions, get_GiornateDegenzaDO_distributions, \
    get_Strutture_distributions, get_NumeroAccessi_media, get_RicoveriRipetuti_distributions

Structures_distributions: dict[str, sim.Pdf]
TypeAccess_distributions: dict[str, sim.Pdf]
DayHospitalizationDO_distributions: dict[str, sim.Pdf]
NumberAccess_mean: dict[str, int]
RepeatHospitalization_distributions: dict[str, sim.Pdf]

monitor_mdc: sim.Monitor
monitor_recovery: dict[str, sim.Monitor] = {}
monitor_days_do: dict[str, sim.Monitor] = {}
monitor_repeat_do: dict[str, sim.Monitor] = {}

class Structure(sim.Component):
    code: str
    name: str
    hospitalization_waiting: sim.Queue
    under_treatment: sim.Queue
    beds: sim.Resource
    n_beds: int
    patient_treated: list
    patient_released: list

    # noinspection PyMethodOverriding
    def setup(self, code: str, name_s: str, n_beds: int):
        self.hospitalization_waiting = sim.Queue("recovery")
        self.beds = sim.Resource('beds', capacity=n_beds)
        self.patient_treated = []
        self.patient_released = []
        self.under_treatment = sim.Queue("undertreatment")

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
                                dh += ds
                            else:
                                ds += dh
                    patient.ds = ds
                    patient.dh = dh
                    patient.do = do
                    patient.visited_already = True
                self.under_treatment.append(patient)
                patient.activate(process="hospitalization")


structures: dict[str, Structure] = {}


def select_type_recovery(ds, dh, do, mdc):
    while True:
        type_recovery = TypeAccess_distributions[mdc].sample()
        if type_recovery == "DH" and dh > 0:
            return type_recovery
        if type_recovery == "DS" and ds > 0:
            return type_recovery
        if type_recovery == "DO" and do > 0:
            return type_recovery


# patient component
class Patient(sim.Component):
    mdc: str
    mdc_desc: str
    visited_already: bool
    ds: int
    dh: int
    do: int
    days_do: int
    residual_days_do: int
    structure: Structure

    # noinspection PyMethodOverriding
    def setup(self, mdc: str, mdc_desc: str):
        self.mdc = mdc
        self.visited_already = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.days_do = 0
        self.residual_days_do = 0
        self.structure = structures[Structures_distributions[mdc].sample()]
        monitor_mdc.tally(mdc)  # conto il numero di pazienti per ogni mdc
        self.structure.hospitalization_waiting.append(self)
        self.structure.activate()

    def hospitalization(self):
        yield self.request(self.structure.beds)
        # seleziono il tipo di ricovero da eseguire
        selected_type = select_type_recovery(ds=self.ds, dh=self.dh, do=self.do, mdc=self.mdc)
        # è stato scelto il ricovero DS
        if selected_type == "DS":
            self.ds -= 1
            yield self.hold(1)
        # è stato scelto il ricovero DH
        elif selected_type == "DH":
            self.dh -= 1
            yield self.hold(1)
        # è stato scelto il ricovero DO
        elif selected_type == "DO":
            # se non ho già generato da un precedente ricovero i giorni di degenza DO, genero il numero di giorni
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
            # se ho terminato di scontare tutti i giorni, decremento il numero di ricoveri DO
            if self.days_do <= 0:
                self.do -= 1
        # se ho terminato di scontare tutti i tipi di ricoveri, aggiungo il paziente al numero di pazienti guariti
        if self.ds == 0 and self.dh == 0 and self.do == 0:
            self.structure.patient_treated.append(self)
        else:
            self.structure.patient_released.append(self)
            self.release(self.structure.beds)
            self.structure.under_treatment.remove(self)
            self.structure = structures[Structures_distributions[self.mdc].sample()]
            self.structure.hospitalization_waiting.append(self)
            yield self.passivate()
        yield self.structure.activate()


def setup():
    global Structures_distributions, TypeAccess_distributions, DayHospitalizationDO_distributions,\
        NumberAccess_mean, RepeatHospitalization_distributions
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
    RepeatHospitalization_distributions = get_RicoveriRipetuti_distributions()
    return iat_mdc, info_structures, info_mdc, info_beds


def simulation(trace: Union[bool, TextIO], sim_time_days: int, animate: bool, speed: float):
    global structures, monitor_mdc, monitor_recovery, monitor_days_do, monitor_repeat_do
    iat_mdc, info_structures, info_mdc, info_beds = setup()
    env = sim.Environment(trace=trace, time_unit="days")

    monitor_mdc = sim.Monitor(name='mdc')
    for mdc in iat_mdc:
        monitor_recovery[mdc] = sim.Monitor(name='recovery ' + mdc)
        monitor_days_do[mdc] = sim.Monitor(name='days do ' + mdc)
        monitor_repeat_do[mdc] = sim.Monitor(name='repeat do ' + mdc)

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
    file_number_patient = open("../statistiche/number_patients.txt", "a")
    for key, value in structures.items():
        value.hospitalization_waiting.print_statistics(file=file_number_patient)# statistiche delle entrate
        file_number_patient.write("\n")
    file_number_patient.close()

    # Numero di pazienti per ogni mdc
    file_number_mdc = open("../statistiche/number_patient_mdc.txt", "w")
    monitor_mdc.print_histograms(values=True, file=file_number_mdc)
    file_number_mdc.close()

    # Numero di ricoveri DS/DH/DO, numero di giorni ricovero DO, numero di ricoveri ripetuti per ogni mdc
    file_stats_recovery = open("../statistiche/stats_recovery_mdc.txt", "a")
    for mdc in iat_mdc:
        file_stats_recovery.write("STATISTICS MDC " + mdc + "\n")
        monitor_recovery[mdc].print_histograms(values=True, file=file_stats_recovery)
        file_stats_recovery.write("\n")
        monitor_days_do[mdc].print_histograms(values=True, file=file_stats_recovery)
        file_stats_recovery.write("\n")
        monitor_repeat_do[mdc].print_histograms(values=True, file=file_stats_recovery)
        file_stats_recovery.write("\n")
    file_stats_recovery.close()

    # OUTPUT
    # Statistiche sui letti in ogni struttura
    file_stats_beds = open("../statistiche/stats_beds.txt", "a")
    for key, value in structures.items():
        file_stats_beds.write("STATISTICS STRUCTURE " + key)
        value.beds.print_statistics(file=file_stats_beds)
    file_stats_beds.close()
    # Numero di pazienti curati in ogni struttura e
    # statistiche sulla permanenza media dei pazienti ricoverati in ogni struttura
    file_number_patients_released = open("../statistiche/number_patients_released.txt", "a")
    file_number_patients_treated = open("../statistiche/number_patients_treated.txt", "a")
    file_stats_patients_undertreatment = open("../statistiche/stats_patients_undertreatment", "a")
    for key, value in structures.items():
        file_number_patients_treated.write('Numero di pazienti guariti nella struttura ' + key + ': ' + str(len(value.patient_treated)) + "\n")
        file_number_patients_released.write('Numero di pazienti rilasciati dalla struttura ' + key + ': ' + str(len(value.patient_released)) + "\n")
        value.under_treatment.print_statistics(file=file_stats_patients_undertreatment)
    file_number_patients_released.close()
    file_number_patients_treated.close()
    file_stats_patients_undertreatment.close()


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

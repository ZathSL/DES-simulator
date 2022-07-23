import salabim as sim
import math
from modello_v1.util import get_TipologieAccessi_distributions, get_GiornateDegenzaDO_distributions, get_Strutture_distributions, get_NumeroAccessi_media
import pandas as pd

Structures_distributions: dict[str, sim.Pdf]
TypeAccess_distributions: dict[str, sim.Pdf]
DayHospitalizationDO_distributions: dict[str, sim.Pdf]
NumberAccess_mean: dict[str, int]


class Structure(sim.Component):
    code: str
    name: str
    acceptance_waiting: sim.Queue
    visit_waiting: sim.Queue
    beds: sim.Resource
    n_beds: int
    treated_patients: list

    def setup(self, code: str, name_s: str, n_beds: int):
        self.acceptance_waiting = sim.Queue("acceptance")
        self.visit_waiting = sim.Queue("visit")
        self.beds = sim.Resource('beds', capacity=n_beds)
        # self.resourceDO = Resource('bedsDO', capacity=100)
        self.treated_patients = []

    def entry_patient(self, patient):
        patient.enter(self.acceptance_waiting)

    def visit_patient(self, patient):
        if not patient.visited_already:
            do = 0
            ds = 0
            dh = 0
            for _ in range(int(NumberAccess_mean[patient.mdc])):
                type_recovery = TypeAccess_distributions[patient.mdc].sample()
                if type_recovery == "DS":
                    ds += 1
                elif type_recovery == "DH":
                    dh += 1
                elif type_recovery == "DO":
                    do += 1
                if ds > 0 and dh > 0:
                    if sim.IntUniform(0, 1) == 0:
                        ds += dh
                        dh = 0
                    else:
                        dh += ds
                        ds = 0
            tot_days_do = DayHospitalizationDO_distributions[patient.mdc].sample()
            days_do = math.ceil(tot_days_do / do) + 1
            patient.assign(ds, dh, do, days_do)
        patient.activate(process='hospitalization')

    def process(self):
        while True:
            while len(self.acceptance_waiting) == 0 and len(self.visit_waiting) == 0:
                yield self.passivate()
            if len(self.acceptance_waiting) > 0:
                # accepted patient
                self.visit_waiting.append(self.acceptance_waiting.pop())
            if len(self.visit_waiting) > 0:
                # patient visit
                self.visit_patient(self.visit_waiting.pop())


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

    def setup(self, mdc: str, mdc_desc: str):
        self.mdc = mdc
        self.visited_already = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.days_do = 0
        self.structure = structures[Structures_distributions[mdc].sample()]
        self.structure.entry_patient(self)
        self.structure.activate()

    def assign(self, ds, dh, do, days_do):
        self.visited_already = True
        self.ds = math.ceil(ds)
        self.dh = math.ceil(dh)
        self.do = math.ceil(do)
        self.days_do = math.ceil(days_do)

    def dec(self, dec_ds, dec_dh, dec_do):
        self.ds = self.ds - dec_ds
        self.dh = self.dh - dec_dh
        self.do = self.do - dec_do

    def hospitalization(self):
        if self.ds > 0:
            self.dec(dec_ds=1, dec_dh=0, dec_do=0)
            yield self.request(self.structure.beds)
            self.structure.visit_waiting.append(self)
            yield self.hold(0.001)
            yield self.release(self.structure.beds)
            self.release_patient()
        elif self.dh > 0:
            self.dec(dec_ds=0, dec_dh=1, dec_do=0)
            yield self.request(self.structure.beds)
            self.structure.visit_waiting.append(self)
            yield self.hold(0.001)
            yield self.release(self.structure.beds)
            self.release_patient()
        elif self.do > 0:
            self.dec(dec_ds=0, dec_dh=0, dec_do=1)
            yield self.request(self.structure.beds)
            self.structure.visit_waiting.append(self)
            yield self.hold(self.days_do/1000)
            yield self.release(self.structure.beds)
            self.release_patient()

    def release_patient(self):
        if self.ds == 0 and self.dh == 0 and self.do == 0:
            self.structure.treated_patients.append(self)
            print(self.structure.treated_patients)
            yield self.structure.activate()
            yield self.cancel()


def setup():
    global Structures_distributions, TypeAccess_distributions, DayHospitalizationDO_distributions, NumberAccess_mean
    csv_mdc = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False)
    codici_mdc = csv_mdc["CODICE MDC"].to_numpy()
    info_mdc = dict(zip(codici_mdc, csv_mdc["DESCRIZIONE MDC"].to_numpy()))
    iat_mdc = dict(zip(codici_mdc, csv_mdc["INTERARRIVO IN GIORNI"].astype(float).to_numpy()))
    Structures_distributions, info_structures = get_Strutture_distributions(codici_mdc)
    TypeAccess_distributions = get_TipologieAccessi_distributions()
    DayHospitalizationDO_distributions = get_GiornateDegenzaDO_distributions(codici_mdc)
    NumberAccess_mean = get_NumeroAccessi_media()
    return iat_mdc, info_structures, info_mdc


def main():
    global structures
    env = sim.Environment(trace=True, time_unit='days')

    iat_mdc, info_structures, info_mdc = setup()
    for structure, name in info_structures.items():
        n_beds = 10
        structures[structure] = Structure(name="Structure." + structure, code=structure, name_s=name, n_beds=n_beds)

    for mdc, iat in iat_mdc.items():
        sim.ComponentGenerator(Patient, generator_name="Patient.generator.mdc-" + mdc, iat=iat, mdc=mdc, mdc_desc=info_mdc[mdc])

    sim_time_days = 1
    env.run(till=sim_time_days)


if __name__ == '__main__':
    main()

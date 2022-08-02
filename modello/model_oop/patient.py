import salabim as sim

from .structure import Structure


class Patient(sim.Component):
    simulation: "Simulation"
    mdc: str
    mdc_desc: str
    visited_already: bool
    ds: int
    dh: int
    do: int
    days_do_array: list[int]
    structure: Structure
    hospitalization_type: str

    # noinspection PyMethodOverriding
    def setup(self, simulation: "Simulation", mdc: str, mdc_desc: str):
        self.simulation = simulation
        self.mdc = mdc
        self.visited_already = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.hospitalization_type = ""
        self.structure = self.simulation.structures[self.simulation.structures_distributions[mdc].sample()]
        self.simulation.monitor_mdc.tally(mdc)  # conto il numero di pazienti per ogni mdc
        self.enter(self.structure.hospitalization_waiting)  # entro nella coda di attesa
        self.structure.activate()

    def calc_days_do(self):
        days_do = self.simulation.hospitalization_days_DO_distributions[self.mdc].sample()
        days_counter = 0
        self.days_do_array = []
        while days_do > 0:
            days_do -= 1
            days_counter += 1
            # se ho ancora giorni di degenza DO da scontare, controllo se devo eseguire dei ricoveri ripetuti
            repeat = self.simulation.get_repeated_hospitalizations_do_probability(self.mdc, self.structure.code) == 1
            self.simulation.monitor_repeat_do[self.mdc].tally(repeat)
            if days_do > 0 and repeat:
                self.days_do_array.append(days_counter)
                days_counter = 0
        self.days_do_array.reverse()

    def hospitalization(self):
        self.structure.bed_requesters_counter[round(self.simulation.env.now())] += 1
        yield self.request(self.structure.beds)
        self.structure.bed_claimers_counter[round(self.simulation.env.now())] += 1
        if self.ds > 0:
            yield self.hold(1)
            self.ds -= 1
        elif self.dh > 0:
            yield self.hold(1)
            self.dh -= 1
        elif self.do > 0:
            if len(self.days_do_array) > 0:
                days = self.days_do_array.pop()
                yield self.hold(days)
            # se ho terminato di scontare tutti i giorni in DO, decremento il numero di ricoveri DO
            if len(self.days_do_array) <= 0:
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
            yield self.hold(sim.Exponential(self.simulation.convalescence_avg_time))
            self.enter(self.structure.hospitalization_waiting)  # entro nella coda di attesa
            yield self.passivate()
        yield self.structure.activate()

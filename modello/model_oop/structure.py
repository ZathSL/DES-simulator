import salabim as sim


class Structure(sim.Component):
    simulation: "Simulation"
    code: str
    name: str
    hospitalization_waiting: sim.Queue
    beds: sim.Resource
    n_beds: int
    patients_treated_dh: int
    patients_treated_ds: int
    patients_treated_do: int
    bed_requesters_counter: list[int]
    bed_claimers_counter: list[int]

    # noinspection PyMethodOverriding
    def setup(self, simulation: "Simulation", code: str, name_s: str, n_beds: int):
        self.simulation = simulation
        self.code = code
        self.name = name_s
        self.n_beds = n_beds
        self.hospitalization_waiting = sim.Queue("hospitalization")
        self.beds = sim.Resource("beds", capacity=n_beds)
        self.patients_treated_dh = 0
        self.patients_treated_ds = 0
        self.patients_treated_do = 0
        self.bed_requesters_counter = [0 for _ in range(self.simulation.duration + 1)]
        self.bed_claimers_counter = [0 for _ in range(self.simulation.duration + 1)]

    def process(self):
        while True:
            while len(self.hospitalization_waiting) <= 0:
                yield self.passivate()
            if len(self.hospitalization_waiting) > 0:
                # patient visit
                patient: "Patient" = self.hospitalization_waiting.pop()
                if not patient.visited_already:
                    hospitalization_type = self.simulation. \
                        hospitalization_type_distributions[patient.mdc][self.code].sample()
                    if hospitalization_type == "DS":
                        patient.hospitalization_type = "DS"
                        patient.ds += self.simulation.accesses_per_hospitalization_DS_distribution[patient.mdc]
                    if hospitalization_type == "DH":
                        patient.hospitalization_type = "DH"
                        patient.dh += self.simulation.accesses_per_hospitalization_DH_distribution[patient.mdc]
                    if hospitalization_type == "DO":
                        patient.hospitalization_type = "DO"
                        patient.do = 1
                        patient.calc_days_do()
                    patient.visited_already = True
                patient.activate(process="hospitalization")

import salabim as sim

from .logger import Logger
from .mutations import Mutation, apply_mutations
from .patient import Patient
from .stats import calculate_statistics
from .structure import Structure
from .util import get_mdc_data, get_beds_info, get_iat_distribution, get_structures_distributions, \
    get_hospitalization_type_distributions, get_hospitalization_days_do_distributions, \
    get_accesses_per_hospitalization_distributions, get_repeated_hospitalizations_do_distribution


class Simulation:
    convalescence_avg_time = 7  # giorni

    structures: dict[str, Structure] = {}

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

    def setup(self):
        mdc_codes, self.info_mdc = get_mdc_data()
        self.info_beds = get_beds_info()
        self.iat_mdc = get_iat_distribution()
        self.structures_distributions, self.info_structures = get_structures_distributions(mdc_codes)
        self.hospitalization_type_distributions = get_hospitalization_type_distributions()
        self.hospitalization_days_DO_distributions = get_hospitalization_days_do_distributions(mdc_codes)
        self.accesses_per_hospitalization_DH_distribution, self.accesses_per_hospitalization_DS_distribution = \
            get_accesses_per_hospitalization_distributions()
        self.repeated_hospitalizations_DO_distribution = get_repeated_hospitalizations_do_distribution()

    def __init__(
            self,
            duration: int,
            mutations: list[Mutation],
            name: str,
            run_n: int,
    ):
        self.name = name
        self.run_n = run_n
        self.duration = duration
        self.statistics_dir = f"../statistiche/{name}/runs/{run_n}/"
        self.env = sim.Environment(trace=False, time_unit="days", random_seed=run_n)
        self.setup()
        apply_mutations(self, mutations)

        self.monitor_mdc = sim.Monitor(name='mdc')
        for mdc, _ in self.iat_mdc.items():
            self.monitor_repeat_do[mdc] = sim.Monitor(name='repeat do ' + mdc)
        for code, name in self.info_structures.items():  # creo le strutture
            if code:
                n_beds = self.info_beds[code]
                structure = Structure(simulation=self, name="structure." + code, code=code, name_s=name, n_beds=n_beds)
                self.structures[code] = structure
        for mdc, iat in self.iat_mdc.items():  # creo i generatori di pazienti
            sim.ComponentGenerator(Patient, generator_name="Patient.generator.mdc-" + mdc, iat=sim.Exponential(iat),
                                   simulation=self, mdc=mdc, mdc_desc=self.info_mdc[mdc])
        Logger(simulation=self, wait_time=1)

    def run(self):
        self.log("started")
        self.env.run(till=self.duration)
        self.log("finished")
        self.log("calculating statistics")
        calculate_statistics(self, self.statistics_dir)
        self.log("finished calculating statistics")
        self.log("completed")

    def log(self, *messages: str):
        print(f"Simulation '{self.name}' run {self.run_n:2} |", *messages)

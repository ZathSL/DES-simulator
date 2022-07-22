import salabim as sim
import scipy.stats.distributions as st


gennorm = iter(sim.External(st.gennorm.rvs(beta=0.16, size=1000, loc=1, scale=0)).dis)
print(next(gennorm))
# norminvgauss = iter(sim.External(st.norminvgauss.rvs(a=4.06, b=4.06, size=1000, loc=1.51, scale=1.76)).dis)
kappa3_1 = iter(sim.External(st.kappa3.rvs(a=1.99, size=1000, loc=1, scale=9.82)).dis)
kappa3_2 = iter(sim.External(st.kappa3.rvs(a=3.14, size=1000, loc=1, scale=7.68)).dis)
genhalf = iter(sim.External(st.genhalflogistic.rvs(c=0.02, size=1000, loc=-8.14, scale=69)).dis)
foldnorm = iter(sim.External(st.foldnorm.rvs(c=0.03, size=1000, loc=0, scale=5.52)).dis)


# patient component
class Patient(sim.Component):
    def setup(self, mdc, structure, *args, **kwargs):
        self.mdc = mdc
        self.enqueue = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.days_do = 0
        structure.entry_patient(self)

    def assign(self, ds, dh, do, days_do):
        self.enqueue = True
        self.ds = ds
        self.dh = dh
        self.do = do
        self.days_do = days_do

    def dec(self, dec_ds, dec_dh, dec_do):
        self.ds = self.ds - dec_ds
        self.dh = self.dh - dec_dh
        self.do = self.do - dec_do

    def hospitalization(self, unit):
        yield self.hold(unit)


class Structure(sim.Component):
    def setup(self):
        self.acceptance_waiting = sim.Queue("acceptance")
        self.visit_waiting = sim.Queue("visit")
        self.hospitalization_waiting = sim.Queue("hospitalization")
        self.worktodo = sim.State('worktodo')
        self.list_patients = []

    def entry_patient(self, patient):
        patient.enter(self.acceptance_waiting)

    def visit_patient(self, patient):
        if not patient.enqueue:
            if 1 <= patient.mdc <= 13 or 15 <= patient.mdc <= 20:
                do = next(gennorm)
            else:
                do = next(gennorm)
            if 1 <= patient.mdc <= 15:
                tot_days_do = next(kappa3_1)
            else:
                tot_days_do = next(kappa3_2)
            days_do = tot_days_do / do
            ds = abs(next(foldnorm))
            dh = abs(next(genhalf))
            patient.assign(ds, dh, do, days_do)
        self.hospitalization_waiting.append(patient)

    def recovery_patient(self, patient):
        if (patient.do and patient.ds and patient.dh) == 0:
            self.list_patients.append(patient)
        else:
            unit = 0
            if patient.ds > 0:
                unit = unit + 1
                if patient.do > 0:
                    unit = unit + patient.days_do
                    patient.hospitalization(unit)
                    patient.dec(dec_ds=1, dec_dh=0, dec_do=1)
                else:
                    patient.hospitalization(unit)
                    patient.dec(dec_ds=1, dec_dh=0, dec_do=0)
            elif patient.dh > 0:
                unit = unit + 1
                if patient.dh > 0:
                    unit = unit + patient.days_do
                    patient.hospitalization(unit)
                    patient.dec(dec_ds=0, dec_dh=1, dec_do=1)
                else:
                    patient.hospitalization(unit)
                    patient.dec(dec_ds=0, dec_dh=1, dec_do=0)
            elif patient.do > 0:
                unit = patient.days_do
                patient.hospitalization(unit)
                patient.dec(dec_ds=0, dec_dh=0, dec_do=1)

    def running_process(self):
        while True:
            if len(self.acceptance_waiting) == 0 and len(self.visit_waiting) == 0 and len(self.hospitalization_waiting) == 0:
                yield self.wait((self.worktodo, True, 1))
            if len(self.acceptance_waiting) > 0:
                # accepted patient
                self.visit_waiting.append(self.acceptance_waiting.pop())
            if len(self.visit_waiting) > 0:
                # patient visit
                self.visit_patient(self.visit_waiting.pop())
            if len(self.hospitalization_waiting) > 0:
                self.recovery_patient(self.hospitalization_waiting.pop())


env = sim.Environment(trace=True)
structure = Structure()
patient = Patient(mdc=10, structure=structure)
structure.activate(process='running_process')
env.run(till=365)
print()
structure.hospitalization_waiting.print_statistics()
structure.acceptance_waiting.print_statistics()
structure.visit_waiting.print_statistics()

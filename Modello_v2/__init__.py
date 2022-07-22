import salabim as sim
import scipy.stats.distributions as st
import math

gennorm = iter(sim.External(st.gennorm.rvs(beta=0.16, size=1000, loc=1, scale=0)).dis)
# norminvgauss = iter(sim.External(st.norminvgauss.rvs(a=4.06, b=4.06, size=1000, loc=1.51, scale=1.76)).dis)
kappa3_1 = iter(sim.External(st.kappa3.rvs(a=1.99, size=1000, loc=1, scale=9.82)).dis)
kappa3_2 = iter(sim.External(st.kappa3.rvs(a=3.14, size=1000, loc=1, scale=7.68)).dis)
genhalf = iter(sim.External(st.genhalflogistic.rvs(c=0.02, size=1000, loc=-8.14, scale=69)).dis)
foldnorm = iter(sim.External(st.foldnorm.rvs(c=0.03, size=1000, loc=0, scale=5.52)).dis)


# patient component
class Patient(sim.Component):
    def setup(self, mdc, structure, *args, **kwargs):
        self.mdc = mdc
        self.visited_already = False
        self.dh = 0
        self.do = 0
        self.ds = 0
        self.days_do = 0
        self.structure = structure
        structure.entry_patient(self)

    def assign(self, ds, dh, do, days_do):
        self.visited_already = True
        self.ds = math.ceil(ds)
        self.dh = math.ceil(dh)
        self.do = math.ceil(do)
        self.days_do = math.ceil(days_do)
        print(ds, dh, do, days_do)
        print(self.ds, self.dh, self.do, self.days_do)

    def dec(self, dec_ds, dec_dh, dec_do):
        self.ds = self.ds - dec_ds
        self.dh = self.dh - dec_dh
        self.do = self.do - dec_do
        print(self.ds, self.dh, self.do)

    def hospitalization(self, unit):
        #yield self.wait(unit)
        if self.do == 0 and self.ds == 0 and self.dh == 0:
            self.structure.list_patients.append(self)
        else:
            self.structure.visit_waiting.append(self)


class Structure(sim.Component):
    def setup(self):
        self.acceptance_waiting = sim.Queue("acceptance")
        self.visit_waiting = sim.Queue("visit")
        self.hospitalization_waitingDS = sim.Queue("hospitalizationDS")
        self.hospitalization_waitingDO = sim.Queue("hospitalizationDO")
        self.hospitalization_waitingDH = sim.Queue("hospitalizationDH")
        self.worktodo = sim.State('worktodo')
        self.list_patients = []

    def entry_patient(self, patient):
        patient.enter(self.acceptance_waiting)

    def visit_patient(self, patient):
        if not patient.visited_already:
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
        if patient.ds > 0:
            self.hospitalization_waitingDS.append(patient)
        elif patient.dh > 0:
            self.hospitalization_waitingDH.append(patient)
        elif patient.do > 0:
            self.hospitalization_waitingDO.append(patient)

    def running_process(self):
        while True:
            if len(self.acceptance_waiting) == 0 and len(self.visit_waiting) == 0 and \
                    len(self.hospitalization_waitingDS) == 0 and len(self.hospitalization_waitingDH) == 0 and \
                    len(self.hospitalization_waitingDO) == 0:
                yield self.wait((self.worktodo, True, 1))
            if len(self.acceptance_waiting) > 0:
                # accepted patient
                self.visit_waiting.append(self.acceptance_waiting.pop())
            if len(self.visit_waiting) > 0:
                # patient visit
                self.visit_patient(self.visit_waiting.pop())
            if len(self.hospitalization_waitingDS) > 0:
                temp_patient = self.hospitalization_waitingDS.pop()
                temp_patient.dec(dec_ds=1, dec_dh=0, dec_do=0)
                temp_patient.hospitalization(1)
            if len(self.hospitalization_waitingDH) > 0:
                temp_patient = self.hospitalization_waitingDH.pop()
                temp_patient.dec(dec_ds=0, dec_dh=1, dec_do=0)
                temp_patient.hospitalization(1)
            if len(self.hospitalization_waitingDO) > 0:
                temp_patient = self.hospitalization_waitingDO.pop()
                temp_patient.dec(dec_ds=0, dec_dh=0, dec_do=1)
                temp_patient.hospitalization(temp_patient.days_do)


env = sim.Environment(trace=True)
structure = Structure()
patient = Patient(mdc=10, structure=structure)
structure.activate(process='running_process')
env.run(till=365)
print()
structure.hospitalization_waitingDS.print_statistics()
structure.hospitalization_waitingDH.print_statistics()
structure.hospitalization_waitingDO.print_statistics()
structure.acceptance_waiting.print_statistics()
structure.visit_waiting.print_statistics()

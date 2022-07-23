import pandas as pd
from salabim import Component, Environment, ComponentGenerator, Pdf, Queue, Resource, State

from util import get_TipologieAccessi_distributions, get_GiornateDegenzaDO_distributions, get_Strutture_distributions

Strutture_distributions: dict[str, Pdf]
TipologieAccessi_distributions: dict[str, Pdf]
GiornateDegenzaDO_distributions: dict[str, Pdf]


class Struttura(Component):
    codice: str
    nome: str
    n_letti: int
    coda_accettazione: Queue
    letti: Resource

    def setup(self, codice: str, nome: str, n_letti: int):
        self.codice = codice
        self.nome = nome
        self.n_letti = n_letti
        self.coda_accettazione = Queue(codice + ".coda_accettazione")
        self.letti = Resource(codice + ".letti", self.n_letti)

    def process(self):
        while True:
            while len(self.coda_accettazione) == 0:
                yield self.passivate()
            paziente: Paziente = self.coda_accettazione.pop()
            paziente.ricoverato.set()


strutture: dict[str, Struttura] = {}


class Paziente(Component):
    mdc: str
    mdc_desc: str
    tipologia_ricovero: str
    giornate_degenza: int
    struttura: Struttura
    ricoverato: State

    def setup(self, mdc: str, mdc_desc: str):
        self.mdc = mdc
        self.mdc_desc = mdc_desc
        self.struttura = strutture[Strutture_distributions[mdc].sample()]
        self.tipologia_ricovero = TipologieAccessi_distributions[self.mdc].sample()
        if self.tipologia_ricovero == "DO":
            self.giornate_degenza = GiornateDegenzaDO_distributions[self.mdc].sample()
        else:
            self.giornate_degenza = 1
        self.ricoverato = State(self.name() + ".ricoverato")

    def process(self):
        self.enter(self.struttura.coda_accettazione)
        if self.struttura.ispassive():
            self.struttura.activate()
        yield self.wait((self.ricoverato, True))
        yield self.request(self.struttura.letti)
        yield self.hold(self.giornate_degenza)
        yield self.release(self.struttura.letti)


def setup():
    global Strutture_distributions, TipologieAccessi_distributions, GiornateDegenzaDO_distributions
    csv_mdc = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False)
    codici_mdc = csv_mdc["CODICE MDC"].to_numpy()
    info_mdc = dict(zip(codici_mdc, csv_mdc["DESCRIZIONE MDC"].to_numpy()))
    iat_mdc = dict(zip(codici_mdc, csv_mdc["INTERARRIVO IN GIORNI"].astype(float).to_numpy()))
    Strutture_distributions, info_strutture = get_Strutture_distributions(codici_mdc)
    TipologieAccessi_distributions = get_TipologieAccessi_distributions()
    GiornateDegenzaDO_distributions = get_GiornateDegenzaDO_distributions(codici_mdc)
    return iat_mdc, info_strutture, info_mdc


def main():
    global strutture
    env = Environment(trace=True, time_unit="days")

    iat_mdc, info_strutture, info_mdc = setup()
    for struttura, nome in info_strutture.items():  # creo le strutture
        n_letti = 10  # TODO: quanti letti ci sono per struttura?
        strutture[struttura] = Struttura(name="Struttura." + struttura, codice=struttura, nome=nome, n_letti=n_letti)

    for mdc, iat in iat_mdc.items():  # creo un generatore di pazienti per ogni MDC
        ComponentGenerator(Paziente, generator_name="Paziente.generator.mdc-" + mdc, iat=iat, mdc=mdc,
                           mdc_desc=info_mdc[mdc])

    sim_time_days = 1
    env.run(till=sim_time_days)


if __name__ == '__main__':
    main()

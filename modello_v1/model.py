import pandas as pd
from salabim import Component, Environment, ComponentGenerator, Pdf, Queue, Resource

from util import get_TipologieAccessi_distributions, get_GiornateDegenzaDO_distributions, get_Strutture_distributions

Strutture_distributions: dict[str, Pdf]
TipologieAccessi_distributions: dict[str, Pdf]
GiornateDegenzaDO_distributions: dict[str, Pdf]


class Struttura(Component):
    codice: str
    nome: str
    coda_accettazione: Queue
    coda_visita: Queue
    coda_ricovero: Queue
    personale_accettazione: Resource
    medici: Resource
    letti: Resource

    def setup(self, codice: str, nome: str):
        self.codice = codice
        self.nome = nome
        self.coda_accettazione = Queue(codice + ".coda_accettazione")
        self.coda_visita = Queue(codice + ".coda_visita")
        self.coda_ricovero = Queue(codice + ".coda_ricovero")
        self.personale_accettazione = Resource(codice + ".personale_accettazione", 10)
        self.medici = Resource(codice + ".medici", 10)
        self.letti = Resource(codice + ".letti", 10)

    def process(self):
        while True:
            yield self.hold(1)


strutture: dict[str, Struttura] = {}


class Paziente(Component):
    mdc: str
    mdc_desc: str
    tipologia_ricovero: str
    giornate_degenza: int
    struttura: Struttura

    def setup(self, mdc: str, mdc_desc: str):
        self.mdc = mdc
        self.mdc_desc = mdc_desc
        self.struttura = strutture[Strutture_distributions[mdc].sample()]

    def process(self):
        yield self.enter(self.struttura.coda_accettazione)
        yield self.request(self.struttura.personale_accettazione)
        yield self.hold(10)
        yield self.release(self.struttura.personale_accettazione)
        yield self.enter(self.struttura.coda_visita)
        yield self.request(self.struttura.medici)
        yield self.hold(10)
        self.tipologia_ricovero = TipologieAccessi_distributions[self.mdc].sample()
        self.giornate_degenza = 1
        if self.tipologia_ricovero == "DO":
            self.giornate_degenza = GiornateDegenzaDO_distributions[self.mdc].sample()
        yield self.release(self.struttura.medici)
        yield self.enter(self.struttura.coda_ricovero)
        yield self.request(self.struttura.letti)
        yield self.hold(self.giornate_degenza * 60 * 24)


def setup():
    global Strutture_distributions, TipologieAccessi_distributions, GiornateDegenzaDO_distributions
    csv_mdc = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False)
    codici_mdc = csv_mdc["CODICE MDC"].to_numpy()
    info_mdc = dict(zip(codici_mdc, csv_mdc["DESCRIZIONE MDC"].to_numpy()))
    iat_mdc = dict(zip(codici_mdc, csv_mdc["CONTEGGIO PER GIORNO"].astype(float).to_numpy()))
    Strutture_distributions, info_strutture = get_Strutture_distributions(codici_mdc)
    TipologieAccessi_distributions = get_TipologieAccessi_distributions()
    GiornateDegenzaDO_distributions = get_GiornateDegenzaDO_distributions(codici_mdc)
    return iat_mdc, info_strutture, info_mdc


def main():
    global strutture
    env = Environment(trace=True, time_unit="minutes")

    iat_mdc, info_strutture, info_mdc = setup()
    for struttura, nome in info_strutture.items():  # creo le strutture
        strutture[struttura] = Struttura(name="Struttura." + struttura, codice=struttura, nome=nome)

    for mdc, iat in iat_mdc.items():  # creo un generatore di pazienti per ogni MDC
        ComponentGenerator(Paziente, iat=iat, mdc=mdc, mdc_desc=info_mdc[mdc])

    env.run(till=50)
    print()


if __name__ == '__main__':
    main()

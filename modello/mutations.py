from modello.model import Mutation


def mutations_example():
    return [  # mutazioni di esempio, l'ordine delle mutazioni conta
        Mutation(type="structure", id="030070-00", ops={"delete": True}),  # elimina la struttura
        Mutation(type="structure", id="030017-00", ops={"beds": 10}),  # imposta i letti della struttura a 10
        Mutation(type="structure", id="030038-00", ops={"beds": 0.50}),  # riduce i letti della struttura del 50%
        Mutation(type="structure", id="*", ops={"beds": 1.10}),  # aumenta i letti di tutte le strutture del 10%
    ]


def delete_5_biggest_structures():
    return [
        Mutation(type="structure", id="030901-01", ops={"delete": True}),
        Mutation(type="structure", id="030905-00", ops={"delete": True}),
        Mutation(type="structure", id="030906-00", ops={"delete": True}),
        Mutation(type="structure", id="030913-00", ops={"delete": True}),
        Mutation(type="structure", id="030924-00", ops={"delete": True}),
    ]


def delete_5_smallest_structures():
    return [
        Mutation(type="structure", id="030070-00", ops={"delete": True}),
        Mutation(type="structure", id="030071-00", ops={"delete": True}),
        Mutation(type="structure", id="030071-01", ops={"delete": True}),
        Mutation(type="structure", id="030075-00", ops={"delete": True}),
        Mutation(type="structure", id="030079-00", ops={"delete": True})
    ]


def decrease_all_beds_percent(percent: float):
    return [
        Mutation(type="structure", id="*", ops={"beds": 1.0 - percent / 100}),
    ]


def increase_all_beds_percent(percent: float):
    return [
        Mutation(type="structure", id="*", ops={"beds": 1.0 + percent / 100}),
    ]


def change_convalescence_avg_time(time: int):
    return [
        Mutation(type="parameter", id="convalescence_avg_time", ops={"value": time}),
    ]

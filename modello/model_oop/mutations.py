from dataclasses import dataclass
from typing import Any


@dataclass
class Mutation:
    type: str
    id: str
    ops: dict[str, Any]


def apply_mutations(simulation: "Simulation", mutations: list[Mutation]):
    for mutation in mutations:
        if mutation.type == "structure":
            apply_structure_mutation(simulation, mutation.id, mutation.ops)
        elif mutation.type == "parameter":
            apply_parameter_mutation(simulation, mutation.id, mutation.ops)
        else:
            raise ValueError("Unknown mutation type: " + mutation.type)


def apply_parameter_mutation(simulation: "Simulation", param: str, ops: dict):
    if param == "convalescence_avg_time":
        if "value" in ops:
            simulation.convalescence_avg_time = ops["value"]
        else:
            raise ValueError("Missing value in parameter mutation")
    else:
        raise ValueError("Unknown parameter: " + param)


# noinspection PyProtectedMember
def apply_structure_mutation(simulation: "Simulation", key: str, ops: dict):
    keys = simulation.info_structures.keys() if key == "*" else [key]  # se key è "*" considero tutte le strutture
    for key in keys:
        for op, value in ops.items():
            if op == "delete":  # elimino la struttura
                if key in simulation.info_structures:
                    del simulation.info_structures[key]
                    del simulation.info_beds[key]
                    for _, pdf in simulation.structures_distributions.items():
                        try:
                            index = pdf._x.index(key)
                            pdf._x.pop(index)
                            pdf._cum.pop(index)
                        except ValueError:
                            pass
                else:
                    raise ValueError(key + " not found")
            elif op == "beds":  # modifico il numero di letti
                if key in simulation.info_structures:
                    if isinstance(value, int):  # imposto il numero di letti
                        simulation.info_beds[key] = value
                    elif isinstance(value, float):  # vario il numero di letti di una percentuale
                        simulation.info_beds[key] = round(value * simulation.info_beds[key])
                    else:
                        raise ValueError("Invalid value for beds")
                else:
                    raise ValueError(key + " not found")
            else:
                raise ValueError("Invalid mutation operation")

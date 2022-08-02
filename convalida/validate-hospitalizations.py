import pandas as pd


def validate_hospitalizations():
    original = pd.read_csv("../Dati per la convalida/mean_hospitalization_dataset.csv", keep_default_na=False,
                           dtype={"Codice Struttura Di Ricovero": str})
    original.set_index("STRUTTURA", inplace=True)
    original.sort_index(inplace=True)
    original.columns = original.columns.str.split("_", expand=True)
    generated = pd.read_csv("../statistiche/base/hospitalization_type_patients_treated_mean.csv", keep_default_na=False,
                            dtype={"STRUTTURA": str})
    generated.set_index("STRUTTURA", inplace=True)
    generated.sort_index(inplace=True)
    generated.columns = generated.columns.str.split("_", expand=True)
    diff_do = original["RICOVERI DO", "MEDIA"].sub(generated["RICOVERI DO", "MEDIA"]).abs().rename("RICOVERI DO")
    diff_dh = original["RICOVERI DH", "MEDIA"].sub(generated["RICOVERI DH", "MEDIA"]).abs().rename("RICOVERI DH")
    diff_ds = original["RICOVERI DS", "MEDIA"].sub(generated["RICOVERI DS", "MEDIA"]).abs().rename("RICOVERI DS")
    diff_tot = original["TOTALE RICOVERI", "MEDIA"].sub(generated["TOTALE RICOVERI", "MEDIA"]).abs().rename(
        "TOTALE RICOVERI")
    concat = pd.concat([diff_do, diff_dh, diff_ds, diff_tot], axis=1)
    concat = pd.concat([concat, pd.DataFrame.from_dict({
        "MEDIA": concat.mean(),
        "VARIANZA": concat.var(),
        "STD": concat.std(),
    }, orient="index")], axis=0)
    concat.index.name = "STRUTTURA"
    concat.to_csv("hospitalizations_distribution_diff.csv", float_format="%.15f", encoding="utf-8")


if __name__ == "__main__":
    validate_hospitalizations()

import numpy as np
import pandas as pd


def validate_mdc():
    original = pd.read_csv("../distribuzioni/empiriche/MDC/MDCDistribution.csv", keep_default_na=False,
                           dtype={"CODICE MDC": str})
    original.set_index("CODICE MDC", inplace=True)
    original.index.name = "MDC"
    original = original["FREQUENZA"].rename("ORIGINALE")
    generated = pd.read_csv("../statistiche/base/mdc_distribution_mean.csv", keep_default_na=False,
                            dtype={"MDC": str})
    generated.set_index("MDC", inplace=True)
    generated = generated["FREQUENCY"].rename("GENERATO")
    concat = pd.concat([original, generated], axis=1)
    concat["DIFF"] = np.absolute((concat["ORIGINALE"] - concat["GENERATO"]))/concat["ORIGINALE"] * 10
    concat.drop(["ORIGINALE", "GENERATO"], axis=1, inplace=True)
    concat = pd.concat([concat, pd.DataFrame.from_dict({
        "MEDIA": concat.mean(),
        "VARIANZA": concat.var(),
        "STD": concat.std(),
    }, orient="index")], axis=0)
    concat.index.name = "MDC"
    concat.to_csv("mdc_distribution_diff.csv", float_format="%.15f", encoding="utf-8")


if __name__ == "__main__":
    validate_mdc()

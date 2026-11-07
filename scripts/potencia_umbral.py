"""Power table of PREREGISTRO.md (section «Potencia», amendment 4) from the simulations already saved, in seconds.

contraste.py --sintetico keeps every simulation (beta, HC1 interval, permutation p, beta without Madrid) so that the
H1 rule can be re-applied with another permutation threshold without simulating again. This script does exactly that
with the three thresholds of amendment 4 (0.05, 0.025, 0.01) on:
  resultados/potencia_sintetica_200x199.json   beta 0 and -0.5, 200 simulations per case
      (made with: python -P scripts/contraste.py --sintetico --sims 200 --betas 0 -0.5 --sin-ensayo)
  resultados/potencia_sintetica_100x199.json   beta -1.1, 100 simulations per case
      (made with: python -P scripts/contraste.py --sintetico --sims 100 --betas -1.1 --sin-ensayo)
The "power" block inside those files was written with the threshold of the time (0.05); the table in PREREGISTRO.md
uses 0.01, the one amendment 4 chose, and is what this script prints.
Usage:  python -P scripts/potencia_umbral.py
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT  # noqa: E402

FILES = ["potencia_sintetica_200x199.json", "potencia_sintetica_100x199.json"]


def main():
    sims = pd.concat([pd.DataFrame(json.loads((ROOT / "resultados" / f).read_text(encoding="utf-8"))["simulations"])
                      for f in FILES], ignore_index=True)
    hi = sims["ci95"].str[1]
    out = {}
    for alpha in (0.05, 0.025, 0.01):
        yes = (sims["beta"] < 0) & (hi < 0) & (sims["p_perm"] < alpha) & (sims["beta_without_madrid"] < 0)
        out[alpha] = sims.assign(yes=yes).groupby(["planted_beta", "noise_sd"])["yes"].mean().mul(100).round(1)
    table = pd.DataFrame(out).rename(columns=lambda a: f"% «sí» con p < {a}")
    table["simulaciones"] = sims.groupby(["planted_beta", "noise_sd"]).size()
    print(table.to_string())


if __name__ == "__main__":
    main()

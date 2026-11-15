"""PREDICTION written before the data exist (15-Nov-2026, 23:4x): the 26 municipalities that went from a 600 to a 900 EUR cap in 2024.

In the 2024 call the Comunidad raised the cap from 600 to 900 EUR in 26 municipalities (resultados/acierto_ampliacion_2024.json).
That is the natural experiment the cross-section cannot give: the same municipality before and after a change of cap, against
the municipalities that kept 600 EUR. On 15-Nov-2026 the portal only has the Bono 2022 requests by municipality (the CKAN search
for «bono alquiler joven» returns spacm_bono_alquiler_joven_2022 and nothing for 2023-2025), so nothing here has seen 2024 data.

What the model predicts (the simulator's request model, with the prudent part of the cap from exploratorio_topes_falsos.json):
  ratio = sum_i base_i * exp(beta * (share_above_900_i - share_above_600_i)) / sum_i base_i,  over the 26 municipalities,
  base_i = simulated requests with the 2022 caps; shares from SERPAVI 2024 (p25, p75, log-normal), as in the simulator.
  Central value with beta, range with the two ends of its 95 % interval.

How it will be checked when the 2024 requests by municipality are published (written now, before seeing them):
  Poisson of the requests of 2022 and 2024 by municipality, with municipality and year effects, exposure the young of 20-34
  of each year, and a dummy «went to 900 EUR in 2024» x 2024 (difference in differences), errors clustered by municipality,
  over the 26 that moved and the municipalities that kept 600 EUR both years.
  It comes out as predicted if the rate ratio is above 1 and its 95 % interval does not touch 1. If it is between 1 and 1.10,
  or not precise, it is said as it is. Other changes of the 2024 call (budget, deadlines) hit both groups alike.
Usage:  python -P scripts/prediccion_2024.py   -> resultados/prediccion_2024.json
"""
import json
import math
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, ROOT, share_above  # noqa: E402


def main():
    sim = pd.read_csv(INTERIM / "simulador_municipios.csv", dtype={"ine": str})
    m24 = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str}).set_index("ine")
    joint = json.loads((ROOT / "resultados" / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))
    beta = joint["real_cap_and_uniform_900"]["real_cap"]["beta"]
    lo, hi = joint["real_cap_and_uniform_900"]["real_cap"]["ci95"]
    mov = sim[(sim["tope_2022"] == 600) & (sim["tope_2024"] == 900)].copy()
    p25, p75 = m24.loc[mov["ine"], "serpavi_p25_2024"].to_numpy(), m24.loc[mov["ine"], "serpavi_p75_2024"].to_numpy()
    mov["ds"] = [share_above(900, a, z) - share_above(600, a, z) for a, z in zip(p25, p75)]
    base = mov["solicitudes_lista_2022_29"].to_numpy(float)

    def ratio(b):
        return float(sum(w * math.exp(b * d) for w, d in zip(base, mov["ds"])) / base.sum())

    pred = {k: round(100 * (ratio(b) - 1), 1) for k, b in (("central", beta), ("low", hi), ("high", lo))}
    out = {"note": "PREDICCIÓN escrita el 15-nov-2026, antes de que haya solicitudes de 2024 por municipio en el portal",
           "n_moved": len(mov), "beta_cap": beta, "beta_ci95": [lo, hi],
           "simulated_requests": {"caps_2022": round(float(base.sum()), 1),
                                  "caps_2024": round(float(mov["solicitudes_actual_2024_55"].sum()), 1)},
           "mean_share_points_removed": round(100 * float(-mov["ds"].mean()), 1),
           "predicted_extra_requests_per_young_pct": pred,
           "moved": mov[["ine", "municipio"]].to_dict("records"),
           "check_rule": "DiD Poisson 2022-2024, efectos de municipio y año, errores por municipio: se cumple si la razón de "
                         "tasas es > 1 y su IC 95 % no toca el 1"}
    text = json.dumps(out, indent=1, ensure_ascii=False, default=float)
    print(text)
    (ROOT / "resultados" / "prediccion_2024.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

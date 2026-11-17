"""EXPLORATORY (not pre-registered; written 17-Nov-2026, BEFORE running it): before the 2024 change, did the 26
municipalities that went from 600 to 900 EUR move like the ones that kept 600 EUR? And how much could the planned 2024
check see?

The 2024 check (prediccion_2024.py, written 15-Nov) is a difference in differences: the 26 municipalities that moved
against those that kept 600 EUR, Bono 2022 vs Bono 2024. The Comunidad chose the 26, so they are not random: if they were
already growing differently before 2024, the check would mistake that for the cap. The Bono has only 2022, but the Ayudas
al alquiler para jóvenes (programme 5.1) have 2022 and 2023 with the same caps both years (panel_ayudas.py), so the same
design can be run as a PLACEBO on 2022-2023, when nothing changed for the 26: a "moved in 2024" x 2023 dummy in a Poisson
with municipality and year effects, exposure the young people 20-34, errors clustered by municipality.
  - parallel trends: the placebo rate ratio should be near 1 (it cannot prove them: one earlier year only)
  - power: the placebo's standard error is the noise of this very design; with it, how often a 5 % test would see the
    predicted effect. The Bono has more requests than the Ayudas, so this is the pessimistic side (🔬)
Written before running (17-Nov-2026, in the commit that adds this script):
  T1  the placebo rate ratio (moved x 2023) is between 0.85 and 1.15, and its 95 % interval contains 1
  T2  in raw totals, the 2023/2022 growth of requests of the 26 is within 15 % of that of the 600 EUR municipalities
  T3  with that standard error, the power to see the central prediction (+29.6 %) is between 50 % and 95 %, and the
      power to see the low end (+10 %) is under 40 %
Usage:  python -P scripts/tendencias_2024.py   (after panel_ayudas.py and simulador.py) -> resultados/tendencias_2024.json
"""
import json
import math
import pathlib
import sqlite3
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm as gauss

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, ROOT  # noqa: E402
import panel_ayudas  # noqa: E402

OUT = ROOT / "resultados" / "tendencias_2024.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # the expectations print ✅ / ❌
    sim = pd.read_csv(INTERIM / "simulador_municipios.csv", dtype={"ine": str})
    moved = set(sim.loc[(sim["tope_2022"] == 600) & (sim["tope_2024"] == 900), "ine"])
    kept = set(sim.loc[(sim["tope_2022"] == 600) & (sim["tope_2024"] == 600), "ine"])
    p = panel_ayudas.panel()
    p = p[p["ine"].isin(moved | kept)].copy()
    p["moved_x_2023"] = (p["ine"].isin(moved) & (p["year"] == 2023)).astype(float)
    X = pd.get_dummies(p["ine"], prefix="m", drop_first=True, dtype=float)
    X = sm.add_constant(X.assign(y2023=(p["year"] == 2023).astype(float), moved_x_2023=p["moved_x_2023"]))
    groups = pd.factorize(p["ine"])[0]
    r = sm.GLM(p["requests"].to_numpy(float), X, family=sm.families.Poisson(),
               offset=np.log(p["young"].to_numpy(float))).fit(cov_type="cluster", cov_kwds={"groups": groups})
    b, se = float(r.params["moved_x_2023"]), float(r.bse["moved_x_2023"])
    lo, hi = b - 1.96 * se, b + 1.96 * se

    tot = p.assign(g=np.where(p["ine"].isin(moved), "moved", "kept")).groupby(["g", "year"])["requests"].sum()
    growth = {g: float(tot[(g, 2023)] / tot[(g, 2022)]) for g in ("moved", "kept")}

    pred = json.loads((ROOT / "resultados" / "prediccion_2024.json").read_text(encoding="utf-8"))
    central = pred["predicted_extra_requests_per_young_pct"]["central"] / 100
    low = pred["predicted_extra_requests_per_young_pct"]["low"] / 100

    def power(effect):
        d = math.log(1 + effect) / se
        return float(gauss.cdf(d - 1.96) + gauss.cdf(-d - 1.96))

    n_m, n_k = int(p.loc[p["ine"].isin(moved), "ine"].nunique()), int(p.loc[p["ine"].isin(kept), "ine"].nunique())
    req = p.groupby("year")["requests"].sum()
    with sqlite3.connect(ROOT / "data" / "bono_alquiler_joven.sqlite") as con:  # the Bono 2022 requests, same municipalities
        b22 = pd.read_sql("SELECT ine, solicitudes FROM solicitudes WHERE programa = 'bono_alquiler_joven' "
                          "AND anio_convocatoria = 2022", con)
    bono = b22.loc[b22["ine"].isin(set(p["ine"])), "solicitudes"].sum()
    out = {
        "note": "EXPLORATORIO, escrito el 17-nov-2026 antes de ejecutarlo: placebo de diferencias en diferencias con las "
                "Ayudas al alquiler para jóvenes 2022-2023 (mismos topes los dos años), entre los municipios que pasaron "
                "de 600 a 900 € en 2024 y los que siguieron en 600 €",
        "municipios": {"pasaron_a_900_en_2024": n_m, "siguieron_en_600": n_k,
                       "faltan_en_el_panel": sorted((moved | kept) - set(p["ine"]))},
        "solicitudes_ayudas": {"2022": int(req[2022]), "2023": int(req[2023])},
        "solicitudes_bono_2022_en_los_mismos_municipios": int(bono),
        "placebo_2023": {"beta": b, "se_cluster": se, "rate_ratio": round(math.exp(b), 3),
                         "rate_ratio_ci95": [round(math.exp(lo), 3), round(math.exp(hi), 3)]},
        "crecimiento_2023_sobre_2022": {"pasaron_a_900": round(growth["moved"], 3), "siguieron_en_600": round(growth["kept"], 3),
                                        "cociente": round(growth["moved"] / growth["kept"], 3)},
        "potencia_con_este_error": {"prediccion_central_pct": round(100 * central, 1), "potencia_central": round(power(central), 3),
                                    "prediccion_baja_pct": round(100 * low, 1), "potencia_baja": round(power(low), 3)},
    }
    rr, gr = out["placebo_2023"]["rate_ratio"], out["crecimiento_2023_sobre_2022"]["cociente"]
    ci = out["placebo_2023"]["rate_ratio_ci95"]
    pw = out["potencia_con_este_error"]
    ok = lambda c: "✅" if c else "❌"  # noqa: E731
    out["esperado"] = [
        f"T1 (placebo entre 0,85 y 1,15, con 1 en el intervalo): {rr} ({ci[0]} a {ci[1]}) -> "
        f"{ok(0.85 <= rr <= 1.15 and ci[0] <= 1 <= ci[1])}",
        f"T2 (crecimiento en bruto a menos del 15 %): cociente {gr} -> {ok(0.85 <= gr <= 1.15)}",
        f"T3 (potencia para +{pw['prediccion_central_pct']} % entre 50 y 95 %; para +{pw['prediccion_baja_pct']} %, "
        f"menos del 40 %): {round(100 * pw['potencia_central'])} % y {round(100 * pw['potencia_baja'])} % -> "
        f"{ok(0.5 <= pw['potencia_central'] <= 0.95 and pw['potencia_baja'] < 0.4)}",
    ]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

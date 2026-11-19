"""EXPLORATORY check of the simulator against the real Bono 2022 (written 19-Nov-2026 BEFORE running it; expectations below).

Why: the simulator (simulador.py) gives the bonos "por orden de llegada" in proportion to each municipality's requests,
which assumes that the order of arrival does not depend on the municipality. The portal's Bono 2022 dataset has, per
municipality, the requests AND the accepted ones (11,477 accepted in the whole region), so that assumption can be
checked with the portal's own data. Note: the simulator uses the 2024 budget (31.8 M EUR = 5,300 bonos of 250 EUR),
not the 2022 one, so the totals are not comparable; only the SHARES are.
Honesty note: a simulated jury rehearsal (19-Nov-2026, before this script existed) did a first quick calculation and saw
two shares (Madrid city about 64 % of the accepted and 65 % in the simulator) and a rank correlation of about 0.95. So
this is not a blind test: it puts that calculation in code, with intervals, so that every figure said comes from here.

What it computes (the 132 municipalities of the simulator, with need groups from necesidad_2024.py):
  1. acceptance rate (accepted / requests) in 2022 by need group, with a 95 % Wilson interval
  2. each group's share of the accepted (real 2022) against its share of the simulator's bonos under the 2022 caps
     (bonos_lista_2022_29), and against its share of the 2022 requests
  3. Spearman rank correlation, per municipality, between the real accepted and the simulated bonos
  4. how many municipalities with 50 or more requests have an acceptance rate outside the regional rate +- 10 points

Expected (written before running):
  - acceptance rate close to the regional one (about 24 %) in every group: all four within 20-28 %
  - Madrid city's share of the accepted within 3 points of its share of the simulator's bonos; same for each third
  - Spearman above 0.9
  - If a group has a clearly different rate (interval not touching the regional rate), first-come is NOT neutral by
    place, and the simulator's "llegada" rule would need that correction: it is said, as with the rest.
Usage:  python -P scripts/reparto_real_2022.py   (run necesidad_2024.py and simulador.py first)
        -> resultados/reparto_real_2022.json
"""
import json
import math
import pathlib

import pandas as pd
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[1]
INTERIM, RES = ROOT / "data" / "interim", ROOT / "resultados"


def wilson(k, n, z=1.959964):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(100 * (centre - half), 1), round(100 * (centre + half), 1)]


mun = pd.read_csv(INTERIM / "municipios_2024.csv")[["ine", "bono_solicitudes", "bono_aceptadas"]]
sim = pd.read_csv(INTERIM / "simulador_municipios.csv")[["ine", "municipio", "grupo_necesidad", "bonos_lista_2022_29"]]
df = sim.merge(mun, on="ine", how="left", validate="one_to_one")
assert df["bono_solicitudes"].notna().all(), "a simulator municipality has no Bono 2022 row"

req, acc, bon = df["bono_solicitudes"].sum(), df["bono_aceptadas"].sum(), df["bonos_lista_2022_29"].sum()
regional = 100 * acc / req
groups = {}
for g, d in df.groupby("grupo_necesidad"):
    groups[g] = {
        "municipalities": int(len(d)),
        "requests_2022": int(d["bono_solicitudes"].sum()),
        "accepted_2022": int(d["bono_aceptadas"].sum()),
        "acceptance_rate_pct": round(100 * d["bono_aceptadas"].sum() / d["bono_solicitudes"].sum(), 1),
        "acceptance_rate_ci95": wilson(d["bono_aceptadas"].sum(), d["bono_solicitudes"].sum()),
        "share_of_accepted_pct": round(100 * d["bono_aceptadas"].sum() / acc, 1),
        "share_of_requests_pct": round(100 * d["bono_solicitudes"].sum() / req, 1),
        "share_of_simulated_bonos_pct": round(100 * d["bonos_lista_2022_29"].sum() / bon, 1),
    }
rho, p_rho = spearmanr(df["bono_aceptadas"], df["bonos_lista_2022_29"])
big = df[df["bono_solicitudes"] >= 50].copy()
big["rate"] = 100 * big["bono_aceptadas"] / big["bono_solicitudes"]
outside = big[(big["rate"] - regional).abs() > 10]

out = {
    "what": "Simulator (first come, 2022 caps) against the real Bono 2022 accepted requests, by need group (exploratory)",
    "written_before_running": "19-Nov-2026; a first quick calculation by a simulated jury had been seen (see docstring)",
    "municipalities": int(len(df)),
    "requests_2022": int(req),
    "accepted_2022": int(acc),
    "regional_acceptance_rate_pct": round(regional, 1),
    "simulated_bonos_2024_budget": int(round(bon)),
    "by_group": groups,
    "spearman_accepted_vs_simulated": {"rho": round(float(rho), 3), "p": float(p_rho)},
    "municipalities_50plus_requests": int(len(big)),
    "of_them_rate_outside_regional_pm10": int(len(outside)),
    "outside_list": [{"municipio": r.municipio, "requests": int(r.bono_solicitudes), "rate_pct": round(r.rate, 1)}
                     for r in outside.sort_values("bono_solicitudes", ascending=False).itertuples()],
}
(RES / "reparto_real_2022.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("accepted_2022", "regional_acceptance_rate_pct", "by_group",
                                      "spearman_accepted_vs_simulated", "of_them_rate_outside_regional_pm10")},
                 ensure_ascii=False, indent=1))

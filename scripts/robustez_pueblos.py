"""EXPLORATORY (not pre-registered; written 12-Nov-2026, before running): does the 58 % depend on how the rents of the
small municipalities are read?

The 58 % (README, slide 1): with the Plan 2026-2030, in the municipalities of 10,000 people or fewer the share of the
2024 rents above the cap (500 EUR) would be 58 %, against 26 % today; with the proposal, 21 % (simulador.py, gap_above_cap;
weighted by young people 20-34). It comes from the SERPAVI 25th and 75th percentiles of each municipality, read as a
log-normal. Two doubts a juror can raise: many small municipalities have few SERPAVI contracts (10 to 575 in 2024, median
90), and the log-normal is an assumption. Here the same three figures (today, Plan, proposal) with:
  - base: as the simulator (log-normal through the 25th and 75th percentiles)
  - log-normal through the three quartiles (the median too; least squares on the log-quartiles: the spread is the same,
    the centre moves towards the median)
  - piecewise: straight lines between the quartiles, and the base log-normal outside them (it goes through both)
  - only municipalities with at least 30, or at least 100, SERPAVI contracts in 2024 (base reading)
Written before running:
  - base gives 26 % / 58 % / 21 % (a check that this script computes the same as the simulator)
  - the two other readings stay within 3 points of 58 %; with at least 30 contracts (64 municipalities, 93 % of the
    young people of the small ones) within 3 points, and with at least 100 (37 municipalities, 70 %) within 5
  - in every case the Plan at least doubles today's share in the small municipalities
Usage:  python -P scripts/robustez_pueblos.py   (after simulador.py) -> resultados/robustez_pueblos.json
"""
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT, share_above  # noqa: E402
import simulador as sim  # noqa: E402

RES = ROOT / "resultados"
Z75 = 0.6745  # standard normal 75th percentile


def lognormal3(cap, p25, p50, p75):
    """Log-normal fitted by least squares on the three log-quartiles: same spread as share_above, centre = their mean."""
    mu, sigma = (math.log(p25) + math.log(p50) + math.log(p75)) / 3, (math.log(p75) - math.log(p25)) / (2 * Z75)
    return 1 - 0.5 * (1 + math.erf((math.log(cap) - mu) / (sigma * math.sqrt(2))))


def piecewise(cap, p25, p50, p75):
    """Straight lines between the quartiles; outside them, the log-normal of share_above (it goes through p25 and p75)."""
    if cap <= p25 or cap >= p75:
        return share_above(cap, p25, p75)
    if cap <= p50:
        return 1 - (0.25 + 0.25 * (cap - p25) / (p50 - p25))
    return 1 - (0.5 + 0.25 * (cap - p50) / (p75 - p50))


def main():
    s, _ = sim.load()
    small = (s["pob_total_2024"] <= 10000).to_numpy()
    rules = sim.rules(s)
    caps = {"hoy": s["tope_2024"].to_numpy(float), "plan": sim.plan_cap(s), "propuesta": rules["plan_p75_hasta_1000"][0]}
    q = s[["serpavi_p25_2024", "serpavi_med_2024", "serpavi_p75_2024"]].to_numpy(float)
    n = s["serpavi_n_2024"].to_numpy(float)
    young = s["jovenes_20_34_2024"].to_numpy(float)
    readings = {"base": lambda c, a, m, z: share_above(c, a, z), "lognormal_tres_cuartiles": lognormal3,
                "a_tramos_entre_cuartiles": piecewise}
    keep = {"todos": small, "al_menos_30_contratos": small & (n >= 30), "al_menos_100_contratos": small & (n >= 100)}
    out = {"note": "EXPLORATORIO: parte del alquiler de 2024 por encima del tope en los municipios de 10.000 habitantes "
                   "o menos, ponderada por jóvenes de 20 a 34 años; lo esperado está en el docstring", "variants": {}}
    for rname, f in readings.items():
        for kname, k in keep.items():
            if rname != "base" and kname != "todos":
                continue
            row = {"municipalities": int(k.sum()), "young": int(young[k].sum())}
            for cname, c in caps.items():
                sh = np.array([f(ci, a, m, z) for ci, (a, m, z) in zip(c, q)])
                row[cname] = round(float(np.average(sh[k], weights=young[k])), 3)
            out["variants"][f"{rname}__{kname}"] = row
    ref = json.loads((RES / "simulador_reparto.json").read_text(encoding="utf-8"))["gap_above_cap"]
    base = out["variants"]["base__todos"]
    assert base["hoy"] == ref["2024_rents_2024_list"]["10000_or_fewer"]
    assert base["plan"] == ref["2024_rents_plan_estatal"]["10000_or_fewer"]
    assert base["propuesta"] == ref["2024_rents_plan_p75_hasta_1000"]["10000_or_fewer"]
    plan = [v["plan"] for v in out["variants"].values()]
    out["plan_range"] = [min(plan), max(plan)]
    out["plan_at_least_doubles_today_everywhere"] = all(v["plan"] >= 2 * v["hoy"] for v in out["variants"].values())
    text = json.dumps(out, indent=1, ensure_ascii=False)
    (RES / "robustez_pueblos.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

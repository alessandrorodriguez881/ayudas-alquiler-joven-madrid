"""EXPLORATORY (not pre-registered; written 7-Nov-2026 AFTER the real test): the 3 x IPREM income requirement.

Bono rule (Acuerdo of 14-Sep-2022, art. 4.1.d and 4.4): yearly income of everyone living in the home <= 3 x IPREM
(14 payments, of the year whose income is checked: the last tax year already filed); for a room, or for young people
sharing a flat, only the applicant's own income. Nobody publishes young people by income per municipality, so this uses
the portal's IRPF returns by taxable-base bracket (all ages): the share of returns at or below 3 x IPREM, with the
bracket that holds the threshold split linearly (and the two ends of that bracket as a range). It is a proxy for how
many people the rule lets in, comparable across municipalities, not a head count of eligible young people.
  1. Share of returns <= 3 x IPREM per municipality: 2021 income (checked for the Bono 2022) and 2024 income
  2. Is that share related to the need index, income per head and the share of rents above the cap?
  3. Does the pre-registered H1 effect hold with that share as one more control? (also the cap-only model)
  4. Rule arithmetic: each cap as a share of the highest income the rule allows (gross, per month)
The simulator reads the 2024 share to weigh need quotas by the young people the rule lets in (rule
"necesidad_requisito_plan_p75_hasta_1000" in simulador.py).
Usage:  python -P scripts/requisito_ingresos.py   (after necesidad_2024.py and exploratorio_topes_falsos.py; before simulador.py)
        -> resultados/requisito_ingresos.json and data/interim/requisito_ingresos.csv
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT, cm_to_ine, leer_csv  # noqa: E402
import contraste  # noqa: E402
import simulador  # noqa: E402

NEW = ROOT / "data" / "raw_2026-11-06"
IPREM_MONTH = {2021: 564.90, 2022: 579.02, 2023: 600.0, 2024: 600.0}  # 14 payments a year
# Lower edge of each taxable-base bracket (EUR/year); the last one has no upper edge
BRACKETS = [("Menor de 6.010,00 euros", 0.0), ("Entre 6.010,01  y 12.020,00 euros", 6010.01),
            ("Entre 12.020,01 y 18.030,00 euros", 12020.01), ("Entre 18.030,01 y 21.035,00 euros", 18030.01),
            ("Entre 21.035,01 y 30.050,61 euros", 21035.01), ("Entre 30.050,62 y 60.101,21 euros", 30050.62),
            ("Más de 60.101,21 euros", 60101.22)]


def threshold(year):
    return 3 * 14 * IPREM_MONTH[year]


def irpf(base):
    d = leer_csv(next((base / "irpf_declaraciones_por_tramo").glob("*.csv")))
    d = d[d["Tipo territorio"] == "Municipios"].copy()
    d["ine"] = d["Código territorio"].map(cm_to_ine)
    d["Valor"] = pd.to_numeric(d["Valor"], errors="coerce")  # the "Unidad" of one bracket says "Miles euros": it is a count
    return d.pivot_table(index=["Año", "ine"], columns="Tramo", values="Valor")


def share_below(table, year):
    """Share of returns with taxable base <= 3 x IPREM: central (linear inside the bracket) and the two bracket ends."""
    t = table.loc[year]
    counts = t[[b for b, _ in BRACKETS]]
    total = t["Total"]
    gap = (counts.sum(axis=1, min_count=len(BRACKETS)) - total).abs()
    assert (gap.dropna() <= 1).all(), "brackets do not add up to the total"  # also checks the "Miles euros" label
    edges = [lo for _, lo in BRACKETS] + [np.inf]
    thr = threshold(year)
    k = max(i for i, lo in enumerate(edges[:-1]) if lo <= thr)
    below = counts.iloc[:, :k].sum(axis=1)
    frac = (thr - edges[k]) / (edges[k + 1] - edges[k])
    return pd.DataFrame({"central": (below + frac * counts.iloc[:, k]) / total, "low": below / total,
                         "high": (below + counts.iloc[:, k]) / total, "returns": total})


def wavg(v, w):
    ok = v.notna() & w.notna()
    return round(float((v[ok] * w[ok]).sum() / w[ok].sum()), 3)


def describe(s, elig):
    s = s.assign(elig=s["ine"].map(elig))
    out = {"by_group_weighted_by_young": {g: wavg(x["elig"], x["jovenes_20_34_2024"])
                                          for g, x in s.groupby("grupo_necesidad")},
           "all_weighted_by_young": wavg(s["elig"], s["jovenes_20_34_2024"])}
    cols = ["indice_necesidad", "renta_pc_2024", "share_above_tope_2024_en_2024", "esfuerzo_alquiler_2024"]
    out["spearman_with"] = {c: round(float(s["elig"].corr(s[c], method="spearman")), 3) for c in cols}
    out["n_municipalities"] = int(s["elig"].notna().sum())
    return out, s


def robustness(elig21):
    """H1 model of the pre-registered test with the share of returns <= 3 x IPREM (2021 income) as one more control."""
    m = contraste.load()
    m["elig"] = m["ine"].map(elig21)
    m = m.dropna(subset=["elig"]).reset_index(drop=True)
    y, sh = "bono_solicitudes", m["share_above_cap_2022"]
    ci = lambda r, n: [float(v) for v in r.conf_int().loc[n]]  # noqa: E731
    pct = lambda b: round(100 * (np.exp(0.1 * b) - 1), 2)  # noqa: E731
    out = {"n_municipalities": len(m),
           "spearman_elig_with_log_income": round(float(m["elig"].corr(m["log_income"], method="spearman")), 3)}
    for name, extra in {"h1_same_sample": None, "h1_plus_elig": {"elig": m["elig"]},
                        "cap_only_same_sample": {"share_900": m["share_above_900_2022"]},
                        "cap_only_plus_elig": {"share_900": m["share_above_900_2022"], "elig": m["elig"]}}.items():
        r = contraste.fit(m, y, sh, extra=extra)
        b = float(r.params["share"])
        out[name] = {"beta": b, "ci95": ci(r, "share"), "pct_per_10_points": pct(b)}
        if extra and "elig" in extra:
            out[name]["elig"] = {"beta": float(r.params["elig"]), "ci95": ci(r, "elig")}
    return out


def arithmetic():
    """Each cap against the highest monthly income the rule allows (3 x IPREM of 14 payments, spread over 12 months)."""
    top = threshold(2024) / 12
    caps = {"600": 600, "900": 900, "plan_1000": 1000, "plan_500": 500}
    return {"max_income_eur_month_2024": round(top, 2),
            "rent_over_max_income_pct": {k: round(100 * c / top, 1) for k, c in caps.items()},
            "rent_minus_bono_over_max_income_pct": {k: round(100 * (c - 250) / top, 1) for k, c in caps.items()}}


def main():
    old, new = irpf(RAW), irpf(NEW)  # data/raw stays frozen for the 2022 test; 2024 comes from the 6-Nov download
    e21, e24 = share_below(old, 2021), share_below(new, 2024)
    s, _ = simulador.load()
    s["grupo_necesidad"] = simulador.need_groups(s)
    desc, s = describe(s, e24["central"])
    out = {"note": "EXPLORATORIO: no preregistrado, hecho tras el contraste real. Proxy con todas las edades; ver docstring",
           "threshold_eur_year": {"2021": threshold(2021), "2024": threshold(2024)},
           "share_of_returns_below_threshold_2024": desc,
           "range_all_weighted_by_young_2024": {k: wavg(s["ine"].map(e24[k]), s["jovenes_20_34_2024"])
                                                for k in ("low", "central", "high")},
           "h1_with_income_rule_control": robustness(e21["central"]),
           "rule_arithmetic": arithmetic()}
    per = pd.DataFrame({"share_irpf_bajo_3iprem_2021": e21["central"], "share_irpf_bajo_3iprem_2024": e24["central"],
                        "share_irpf_bajo_3iprem_2024_min": e24["low"], "share_irpf_bajo_3iprem_2024_max": e24["high"],
                        "declaraciones_2024": e24["returns"]}).round(4).reset_index()
    per.to_csv(INTERIM / "requisito_ingresos.csv", index=False, encoding="utf-8")
    text = json.dumps(out, indent=1, ensure_ascii=False, default=float)
    (ROOT / "resultados" / "requisito_ingresos.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

"""Allocation simulator with a fixed budget (development period, after the pre-registered test).

The Bono 2024 has 31.8 M EUR = 5,300 bonos of 250 EUR x 24 months, granted "por orden cronológico de entrada"
(Certificado ACG, BDNS 805618) while money lasts. So a higher cap brings more requests, not more bonos: what changes
is WHERE the 5,300 bonos go. Each rule sets a cap per municipality and an allocation:
  - requests:  r_i (Bono 2022 requests per young person 20-34) x young_2024_i x exp(beta x (s_rule_i - s_2022_i))
               where s = share of the rental market above the cap (SERPAVI p25/p75, log-normal, as in the test)
  - "llegada"   (first come): bonos in proportion to requests (assumes arrival order does not depend on the municipality)
  - "necesidad" : bonos in proportion to young_2024 x need index^k (k = 1, or 2 to weigh need more), never more than a
                  municipality's requests; the "requisito" variant also multiplies by the share of IRPF returns at or
                  below 3 x IPREM (2024, from requisito_ingresos.py), so quotas follow the people the income rule lets
                  in (municipalities without that figure take the median)
Plan Estatal 2026-2030 (RD 326/2026, art. 133.1.e): cap 1,000 EUR, or 500 EUR in municipalities of 10,000 people or
fewer (also in small "núcleos" inside bigger ones, which municipal data cannot see); art. 135 lets the region raise it
with an updated rent study, which is what the "o p75 local" rules do (never below the Plan's cap).
Outputs per rule: requests, requests per bono, share of the rental market above the cap (weighted by young people),
extra money to keep the success rate of the current rule, bonos per 1,000 young people by need group (Madrid city
apart, the rest in thirds of young people by need; also the old thirds of municipalities), and the municipalities that
gain or lose the most bonos against the current rule (central beta).
beta: changing the cap only moves the part of the deterrence that is due to the cap, so the central value is the -0.54
of the exploratory model that also has the uniform 900 EUR share (with its 95 % interval); the -0.79 of the
pre-registered test (which also carries "expensive rent deters") is the high case, and 0 the no-deterrence case.
Also: requests not made in 2022 = requests if the cap had covered the whole market (share above = 0) minus actual.
Usage:  python -P scripts/simulador.py   (run exploratorio_topes_falsos.py, necesidad_2024.py and requisito_ingresos.py first)
        -> resultados/simulador_reparto.json and data/interim/simulador_municipios.csv (central beta)
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, ROOT, share_above  # noqa: E402

BUDGET_EUR = 31.8e6
BONO_EUR = 250 * 24
MADRID = "079"


def load():
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    need = ["bono_solicitudes", "jovenes_20_34_2022", "share_above_cap_2022", "serpavi_p25_2024", "serpavi_p75_2024",
            "indice_necesidad", "jovenes_20_34_2024"]
    s = t.dropna(subset=need)
    s = s[s["jovenes_20_34_2022"] > 0].copy()
    s["tasa_2022"] = s["bono_solicitudes"] / s["jovenes_20_34_2022"]
    inc = pd.read_csv(INTERIM / "requisito_ingresos.csv", dtype={"ine": str}).set_index("ine")
    s["share_irpf_bajo_3iprem_2024"] = s["ine"].map(inc["share_irpf_bajo_3iprem_2024"])
    missing = int(s["share_irpf_bajo_3iprem_2024"].isna().sum())
    s["share_irpf_bajo_3iprem_2024"] = s["share_irpf_bajo_3iprem_2024"].fillna(s["share_irpf_bajo_3iprem_2024"].median())
    cover = {"municipalities": len(s), "of_2022_requests": s["bono_solicitudes"].sum() / t["bono_solicitudes"].sum(),
             "of_young_2024": s["jovenes_20_34_2024"].sum() / t["jovenes_20_34_2024"].sum(),
             "municipalities_income_share_filled_with_median": missing}
    return s.reset_index(drop=True), cover


def rules(s):
    """Cap per municipality for each rule (EUR/month)."""
    p75 = np.ceil(s["serpavi_p75_2024"].to_numpy() / 50) * 50
    plan = plan_cap(s)
    # Art. 135 raise: the Plan's cap, or the local p75 where it is higher (3 of every 4 rents fit under the cap)
    local = np.maximum(plan, p75)
    # The same raise, but never above 1,000 EUR: income must stay under 3 x IPREM (whole household), so caps far above
    # 1,000 EUR mostly add requests from the west; this only lifts the 500 EUR of small municipalities up to their p75
    upto1000 = np.clip(p75, plan, 1000)
    return {
        "lista_2022_29": (s["tope_2022"].to_numpy(float), "llegada"),
        "actual_2024_55": (s["tope_2024"].to_numpy(float), "llegada"),
        "plan_estatal": (plan, "llegada"),
        "plan_o_p75_local": (local, "llegada"),
        "plan_p75_hasta_1000": (upto1000, "llegada"),
        "necesidad_topes_actuales": (s["tope_2024"].to_numpy(float), ("necesidad", 1)),
        "necesidad2_topes_actuales": (s["tope_2024"].to_numpy(float), ("necesidad", 2)),
        "necesidad_plan_o_p75_local": (local, ("necesidad", 1)),
        "necesidad_plan_p75_hasta_1000": (upto1000, ("necesidad", 1)),
        "necesidad_requisito_plan_p75_hasta_1000": (upto1000, ("necesidad", 1, "requisito")),
    }


def plan_cap(s):
    """Plan Estatal 2026-2030, art. 133.1.e: 1,000 EUR, or 500 EUR where the municipality has 10,000 people or fewer."""
    return np.where(s["pob_total_2024"].to_numpy() <= 10000, 500.0, 1000.0)


def need_groups(s):
    """Madrid city apart (more than half of the young people); the rest in thirds of young people by need index."""
    rest = s[s["ine"] != MADRID].sort_values("indice_necesidad")
    cum = rest["jovenes_20_34_2024"].cumsum() / rest["jovenes_20_34_2024"].sum()
    g = pd.Series("Madrid capital", index=s.index)
    g[rest.index] = np.select([cum <= 1 / 3, cum <= 2 / 3], ["resto, necesidad baja", "resto, necesidad media"],
                              "resto, necesidad alta")
    return g


def requests(s, caps, beta):
    sh = np.array([share_above(c, a, z) for c, a, z in zip(caps, s["serpavi_p25_2024"], s["serpavi_p75_2024"])])
    return s["tasa_2022"].to_numpy() * s["jovenes_20_34_2024"].to_numpy() * np.exp(beta * (sh - s["share_above_cap_2022"].to_numpy())), sh


def need_weights(s, how):
    """Quota weights: young_2024 x need index^k, also x the share under 3 x IPREM in the "requisito" variant."""
    w = s["jovenes_20_34_2024"] * s["indice_necesidad"] ** how[1]
    return (w * s["share_irpf_bajo_3iprem_2024"] if "requisito" in how else w).to_numpy()


def allocate(req, weights, n_bonos):
    """Water-filling: bonos in proportion to weights, capped at each municipality's requests; leftovers go round again.
    Weights that are 0 or missing get nothing; if no open municipality has a weight left, the rest stays unallocated."""
    weights = np.nan_to_num(np.asarray(weights, dtype=float), nan=0.0).clip(min=0)
    out, open_ = np.zeros(len(req)), req > 0
    left = min(n_bonos, req.sum())
    while left > 1e-6 and open_.any():
        w = np.where(open_, weights, 0)
        if w.sum() <= 0:
            break
        give = left * w / w.sum()
        give = np.minimum(give, req - out)
        out += give
        left -= give.sum()
        open_ = (req - out) > 1e-9
    return out


def summarise(s, req, bonos, sh, req_now):
    young = s["jovenes_20_34_2024"].to_numpy()
    by = pd.DataFrame({"t": s["tercil_necesidad"], "young": young, "bonos": bonos, "req": req}).groupby("t", observed=True).sum()
    per1000 = 1000 * by["bonos"] / by["young"]  # rounded only when written (rounding twice moved some figures)
    grp = pd.DataFrame({"g": s["grupo_necesidad"], "young": young, "bonos": bonos}).groupby("g").sum()
    given = bonos.sum()
    return {"requests": round(req.sum()), "bonos": round(given),
            "bonos_per_1000_young_by_group": (1000 * grp["bonos"] / grp["young"]).round(4).to_dict(),
            "requests_per_bono": round(req.sum() / given, 4) if given else None,
            "extra_meur_same_success_rate": round(BUDGET_EUR / 1e6 * (req.sum() / req_now - 1), 4),
            "bonos_per_1000_young_by_need": per1000.round(4).to_dict(),
            "ratio_high_vs_low_need": round(per1000["alta"] / per1000["baja"], 3) if per1000["baja"] else None,
            "pct_bonos_high_need": round(100 * by.loc["alta", "bonos"] / given, 2) if given else None,
            "pct_young_high_need": round(100 * by.loc["alta", "young"] / young.sum(), 2),
            "pct_bonos_madrid_city": round(100 * bonos[(s["ine"] == MADRID).to_numpy()].sum() / given, 2) if given else None,
            "mean_share_above_cap_weighted_by_young": round(float(np.average(sh, weights=young)), 3)}


def gap(s):
    """How much of the rental market is above the cap (weighted by young people 20-34), 2022 against 2024."""
    sh = lambda caps: np.array([share_above(c, a, z) for c, a, z in  # noqa: E731
                                zip(caps, s["serpavi_p25_2024"], s["serpavi_p75_2024"])])
    cols = {"2022_rents_2022_list": (s["share_above_cap_2022"].to_numpy(), "jovenes_20_34_2022"),
            "2024_rents_2022_list": (sh(s["tope_2022"]), "jovenes_20_34_2024"),
            "2024_rents_2024_list": (sh(s["tope_2024"]), "jovenes_20_34_2024")}
    cols["2024_rents_plan_estatal"] = (sh(plan_cap(s)), "jovenes_20_34_2024")
    cols["2024_rents_plan_p75_hasta_1000"] = (sh(rules(s)["plan_p75_hasta_1000"][0]), "jovenes_20_34_2024")
    mad = (s["ine"] == MADRID).to_numpy()
    small = (s["pob_total_2024"] <= 10000).to_numpy()
    out = {}
    for k, (v, w) in cols.items():
        w = s[w].to_numpy()
        out[k] = {"all": round(float(np.average(v, weights=w)), 3),
                  "without_madrid_city": round(float(np.average(v[~mad], weights=w[~mad])), 3),
                  "madrid_city": round(float(v[mad][0]), 3),
                  "over_10000_without_madrid": round(float(np.average(v[~small & ~mad], weights=w[~small & ~mad])), 3),
                  "10000_or_fewer": round(float(np.average(v[small], weights=w[small])), 3)}
    out["municipalities_10000_or_fewer"] = {"n": int(small.sum()), "young_2024": int(s.loc[small, "jovenes_20_34_2024"].sum())}
    v, w = cols["2024_rents_2024_list"][0], s["jovenes_20_34_2024"].to_numpy()
    out["young_2024_where_over_half_above_cap"] = {"municipalities": int((v > 0.5).sum()), "young": int(w[v > 0.5].sum()),
                                                  "of_all_young": round(float(w[v > 0.5].sum() / w.sum()), 3)}
    return out


def not_made(s, betas):
    """Bono 2022 requests that were not made because part of the market was above the cap: requests with the share
    above the cap at 0, minus the actual ones (an extrapolation to "the cap covers everything")."""
    req, sh = s["bono_solicitudes"].to_numpy(), s["share_above_cap_2022"].to_numpy()
    out = {"actual_requests_2022": int(req.sum())}
    for name, b in betas.items():
        out[name] = round(float((req * (np.exp(-b * sh) - 1)).sum()))
    return out


def movers(s, bonos, bonos_now, n=5):
    d = s[["municipio", "indice_necesidad"]].assign(bonos_now=bonos_now.round(1), bonos=bonos.round(1),
                                                    delta=(bonos - bonos_now).round(1)).sort_values("delta")
    return {"lose": d.head(n).round(1).to_dict("records"), "gain": d.tail(n)[::-1].round(1).to_dict("records")}


def main():
    s, cover = load()
    res = json.loads((ROOT / "resultados" / "contraste_real.json").read_text(encoding="utf-8"))["H1"]
    cap_only = json.loads((ROOT / "resultados" / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
        "real_cap_and_uniform_900"]["real_cap"]
    betas = {"central": cap_only["beta"], "ic_bajo": cap_only["ci95"][0], "ic_alto": cap_only["ci95"][1],
             "contraste_preregistrado": res["beta"], "sin_efecto": 0.0}
    n_bonos = BUDGET_EUR / BONO_EUR
    s["grupo_necesidad"] = need_groups(s)
    caps_now = s["tope_2024"].to_numpy(float)
    now = {b: requests(s, caps_now, v)[0] for b, v in betas.items()}
    bonos_now = allocate(now["central"], now["central"], n_bonos)
    out = {"note": "Desarrollo (después del contraste preregistrado); supuestos en el docstring de scripts/simulador.py",
           "n_bonos": n_bonos, "coverage": cover, "betas": betas, "gap_above_cap": gap(s),
           "young_by_group": s.groupby("grupo_necesidad")["jovenes_20_34_2024"].sum().astype(int).to_dict(),
           "requests_not_made_2022": not_made(s, betas), "rules": {}}
    per_muni = s[["ine", "municipio", "pob_total_2024", "tope_2022", "tope_2024", "indice_necesidad", "tercil_necesidad", "grupo_necesidad",
                  "jovenes_20_34_2024", "share_irpf_bajo_3iprem_2024", "serpavi_med_2024", "serpavi_p75_2024"]].copy()
    for name, (caps, how) in rules(s).items():
        out["rules"][name] = {"allocation": how if how == "llegada" else " x ".join(["necesidad^%d" % how[1], *how[2:]])}
        for bname, b in betas.items():
            req, sh = requests(s, caps, b)
            bonos = allocate(req, req if how == "llegada" else need_weights(s, how), n_bonos)
            out["rules"][name][bname] = summarise(s, req, bonos, sh, now[bname].sum())
            if bname == "central":
                out["rules"][name]["movers_vs_actual_2024_55"] = movers(s, bonos, bonos_now)
                per_muni[f"tope_{name}"] = caps
                per_muni[f"solicitudes_{name}"] = req.round(1)
                per_muni[f"bonos_{name}"] = bonos.round(1)
    text = json.dumps(out, indent=1, ensure_ascii=False, default=float)
    (ROOT / "resultados" / "simulador_reparto.json").write_text(text, encoding="utf-8")
    per_muni.to_csv(INTERIM / "simulador_municipios.csv", index=False, encoding="utf-8")
    print("coverage:", {k: round(v, 3) for k, v in cover.items()}, "| bonos:", n_bonos)
    print("share of the rental market above the cap:", json.dumps(out["gap_above_cap"], ensure_ascii=False))
    print("young people by group:", out["young_by_group"])
    print("requests not made in 2022:", out["requests_not_made_2022"])
    keys = ["requests", "requests_per_bono", "extra_meur_same_success_rate", "bonos_per_1000_young_by_group",
            "ratio_high_vs_low_need",
            "pct_bonos_high_need", "pct_bonos_madrid_city", "mean_share_above_cap_weighted_by_young"]
    for name, r in out["rules"].items():
        print(f"\n{name} ({r['allocation']})")
        print(pd.DataFrame({b: {k: r[b][k] for k in keys} for b in betas}).to_string())
        mv = r["movers_vs_actual_2024_55"]
        print("  gain:", [(d["municipio"], d["delta"]) for d in mv["gain"]])
        print("  lose:", [(d["municipio"], d["delta"]) for d in mv["lose"]])


if __name__ == "__main__":
    main()

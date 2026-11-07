"""Allocation simulator with a fixed budget (development period, after the pre-registered test).

The Bono 2024 has 31.8 M EUR = 5,300 bonos of 250 EUR x 24 months, granted "por orden cronológico de entrada"
(Certificado ACG, BDNS 805618) while money lasts. So a higher cap brings more requests, not more bonos: what changes
is WHERE the 5,300 bonos go. Each rule sets a cap per municipality and an allocation:
  - requests:  r_i (Bono 2022 requests per young person 20-34) x young_2024_i x exp(beta x (s_rule_i - s_2022_i))
               where s = share of the rental market above the cap (SERPAVI p25/p75, log-normal, as in the test)
  - "llegada"   (first come): bonos in proportion to requests (assumes arrival order does not depend on the municipality)
  - "necesidad" : bonos in proportion to young_2024 x need index^k (k = 1, or 2 to weigh need more), never more than a
                  municipality's requests
Outputs per rule: requests, requests per bono, share of the rental market above the cap (weighted by young people),
extra money to keep the success rate of the current rule, bonos per 1,000 young people by need tercile, and the
municipalities that gain or lose the most bonos against the current rule (central beta).
beta comes from resultados/contraste_real.json (and its 95 % interval), plus 0 (no deterrence) and the prudent -0.54
of the exploratory model that also has the uniform 900 EUR share.
Usage:  python -P scripts/simulador.py   (run necesidad_2024.py first)
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
    cover = {"municipalities": len(s), "of_2022_requests": s["bono_solicitudes"].sum() / t["bono_solicitudes"].sum(),
             "of_young_2024": s["jovenes_20_34_2024"].sum() / t["jovenes_20_34_2024"].sum()}
    return s.reset_index(drop=True), cover


def rules(s):
    """Cap per municipality for each rule (EUR/month)."""
    p75 = np.ceil(s["serpavi_p75_2024"].to_numpy() / 50) * 50
    # Plan Estatal 2026-2030: 1,000 EUR by default; art. 135 lets the region raise it with an updated rent study.
    # Proposal: 1,000 EUR, or the local p75 where it is higher (3 of every 4 rents fit under the cap); it never goes down
    local = np.maximum(1000, p75)
    return {
        "lista_2022_29": (s["tope_2022"].to_numpy(float), "llegada"),
        "actual_2024_55": (s["tope_2024"].to_numpy(float), "llegada"),
        "1000_para_todos": (np.full(len(s), 1000.0), "llegada"),
        "1000_o_p75_local": (local, "llegada"),
        "necesidad_topes_actuales": (s["tope_2024"].to_numpy(float), ("necesidad", 1)),
        "necesidad2_topes_actuales": (s["tope_2024"].to_numpy(float), ("necesidad", 2)),
        "necesidad_1000_o_p75_local": (local, ("necesidad", 1)),
    }


def requests(s, caps, beta):
    sh = np.array([share_above(c, a, z) for c, a, z in zip(caps, s["serpavi_p25_2024"], s["serpavi_p75_2024"])])
    return s["tasa_2022"].to_numpy() * s["jovenes_20_34_2024"].to_numpy() * np.exp(beta * (sh - s["share_above_cap_2022"].to_numpy())), sh


def allocate(req, weights, n_bonos):
    """Water-filling: bonos in proportion to weights, capped at each municipality's requests; leftovers go round again."""
    out, open_ = np.zeros(len(req)), req > 0
    left = min(n_bonos, req.sum())
    while left > 1e-6 and open_.any():
        give = left * np.where(open_, weights, 0) / np.where(open_, weights, 0).sum()
        give = np.minimum(give, req - out)
        out += give
        left -= give.sum()
        open_ = (req - out) > 1e-9
    return out


def summarise(s, req, bonos, sh, req_now):
    young = s["jovenes_20_34_2024"].to_numpy()
    by = pd.DataFrame({"t": s["tercil_necesidad"], "young": young, "bonos": bonos, "req": req}).groupby("t", observed=True).sum()
    per1000 = (1000 * by["bonos"] / by["young"]).round(2)
    return {"requests": round(req.sum()), "bonos": round(bonos.sum()),
            "requests_per_bono": round(req.sum() / bonos.sum(), 2),
            "extra_meur_same_success_rate": round(BUDGET_EUR / 1e6 * (req.sum() / req_now - 1), 2),
            "bonos_per_1000_young_by_need": per1000.to_dict(),
            "ratio_high_vs_low_need": round(per1000["alta"] / per1000["baja"], 3),
            "pct_bonos_high_need": round(100 * by.loc["alta", "bonos"] / bonos.sum(), 1),
            "pct_young_high_need": round(100 * by.loc["alta", "young"] / young.sum(), 1),
            "pct_bonos_madrid_city": round(100 * bonos[(s["ine"] == MADRID).to_numpy()].sum() / bonos.sum(), 1),
            "mean_share_above_cap_weighted_by_young": round(float(np.average(sh, weights=young)), 3)}


def gap(s):
    """How much of the rental market is above the cap (weighted by young people 20-34), 2022 against 2024."""
    sh = lambda caps: np.array([share_above(c, a, z) for c, a, z in  # noqa: E731
                                zip(caps, s["serpavi_p25_2024"], s["serpavi_p75_2024"])])
    cols = {"2022_rents_2022_list": (s["share_above_cap_2022"].to_numpy(), "jovenes_20_34_2022"),
            "2024_rents_2022_list": (sh(s["tope_2022"]), "jovenes_20_34_2024"),
            "2024_rents_2024_list": (sh(s["tope_2024"]), "jovenes_20_34_2024")}
    mad = (s["ine"] == MADRID).to_numpy()
    out = {}
    for k, (v, w) in cols.items():
        w = s[w].to_numpy()
        out[k] = {"all": round(float(np.average(v, weights=w)), 3),
                  "without_madrid_city": round(float(np.average(v[~mad], weights=w[~mad])), 3),
                  "madrid_city": round(float(v[mad][0]), 3)}
    v, w = cols["2024_rents_2024_list"][0], s["jovenes_20_34_2024"].to_numpy()
    out["young_2024_where_over_half_above_cap"] = {"municipalities": int((v > 0.5).sum()), "young": int(w[v > 0.5].sum()),
                                                  "of_all_young": round(float(w[v > 0.5].sum() / w.sum()), 3)}
    return out


def movers(s, bonos, bonos_now, n=5):
    d = s[["municipio", "indice_necesidad"]].assign(bonos_now=bonos_now.round(1), bonos=bonos.round(1),
                                                    delta=(bonos - bonos_now).round(1)).sort_values("delta")
    return {"lose": d.head(n).round(1).to_dict("records"), "gain": d.tail(n)[::-1].round(1).to_dict("records")}


def main():
    s, cover = load()
    res = json.loads((ROOT / "resultados" / "contraste_real.json").read_text(encoding="utf-8"))["H1"]
    betas = {"central": res["beta"], "ic_bajo": res["ci95"][0], "ic_alto": res["ci95"][1], "prudente_exploratorio": -0.5446,
             "sin_efecto": 0.0}
    n_bonos = BUDGET_EUR / BONO_EUR
    need = lambda k: (s["jovenes_20_34_2024"] * s["indice_necesidad"] ** k).to_numpy()  # noqa: E731
    caps_now = s["tope_2024"].to_numpy(float)
    now = {b: requests(s, caps_now, v)[0] for b, v in betas.items()}
    bonos_now = allocate(now["central"], now["central"], n_bonos)
    out = {"note": "Desarrollo (después del contraste preregistrado); supuestos en el docstring de scripts/simulador.py",
           "n_bonos": n_bonos, "coverage": cover, "betas": betas, "gap_above_cap": gap(s), "rules": {}}
    per_muni = s[["ine", "municipio", "tope_2022", "tope_2024", "indice_necesidad", "tercil_necesidad",
                  "jovenes_20_34_2024", "serpavi_med_2024", "serpavi_p75_2024"]].copy()
    for name, (caps, how) in rules(s).items():
        out["rules"][name] = {"allocation": how if how == "llegada" else f"necesidad^{how[1]}"}
        for bname, b in betas.items():
            req, sh = requests(s, caps, b)
            bonos = allocate(req, req if how == "llegada" else need(how[1]), n_bonos)
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
    keys = ["requests", "requests_per_bono", "extra_meur_same_success_rate", "ratio_high_vs_low_need",
            "pct_bonos_high_need", "pct_bonos_madrid_city", "mean_share_above_cap_weighted_by_young"]
    for name, r in out["rules"].items():
        print(f"\n{name} ({r['allocation']})")
        print(pd.DataFrame({b: {k: r[b][k] for k in keys} for b in betas}).to_string())
        mv = r["movers_vs_actual_2024_55"]
        print("  gain:", [(d["municipio"], d["delta"]) for d in mv["gain"]])
        print("  lose:", [(d["municipio"], d["delta"]) for d in mv["lose"]])


if __name__ == "__main__":
    main()

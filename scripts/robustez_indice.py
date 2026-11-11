"""EXPLORATORY (not pre-registered; written 12-Nov-2026, before running): is the proposal's +41 % only true when it is
measured with our own need index?

The +41 % (README, slide 3) compares, in the third of young people outside Madrid city with the most need, the aids per
1,000 young people of the proposal (quotas by young x need index x share under the Plan's income limit, with the Plan's
aid) against the Plan as it is (first come), with the same 31.8 M EUR (simulador.py, block plan_amount). The quotas use
the index, and the same index picks the third that is measured: a juror can fairly say that it is graded with its own
ruler. Here the proposal stays exactly as it is (its quotas still use our index) and only the ruler changes: the third
with the most need is picked, among the same municipalities, by other measures of need:
  - each component alone: rent effort, youth unemployment, renting households
  - the variants of necesidad_2024.py's sensitivity: the index without each component, with z-scores, with a geometric
    mean
For each ruler: aids per 1,000 young people in its top third with the Plan and with the proposal, the change, the aids
in that third, and how many of its municipalities are also in our index's top third.
Written before running:
  - our index gives the +41 % of simulador_reparto.json (a check that this script computes the same)
  - with the index variants (Spearman 0.77-0.96 with the index) the gain stays clearly positive, above +20 %
  - with single components it is smaller; renting households or youth unemployment alone may give less than +10 %. If
    any ruler gives a loss, it is said: the proposal moves aid away from that kind of need
Added after the first run (every ruler gave from +31 % to +52 %): the other two thirds and Madrid city with each ruler,
to see whether the gain goes to the top third or to every municipality outside Madrid city alike.
Usage:  python -P scripts/robustez_indice.py   (after simulador.py) -> resultados/robustez_indice.json
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT  # noqa: E402
from necesidad_2024 import COMPONENTS  # noqa: E402
import simulador as sim  # noqa: E402

RES = ROOT / "resultados"
PROPOSAL = "necesidad_requisito_plan_p75_hasta_1000"


def thirds(s, score):
    """As simulador.need_groups: Madrid city apart, the rest in thirds of young people by score (higher = more need)."""
    rest = s[s["ine"] != sim.MADRID].assign(score=score).sort_values("score")
    cum = rest["jovenes_20_34_2024"].cumsum() / rest["jovenes_20_34_2024"].sum()
    g = pd.Series("Madrid capital", index=s.index)
    g[rest.index] = np.select([cum <= 1 / 3, cum <= 2 / 3], ["resto, necesidad baja", "resto, necesidad media"],
                              "resto, necesidad alta")
    return g


def main():
    s, _ = sim.load()
    s["grupo_necesidad"] = sim.need_groups(s)
    beta = json.loads((RES / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
        "real_cap_and_uniform_900"]["real_cap"]["beta"]
    rules = sim.rules(s)
    plan_caps = rules["plan_estatal"][0]
    prop_caps, how = rules[PROPOSAL]
    req_plan, req_prop = sim.requests(s, plan_caps, beta)[0], sim.requests(s, prop_caps, beta)[0]
    aids = {"plan": sim.allocate_money(req_plan, req_plan, sim.BUDGET_EUR, sim.plan_aid(s, plan_caps)),
            "propuesta": sim.allocate_money(req_prop, sim.need_weights(s, how, sim.PLAN_INCOME), sim.BUDGET_EUR,
                                            sim.plan_aid(s, prop_caps))}
    young = s["jovenes_20_34_2024"].to_numpy(float)
    ours = (s["grupo_necesidad"] == "resto, necesidad alta").to_numpy()
    assert (thirds(s, s["indice_necesidad"]) == s["grupo_necesidad"]).all()
    ref = json.loads((RES / "simulador_reparto.json").read_text(encoding="utf-8"))["plan_amount"]
    for k, rule in (("plan", "plan_estatal"), ("propuesta", PROPOSAL)):  # the same figures as the simulator
        assert np.isclose(1000 * aids[k][ours].sum() / young[ours].sum(),
                          ref[rule]["aids_per_1000_young_by_group"]["resto, necesidad alta"], atol=1e-3)

    ranks = s[[f"rango_{c}" for c in COMPONENTS]]
    raw = s[list(COMPONENTS)]
    rulers = {"indice_del_proyecto": s["indice_necesidad"]}
    rulers.update({f"solo_{c}": s[c] for c in COMPONENTS})
    rulers.update({f"sin_{c}": ranks.drop(columns=f"rango_{c}").mean(axis=1) for c in COMPONENTS})
    rulers["zscores"] = ((raw - raw.mean()) / raw.std()).mean(axis=1)
    rulers["media_geometrica"] = np.exp(np.log(ranks).mean(axis=1))
    rest = (s["ine"] != sim.MADRID).to_numpy()
    out = {"note": "EXPLORATORIO: la propuesta no cambia (sus cupos siguen usando nuestro índice); solo cambia con qué "
                   "se elige el tercio con más necesidad. Lo esperado está en el docstring",
           "beta": beta, "rulers": {}}
    for name, score in rulers.items():
        groups = thirds(s, score)
        top = (groups == "resto, necesidad alta").to_numpy()
        per1000 = {k: 1000 * a[top].sum() / young[top].sum() for k, a in aids.items()}
        by_group = {}
        for g in ("resto, necesidad alta", "resto, necesidad media", "resto, necesidad baja", "Madrid capital"):
            k = (groups == g).to_numpy()
            p, q = (1000 * aids[r][k].sum() / young[k].sum() for r in ("plan", "propuesta"))
            by_group[g] = {"plan": round(float(p), 2), "propuesta": round(float(q), 2),
                           "change_pct": round(float(100 * (q / p - 1)), 1)}
        out["rulers"][name] = {
            "spearman_with_index": round(float(score[rest].corr(s.loc[rest, "indice_necesidad"], method="spearman")), 3),
            "municipalities_in_top_third": int(top.sum()), "young_in_top_third": int(young[top].sum()),
            "municipalities_also_in_index_top_third": int((top & ours).sum()),
            "aids_per_1000_young": {k: round(float(v), 2) for k, v in per1000.items()},
            "change_pct": round(float(100 * (per1000["propuesta"] / per1000["plan"] - 1)), 1),
            "aids": {k: round(float(a[top].sum())) for k, a in aids.items()},
            "aids_per_1000_young_by_group": by_group}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    (RES / "robustez_indice.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

"""EXPLORATORY (not pre-registered; written 8-Nov-2026, after the real test): does the requests model predict
municipalities it has not seen better when it knows the share of the rent above the cap?

The pre-registered model (contraste.py): Poisson, Bono 2022 requests, offset log(young 20-34), controls log rent, log
income, % renting households, youth unemployment and log population. The test measured the share's coefficient
in-sample; this checks prediction instead, two ways:
  A. Cross-validation on the Bono 2022 (132 municipalities): leave-one-out and 10-fold repeated 20 times. Each model is
     fitted without the held-out municipalities and scored on them by Poisson deviance (lower is better), in total, without
     Madrid city in the score (its 15,000 requests weigh most), and as the median absolute % error of the predicted
     requests where there were 10 or more. Models: controls only; + share above the real cap; + share above a uniform
     900 EUR (the fake cap that fitted better in-sample, exploratorio_topes_falsos.py); + both shares; and intercept only.
     Paired: the difference with "controls only", municipality by municipality, with its standard error.
  B. Another programme and year: the slopes fitted on the Bono 2022 predict the Ayudas al alquiler para jóvenes of 2023
     (programme 5.1, same 29 municipalities with 900 EUR), with 2023 SERPAVI rents for the rent and the share, the other
     controls of 2022 and the young people of 2022 as exposure. Only one number is fitted on the 2023 data, the
     intercept (the programme's size), the same for every model; the slopes stay those of the Bono. Also the Spearman
     correlation of predicted and observed requests per young person, which needs no intercept, and, for scale, the
     model refitted on 2023 (in-sample, the best these variables can do).
Written before running:
  - A: + real cap scores better than controls only in held-out deviance, with Madrid and without it
  - A: + uniform 900 EUR scores as well or better than + real cap, as in-sample (966 against 1,023); if so, it is said:
    it is the limitation already known (expensive rent also deters on its own)
  - A: both shares together do not beat the better single share by much out of sample (one more parameter)
  - B: the Bono's slopes with the real cap predict the Ayudas 2023 better than the slopes without it, by less than in A
    (another programme, with other conditions, and the 2023 SERPAVI change matched the portal's rents poorly)
Added 12-Nov-2026, written before running them: three models with the room route of habitaciones.py, which fitted best
in-sample but was found after seeing the data (deviance 805, against 1,023 with the real cap and 850 with a uniform
1,350 EUR). Room route = share of the rents above 1.5 x the cap: the most three young people sharing a flat on room
contracts can pay (3 x 300 = 900 EUR outside Annex II, 3 x 450 = 1,350 EUR in it). Models: + room route; + uniform
1,350 EUR; + both. The earlier models and their numbers do not change (same folds, same fits).
  - A: + room route predicts held-out municipalities better than + real cap, with Madrid and without it, and about as
    well as + uniform 1,350 EUR; both together do not beat the room route alone by much (one more parameter)
  - B: + room route also predicts the Ayudas 2023 better than + real cap; against the uniform 1,350 EUR, no guess.
    The Ayudas 5.1 have the same flat caps; RD 42/2022 sets the same room caps (300 / 450 EUR), not checked in their texts
Usage:  python -P scripts/validacion_fuera_muestra.py   -> resultados/validacion_fuera_muestra.json"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import RAW, ROOT, leer_csv  # noqa: E402
from contraste import CONTROLS, MADRID, load, shares  # noqa: E402

MODELS = {"solo_constante": None, "controles": [], "controles_tope_real": ["share_above_cap"],
          "controles_900_igual": ["share_above_900"], "controles_ambas": ["share_above_cap", "share_above_900"],
          # added 12-Nov (docstring): the room route of habitaciones.py, a uniform 1,350 EUR, and both
          "controles_habitaciones": ["share_above_rooms3"], "controles_1350_igual": ["share_above_1350"],
          "controles_habitaciones_y_1350": ["share_above_rooms3", "share_above_1350"]}
BASE = "controles"


def with_room_shares(m):
    """The room-route and uniform 1,350 EUR shares of 2022 and 2023, as habitaciones.py computes them for 2022."""
    for year in (2022, 2023):
        m[f"share_above_rooms3_{year}"] = shares(m, 1.5 * m["cap"].to_numpy(float), year)
        m[f"share_above_1350_{year}"] = shares(m, np.full(len(m), 1350.0), year)
    return m


def design(m, shares, year):
    """Covariates of one year: the share columns and log rent of that year's SERPAVI, the other controls of 2022."""
    X = m[CONTROLS].assign(log_rent=np.log(m[f"serpavi_med_{year}"]))
    X = X.assign(**{s: m[f"{s}_{year}"] for s in shares})
    return sm.add_constant(X, has_constant="add")


def design_for(name, m, year):
    shares = MODELS[name]
    return sm.add_constant(pd.DataFrame(index=m.index), has_constant="add") if shares is None else design(m, shares, year)


def unit_deviance(y, mu):
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(y > 0, y * np.log(y / mu), 0.0)
    return 2 * (t - (y - mu))


def scores(y, mu, madrid):
    d = unit_deviance(y, mu)
    big = y >= 10
    return {"deviance": float(d.sum()), "deviance_without_madrid": float(d[~madrid].sum()),
            "median_abs_pct_error_10_or_more": float(np.median(np.abs(mu[big] / y[big] - 1)) * 100)}


def gain(diff, madrid):
    """diff: deviance of "controls only" minus the model's, per municipality (> 0: the model predicts it better)."""
    return {"deviance": float(diff.sum()), "se": float(np.sqrt(len(diff)) * diff.std(ddof=1)),
            "deviance_without_madrid": float(diff[~madrid].sum()),
            "se_without_madrid": float(np.sqrt((~madrid).sum()) * diff[~madrid].std(ddof=1)),
            "municipalities_better": int((diff > 0).sum()), "of": len(diff)}


def cross_validate(m, folds):
    """Held-out predictions of every model: one array per model, each municipality predicted by a fit without it."""
    y, off = m["bono_solicitudes"].to_numpy(float), np.log(m["jovenes_20_34_2022"].to_numpy(float))
    pred = {k: np.zeros(len(m)) for k in MODELS}
    for test in folds:
        train = np.setdiff1d(np.arange(len(m)), test)
        for k in MODELS:
            X = design_for(k, m, 2022).to_numpy(float)
            r = sm.GLM(y[train], X[train], family=sm.families.Poisson(), offset=off[train]).fit()
            pred[k][test] = np.exp(X[test] @ r.params + off[test])
    return pred


def part_a(m, seed=3, repeats=20, k=10):
    y, madrid = m["bono_solicitudes"].to_numpy(float), (m["ine"] == MADRID).to_numpy()
    loo = cross_validate(m, [np.array([i]) for i in range(len(m))])
    out = {"leave_one_out": {name: scores(y, mu, madrid) for name, mu in loo.items()}}
    base = unit_deviance(y, loo[BASE])
    for name in MODELS:
        if name not in (BASE, "solo_constante"):
            out["leave_one_out"][name]["gain_vs_controls"] = gain(base - unit_deviance(y, loo[name]), madrid)
    rng = np.random.default_rng(seed)
    rep = {name: [] for name in MODELS}
    for _ in range(repeats):
        folds = np.array_split(rng.permutation(len(m)), k)
        for name, mu in cross_validate(m, folds).items():
            rep[name].append(scores(y, mu, madrid))
    out[f"{k}_fold_x{repeats}"] = {name: {s: float(np.mean([r[s] for r in rs])) for s in rs[0]} for name, rs in rep.items()}
    wins = [np.mean([a["deviance"] < b["deviance"] for a, b in zip(rep[name], rep[BASE])]) for name in MODELS]
    out[f"{k}_fold_x{repeats}_share_of_repeats_better_than_controls"] = dict(zip(MODELS, map(float, wins)))
    return out


def ayudas_2023(m):
    ay = leer_csv(next((RAW / "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos").glob("*.csv")))
    ay = ay[(ay["programa"] == 5.1) & (ay["año_convocatoria"] == 2023)].groupby("municipio")["solicitudes"].sum()
    return m["ine"].map(ay).fillna(0).to_numpy(float)


def part_b(m):
    t = m.dropna(subset=["serpavi_med_2023", "share_above_cap_2023", "share_above_900_2023", "share_above_rooms3_2023",
                         "share_above_1350_2023"]).reset_index(drop=True)
    y_bono, off = t["bono_solicitudes"].to_numpy(float), np.log(t["jovenes_20_34_2022"].to_numpy(float))
    y = ayudas_2023(t)
    madrid = (t["ine"] == MADRID).to_numpy()
    out, mus = {"n_municipalities": len(t), "requests_2023": int(y.sum())}, {}
    for name in MODELS:
        X22, X23 = design_for(name, t, 2022).to_numpy(float), design_for(name, t, 2023).to_numpy(float)
        slopes = sm.GLM(y_bono, X22, family=sm.families.Poisson(), offset=off).fit().params
        eta = X23[:, 1:] @ slopes[1:] + off  # the Bono's slopes; the intercept is the only thing fitted on 2023
        a = sm.GLM(y, np.ones((len(t), 1)), family=sm.families.Poisson(), offset=eta).fit().params[0]
        mus[name] = np.exp(a + eta)
        refit = sm.GLM(y, X23, family=sm.families.Poisson(), offset=off).fit()
        rate_pred, rate_obs = np.exp(eta - off), y / np.exp(off)
        out[name] = {**scores(y, mus[name], madrid),
                     "spearman_rate": None if name == "solo_constante" else float(spearmanr(rate_pred, rate_obs)[0]),
                     "refit_in_sample_deviance": float(refit.deviance)}
    base = unit_deviance(y, mus[BASE])
    for name in MODELS:
        if name not in (BASE, "solo_constante"):
            out[name]["gain_vs_controls"] = gain(base - unit_deviance(y, mus[name]), madrid)
    return out


def main():
    m = with_room_shares(load())
    a = part_a(m)
    b = part_b(m)
    out = {"note": "EXPLORATORIO: no preregistrado, hecho tras el contraste real; lo esperado está en el docstring",
           "n_municipalities": len(m), "A_bono_2022_cross_validation": a, "B_bono_2022_to_ayudas_jovenes_2023": b}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    (ROOT / "resultados" / "validacion_fuera_muestra.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

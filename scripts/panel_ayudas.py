"""EXPLORATORY (not pre-registered; written 7-Nov-2026 after the real test): the same municipality in 2022 and 2023.

The pre-registered test compares expensive and cheap municipalities, so anything else that differs between them could be
behind the effect. The Ayudas al alquiler para jóvenes (programme 5.1) give requests per municipality for the 2022 and
the 2023 calls, with the same caps both years (600 / 900 EUR; the Annex II list of 29 did not change until Dec-2024).
Rents rose between the two years, more in some municipalities than in others, so the share of the market above the
fixed cap moved. Model: Poisson with one dummy per municipality and one for 2023, offset log(young 20-34 of that year),
errors clustered by municipality: only changes inside each municipality count, so nothing fixed about a place (being
rich, being in the west, liking to rent) can be behind it.
Written before running:
  - expected: beta < 0 for the share above the real cap, with and without time-varying controls (log income per head
    and unemployment under 25 per 1,000 people aged 15-24, both for 2022 and 2023)
  - the same with the share above a uniform 900 EUR and a uniform 600 EUR (fake caps), side by side, and the real one
    together with the uniform 900 EUR; if the cap is the mechanism, the real share should keep a negative beta
  - how much the share moved between the two years: if it hardly moves, the interval will be wide, and that is said
  - SERPAVI rises did not match the portal's rent index well for 2022-2024 (validar_serpavi.py): noise in the change
    pulls beta towards 0
Usage:  python -P scripts/panel_ayudas.py   (after preparar_datos.py)  -> resultados/panel_ayudas.json
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT, cm_to_ine, leer_csv, norm  # noqa: E402

NEW = ROOT / "data" / "raw_2026-11-06"  # income and unemployment with 2023 (downloaded 6-Nov, identical on 7-Nov)
YEARS = (2022, 2023)


def csv(base, folder):
    return leer_csv(next((base / folder).glob("*.csv")))


def panel():
    m = pd.read_csv(INTERIM / "municipios.csv", dtype={"ine": str})
    ay = csv(RAW, "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos")
    ay = ay[(ay["programa"] == 5.1) & ay["municipio"].str.fullmatch(r"\d{3}", na=False)]
    req = ay.groupby(["municipio", "año_convocatoria"])["solicitudes"].sum()

    pop = csv(RAW, "poblacion_censada_por_edad_nacionalidad_y_sexo")
    pop = pop[(pop["Tipo territorio"] == "Municipios") & (pop["Nacionalidad"] == "Total") & (pop["Sexo"] == "Total")
              & pop["Año"].isin(YEARS)].assign(ine=lambda d: d["Código territorio"].map(cm_to_ine))
    by_age = pop.pivot_table(index=["ine", "Año"], columns="Edad", values="Valor", aggfunc="sum")
    young = by_age[["De 20-24 años", "De 25-29 años", "De 30-34 años"]].sum(axis=1)
    young1524 = by_age[["De 15-19 años", "De 20-24 años"]].sum(axis=1)

    renta = csv(NEW, "irpf_indicador_renta")
    renta = renta[(renta["Tipo territorio"] == "Municipios") & (renta["Medida"] == "Per cápita") & renta["Año"].isin(YEARS)]
    renta = renta.assign(ine=renta["Código territorio"].map(cm_to_ine), v=pd.to_numeric(renta["Valor"], errors="coerce"))
    renta = renta.set_index(["ine", "Año"])["v"]

    paro = csv(NEW, "paro_registrado_edad_municipio")
    paro = paro[paro["Año"].isin(YEARS) & (paro["Indicador"] == "Serie") & (paro["Edad"] == "Menor de 25 años")]
    loose = lambda s: " ".join(w for w in norm(s).split() if w not in ("de", "del"))  # noqa: E731  (as preparar_datos)
    paro = paro.assign(key=paro["Municipio"].map(loose)).groupby(["key", "Año"])["Valor"].mean()

    rows = []
    for _, r in m.iterrows():
        for y in YEARS:
            rows.append({"ine": r["ine"], "municipio": r["municipio"], "year": y, "cap": r["cap"],
                         "requests": req.get((r["ine"], y), 0), "young": young.get((r["ine"], y), np.nan),
                         "share_real": r[f"share_above_cap_{y}"], "share_600": r[f"share_above_600_{y}"],
                         "share_900": r[f"share_above_900_{y}"], "log_income": np.log(renta.get((r["ine"], y), np.nan)),
                         "paro25": 1000 * paro.get((loose(r["municipio"]), y), np.nan) / young1524.get((r["ine"], y), np.nan)})
    p = pd.DataFrame(rows)
    full = p.dropna().groupby("ine").filter(lambda d: len(d) == 2 and d["requests"].sum() > 0 and (d["young"] > 0).all())
    return full.reset_index(drop=True)


def fit(p, shares, controls):
    X = pd.get_dummies(p["ine"], prefix="m", drop_first=True, dtype=float)
    X = X.assign(y2023=(p["year"] == 2023).astype(float), **{k: p[k] for k in shares + controls})
    X = sm.add_constant(X)
    groups = pd.factorize(p["ine"])[0]
    return sm.GLM(p["requests"].to_numpy(float), X, family=sm.families.Poisson(),
                  offset=np.log(p["young"].to_numpy(float))).fit(cov_type="cluster", cov_kwds={"groups": groups})


def coef(r, name):
    b, (lo, hi) = float(r.params[name]), r.conf_int().loc[name]
    pct = lambda v: round(100 * (np.exp(0.1 * v) - 1), 2)  # noqa: E731
    return {"beta": b, "ci95": [float(lo), float(hi)], "pct_per_10_points": pct(b), "pct_ci95": [pct(lo), pct(hi)]}


def main():
    p = panel()
    wide = p.pivot(index="ine", columns="year", values=["share_real", "share_900", "share_600", "requests", "young"])
    d_real = wide["share_real"][2023] - wide["share_real"][2022]
    d_900 = wide["share_900"][2023] - wide["share_900"][2022]
    controls = ["log_income", "paro25"]
    out = {"note": "EXPLORATORIO: no preregistrado, hecho tras el contraste real; ver docstring",
           "n_municipalities": int(p["ine"].nunique()), "by_cap": p.drop_duplicates("ine").groupby("cap").size().to_dict(),
           "requests_by_year": p.groupby("year")["requests"].sum().astype(int).to_dict(),
           "change_share_real_2022_2023": {"mean_points": round(100 * float(d_real.mean()), 2),
                                           "sd_points": round(100 * float(d_real.std()), 2),
                                           "min_points": round(100 * float(d_real.min()), 2),
                                           "max_points": round(100 * float(d_real.max()), 2),
                                           "corr_with_change_share_900": round(float(d_real.corr(d_900)), 3)}}
    models = {"real_cap_no_controls": (["share_real"], []), "real_cap": (["share_real"], controls),
              "uniform_900": (["share_900"], controls), "uniform_600": (["share_600"], controls),
              "real_cap_and_uniform_900": (["share_real", "share_900"], controls)}
    for name, (shares, ctrl) in models.items():
        r = fit(p, shares, ctrl)
        out[name] = {s: coef(r, s) for s in shares}
        out[name]["deviance"] = float(r.deviance)
    text = json.dumps(out, indent=1, ensure_ascii=False, default=float)
    (ROOT / "resultados" / "panel_ayudas.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

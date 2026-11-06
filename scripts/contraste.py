"""Pre-registered test of PREREGISTRO.md (does the Bono rent cap deter young people from applying?).

  python -P scripts/contraste.py --sintetico   power check: real covariates, INVENTED outcomes with planted effects
  python -P scripts/contraste.py               the real test; refuses to run before 7-Nov-2026 (development period)

The synthetic mode never reads the real request counts: outcomes are drawn from a model with known coefficients.
"""
import argparse
import datetime
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, ROOT, share_above  # noqa: E402

START = datetime.date(2026, 11, 7)
CONTROLS = ["log_rent", "log_income", "pct_alquiler_2021", "paro25_por_1000_15_24", "log_pop"]
MADRID = "079"
# Amendment 4 of PREREGISTRO.md (2-Nov, invented data only): 0.05 and 0.025 gave > 5 % false "yes" without an effect
P_THRESHOLD = 0.01


def load():
    m = pd.read_csv(INTERIM / "municipios.csv", dtype={"ine": str})
    m = m.dropna(subset=["serpavi_med_2022", "serpavi_p25_2022", "serpavi_p75_2022", "renta_pc_2022",
                         "pct_alquiler_2021", "paro25_por_1000_15_24", "pob_total_2022", "jovenes_20_34_2022"]).copy()
    m["log_rent"] = np.log(m["serpavi_med_2022"])
    m["log_income"] = np.log(m["renta_pc_2022"])
    m["log_pop"] = np.log(m["pob_total_2022"])
    m["pop_tercile"] = pd.qcut(m["pob_total_2022"], 3, labels=False)
    return m.reset_index(drop=True)


def shares(m, caps, year=2022):
    return np.array([share_above(c, a, z) for c, a, z in zip(caps, m[f"serpavi_p25_{year}"], m[f"serpavi_p75_{year}"])])


def fit(m, y, share, exposure="jovenes_20_34_2022", family="poisson", controls=CONTROLS, extra=None):
    X = m[controls] if share is None else m[controls].assign(share=share)
    if extra is not None:
        X = X.assign(**extra)
    X = sm.add_constant(X)
    off = np.log(m[exposure].to_numpy(float))
    if family == "poisson":
        return sm.GLM(m[y].to_numpy(float), X, family=sm.families.Poisson(), offset=off).fit(cov_type="HC1")
    return sm.NegativeBinomial(m[y].to_numpy(float), X, offset=off).fit(disp=0, maxiter=200)


def permutation_p(m, y, beta_obs, n_perm, rng):
    """One-sided p: share of draws with beta <= observed, permuting the 900 label within population terciles."""
    caps = m["cap"].to_numpy()
    betas = []
    for _ in range(n_perm):
        perm = caps.copy()
        for t in np.unique(m["pop_tercile"]):
            idx = np.flatnonzero(m["pop_tercile"].to_numpy() == t)
            perm[idx] = rng.permutation(caps[idx])
        betas.append(fit(m, y, shares(m, perm)).params["share"])
    return (1 + np.sum(np.array(betas) <= beta_obs)) / (1 + n_perm)


def h1(m, y, n_perm, rng):
    r = fit(m, y, m["share_above_cap_2022"])
    b, (lo, hi) = r.params["share"], r.conf_int().loc["share"]
    p_perm = permutation_p(m, y, b, n_perm, rng)
    nm = m[m["ine"] != MADRID]
    b_nm = fit(nm, y, nm["share_above_cap_2022"]).params["share"]
    ok = bool(b < 0 and hi < 0 and p_perm < P_THRESHOLD and b_nm < 0)
    return {"beta": b, "ci95": [lo, hi], "pct_per_10_points": 100 * (np.exp(0.1 * b) - 1), "p_perm": p_perm,
            "beta_without_madrid": b_nm, "H1_confirmed": ok}


def full_test(m, y="bono_solicitudes", y_rep="ayudas51_solicitudes", n_perm=2000, seed=7):
    rng = np.random.default_rng(seed)
    out = {"n_municipalities": len(m), "by_cap": m.groupby("cap").size().to_dict(), "H1": h1(m, y, n_perm, rng)}
    # H2: common rent range of both cap groups, computed on every municipality of the model (amendment of 2-Nov)
    lo = m.groupby("cap")["serpavi_med_2022"].min().max()
    hi = m.groupby("cap")["serpavi_med_2022"].max().min()
    c = m[m["serpavi_med_2022"].between(lo, hi)]
    r2 = fit(c, y, None, extra={"cap600": (c["cap"] == 600).astype(float)})
    out["H2"] = {"rent_range": [lo, hi], "n": c.groupby("cap").size().to_dict(),
                 "rate_ratio_cap600": float(np.exp(r2.params["cap600"])),
                 "ci95": np.exp(r2.conf_int().loc["cap600"]).tolist()}
    rr = fit(m, y_rep, m["share_above_cap_2022"])
    out["R1_ayudas51"] = {"beta": rr.params["share"], "ci95": rr.conf_int().loc["share"].tolist()}
    out["fake_caps_deviance"] = {k: fit(m, y, m[col]).deviance for k, col in
                                 [("real_cap", "share_above_cap_2022"), ("uniform_600", "share_above_600_2022"),
                                  ("uniform_900", "share_above_900_2022")]}
    rob = {"negative_binomial": fit(m, y, m["share_above_cap_2022"], family="nb").params["share"],
           "per_rented_household": fit(m, y, m["share_above_cap_2022"], exposure="hogares_alquiler_2021").params["share"]}
    m23 = m.dropna(subset=["share_above_cap_2023"])
    rob["serpavi_2023"] = fit(m23, y, m23["share_above_cap_2023"]).params["share"]
    big = m.dropna(subset=["alq_medio_portal_2023"]).assign(log_rent=lambda d: np.log(d["alq_medio_portal_2023"]))
    rob["portal_rent_over_20k"] = {"n": len(big), "beta": fit(big, y, big["share_above_cap_2022"]).params["share"]}
    keep = m[m["jovenes_20_34_2022"] >= 1000]
    rob["young_at_least_1000"] = {"n": len(keep), "beta": fit(keep, y, keep["share_above_cap_2022"]).params["share"]}
    out["robustness_beta"] = rob
    return out


def synthetic(m, beta, noise_sd, rng):
    """Invented request counts from known coefficients, scaled to ~48,000 requests like the real call."""
    gamma = {"log_rent": 0.0, "log_income": -0.5, "pct_alquiler_2021": 0.02, "paro25_por_1000_15_24": 0.002, "log_pop": 0.1}
    eta = beta * m["share_above_cap_2022"] + sum(g * m[k] for k, g in gamma.items()) + rng.normal(0, noise_sd, len(m))
    rate = np.exp(eta)
    rate *= 48000 / np.sum(rate * m["jovenes_20_34_2022"])
    return rng.poisson(rate * m["jovenes_20_34_2022"])


def power(m, sims, n_perm, betas=(0.0, -0.5, -1.1), seed=11):
    """Share of invented datasets where H1 passes; keeps every simulation so other thresholds can be checked later."""
    rng = np.random.default_rng(seed)
    rows, detail = [], []
    for noise_sd in (0.2, 0.4):
        for beta in betas:
            res = [h1(m.assign(y_fake=synthetic(m, beta, noise_sd, rng)), "y_fake", n_perm, rng) for _ in range(sims)]
            detail += [{"noise_sd": noise_sd, "planted_beta": beta, **r} for r in res]
            rows.append({"noise_sd": noise_sd, "planted_beta": beta, "pct_per_10_points": round(100 * (np.exp(0.1 * beta) - 1), 1),
                         "H1_confirmed_share": float(np.mean([r["H1_confirmed"] for r in res])),
                         "mean_beta_recovered": float(np.mean([r["beta"] for r in res]))})
            print(rows[-1], flush=True)
    return rows, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sintetico", action="store_true")
    ap.add_argument("--sims", type=int, default=100)
    ap.add_argument("--perm", type=int, default=199)
    ap.add_argument("--betas", type=float, nargs="+", default=[0.0, -0.5, -1.1])
    ap.add_argument("--sin-ensayo", action="store_true", help="skip the end-to-end dry run, only power")
    args = ap.parse_args()
    m = load()
    out_dir = ROOT / "resultados"
    out_dir.mkdir(exist_ok=True)
    if args.sintetico:
        rng = np.random.default_rng(3)
        # 1) every block of the real test runs end to end on one invented dataset with a planted effect
        dry = None
        if not args.sin_ensayo:
            mm = m.assign(bono_solicitudes=synthetic(m, -1.1, 0.3, rng), ayudas51_solicitudes=synthetic(m, -1.1, 0.3, rng))
            dry = full_test(mm, n_perm=99)
            print(json.dumps(dry, indent=1, default=float))
        # 2) power of the three H1 conditions together (every simulation kept in the JSON)
        pw, detail = power(m, args.sims, args.perm, tuple(args.betas))
        name = f"potencia_sintetica_{args.sims}x{args.perm}.json"
        (out_dir / name).write_text(json.dumps({"dry_run": dry, "power": pw, "simulations": detail}, indent=1, default=float),
                                    encoding="utf-8")
        return
    if datetime.date.today() < START:
        sys.exit(f"Real test blocked until {START} (development period; see PREREGISTRO.md). Use --sintetico.")
    res = full_test(m)
    print(json.dumps(res, indent=1, default=float))
    (out_dir / "contraste_real.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()

"""EXPLORATORY placebo (not pre-registered; written 15-Nov-2026 BEFORE running it, in commit 5a970aa at 23:32; expectations below).

Why: in the exploratory model with the real-cap share and the uniform-900 share together (exploratorio_topes_falsos.py),
the real cap only differs from the 900 threshold in the 600-EUR-cap municipalities, by the share of rents between 600
and 900 EUR. So the -5.3 % "part of the cap" rests on that band. A rent level that deters by itself would deter in the
900-EUR-cap municipalities too, where the same band is BELOW the cap (eligible). This script asks that directly:
  M1 controls + share above 900 + band x cap600 + band x cap900   (band = share of rents between 600 and 900 EUR)

Expected (written before running):
  - If the cap is what deters: band x cap600 < 0 with an interval that does not touch 0 (about -0.5, as the joint model),
    band x cap900 close to 0, and the difference (cap600 - cap900) < 0.
  - Against the cap: band x cap900 as negative as band x cap600 (difference interval around 0, band x cap900 < 0).
  - Most likely, with only 29 municipalities at 900 EUR: band x cap900 with a wide interval, so the answer will be
    "consistent with the cap, not precise". Whatever comes out is published, as with the rest.

Correction (15-Nov-2026, 23:48, after round 2 of the statistical jury rehearsal, so AFTER seeing the first result):
the first version had no effect of its own for the 600-EUR-cap municipalities, so the gap between the two slopes also
picked up that the 29 municipalities at 900 EUR (the metropolitan area) apply more for other reasons. An interaction goes
with its main effects. Corrected model, also in the common rent range of H2 (the test is band x cap600 < 0; band alone is
the placebo slope, where the band is below the cap):
  M1 controls + share above 900 + cap600 + band + band x cap600
The joint model of exploratorio_topes_falsos.py is refitted with cap600 as well. Both versions stay in the JSON.
Usage:  python -P scripts/placebo_franja.py   -> resultados/placebo_franja.json
"""
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT  # noqa: E402
from contraste import MADRID, fit, load  # noqa: E402

Y = "bono_solicitudes"


def pct(b):
    return round(100 * (np.exp(0.1 * b) - 1), 2)


def term(r, k):
    lo, hi = r.conf_int().loc[k]
    return {"beta": r.params[k], "ci95": [lo, hi], "pct_per_10_points": pct(r.params[k]), "pct_ci95": [pct(lo), pct(hi)]}


def parts(m):
    return (m["share_above_600_2022"] - m["share_above_900_2022"]).to_numpy(float), (m["cap"] == 600).to_numpy(float)


def first_version(m):
    """As written in 5a970aa: two slopes, no effect of its own for the 600-EUR group (mis-specified, kept for the record)."""
    band, cap600 = parts(m)
    r = fit(m, Y, None, extra={"share_900": m["share_above_900_2022"], "band_cap600": band * cap600,
                               "band_cap900": band * (1 - cap600)})
    out = {"n": {"cap600": int(cap600.sum()), "cap900": int((1 - cap600).sum())},
           "band_mean": {"cap600": round(float(band[cap600 == 1].mean()), 3), "cap900": round(float(band[cap600 == 0].mean()), 3)}}
    for k in ("band_cap600", "band_cap900", "share_900"):
        out[k] = term(r, k)
    cov = r.cov_params()
    d = r.params["band_cap600"] - r.params["band_cap900"]
    se = float(np.sqrt(cov.loc["band_cap600", "band_cap600"] + cov.loc["band_cap900", "band_cap900"]
                       - 2 * cov.loc["band_cap600", "band_cap900"]))
    out["difference_cap600_minus_cap900"] = {"beta": d, "ci95": [d - 1.96 * se, d + 1.96 * se], "z": d / se,
                                             "pct_per_10_points": pct(d), "pct_ci95": [pct(d - 1.96 * se), pct(d + 1.96 * se)]}
    out["deviance"] = r.deviance
    return out


def corrected(m):
    band, cap600 = parts(m)
    r = fit(m, Y, None, extra={"share_900": m["share_above_900_2022"], "cap600": cap600, "band": band,
                               "band_x_cap600": band * cap600})
    out = {"n": {"cap600": int(cap600.sum()), "cap900": int((1 - cap600).sum())},
           "band_x_cap600": term(r, "band_x_cap600"), "band_where_below_cap": term(r, "band"),
           "cap600_rate_ratio": float(np.exp(r.params["cap600"])), "deviance": r.deviance}
    return out


def joint_with_cap600(m):
    band, cap600 = parts(m)
    r = fit(m, Y, m["share_above_cap_2022"], extra={"share_900": m["share_above_900_2022"], "cap600": cap600})
    return {"real_cap": term(r, "share"), "uniform_900": term(r, "share_900"),
            "cap600_rate_ratio": float(np.exp(r.params["cap600"])),
            "cap600_rate_ratio_ci95": np.exp(r.conf_int().loc["cap600"]).tolist(), "deviance": r.deviance}


def main():
    m = load()
    nm = m[m["ine"] != MADRID].reset_index(drop=True)
    lo = m.groupby("cap")["serpavi_med_2022"].min().max()
    hi = m.groupby("cap")["serpavi_med_2022"].max().min()
    h2 = m[m["serpavi_med_2022"].between(lo, hi)].reset_index(drop=True)
    out = {"note": "EXPLORATORIO: placebo de la franja de 600 a 900 €. Lo esperado, escrito antes (5a970aa); la corrección, "
                   "posterior (falta el efecto propio de los municipios con tope de 600 € en la primera versión)",
           "corrected": {"all": corrected(m), "without_madrid": corrected(nm),
                         "h2_rent_range": {"rent_range": [lo, hi], **corrected(h2)}},
           "joint_model_with_cap600": joint_with_cap600(m),
           "first_version_without_group_effect": {"all": first_version(m), "without_madrid": first_version(nm)}}
    text = json.dumps(out, indent=1, default=float)
    print(text)
    (ROOT / "resultados" / "placebo_franja.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

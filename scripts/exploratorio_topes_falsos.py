"""EXPLORATORY (not pre-registered; written 7-Nov-2026 AFTER seeing contraste_real.json).

The pre-registered fake-cap check came out against the cap mechanism: a uniform 600 or 900 EUR threshold fits better
(lower deviance) than each municipality's real cap. This script only describes that result, it changes no rule:
  1. M1 with no share variable (controls only), as a reference deviance
  2. M1 with each share variable alone: beta, HC1 interval, deviance
  3. M1 with the real-cap share and the uniform-900 share together: does the real cap add anything?
Usage:  python -P scripts/exploratorio_topes_falsos.py   -> resultados/exploratorio_topes_falsos.json
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT  # noqa: E402
from contraste import fit, load  # noqa: E402

Y = "bono_solicitudes"
SHARES = {"real_cap": "share_above_cap_2022", "uniform_600": "share_above_600_2022", "uniform_900": "share_above_900_2022"}


def coef(r, name):
    lo, hi = r.conf_int().loc[name]
    return {"beta": r.params[name], "ci95": [lo, hi]}


def main():
    m = load()
    out = {"note": "EXPLORATORIO: no preregistrado, hecho tras ver el contraste real",
           "controls_only_deviance": fit(m, Y, None).deviance}
    for k, col in SHARES.items():
        r = fit(m, Y, m[col])
        out[k] = {**coef(r, "share"), "deviance": r.deviance}
    r = fit(m, Y, m[SHARES["real_cap"]], extra={"share_900": m[SHARES["uniform_900"]]})
    out["real_cap_and_uniform_900"] = {"real_cap": coef(r, "share"), "uniform_900": coef(r, "share_900"),
                                       "deviance": r.deviance}
    out["corr_shares"] = m[list(SHARES.values())].corr().round(3).to_dict()
    text = json.dumps(out, indent=1, default=float)
    print(text)
    (ROOT / "resultados" / "exploratorio_topes_falsos.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

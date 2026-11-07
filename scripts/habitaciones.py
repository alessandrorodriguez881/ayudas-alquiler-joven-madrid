"""EXPLORATORY (not pre-registered; written 7-Nov-2026 AFTER the real test): the room caps.

Rules: Acuerdo of 14-Sep-2022, art. 5 (read in the PDF): rent <= 600 EUR for a flat and <= 300 EUR for a room, 900 / 450 EUR
in the municipalities of Annex II (the same in the Bono 2024, BDNS 805618). Plan 2026-2030 (RD 326/2026, art. 133.1.e):
1,000 / 600 EUR, and 500 / 250 EUR in municipalities of 10,000 people or fewer. Young people sharing a flat on one contract:
the whole rent must fit the flat cap (art. 5), each with own income <= 3 x IPREM (art. 4.1.d), 250 EUR each up to the rent
(art. 8). On a room contract only the room rent and the applicant's income count.
No open data gives room rents by municipality (SERPAVI covers whole dwellings; the Bono data does not split flat / room).
Proxy: a room in a flat shared by n young people costs the whole-flat rent / n (no bills and no premium for renting by
rooms, so it is the optimistic case), with the same log-normal SERPAVI fit as the test. n sharers then fit the Bono when
the flat rent <= max(flat cap, n x room cap): one contract, or n room contracts.
  1. Rule arithmetic: the flat rent up to which n sharers fit (n = 2, 3), and each room cap against the highest income
  2. Share of the rental market above the cap (2024 rents, weighted by young people): one tenant or couple (flat cap)
     and 2 or 3 sharers (best route), for the current caps, the Plan and the proposal (room cap = 60 % of the flat cap,
     the Plan's ratio for 1,000 / 600 EUR), by need group and for municipalities of 10,000 people or fewer
  3. Does H1 hold if part of the young rent rooms? Exposure = (1 - w) x flat share + w x share above 1.5 x cap (3 sharers
     on room contracts), w = 0 ... 1. Written before running: beta < 0 for every w; if rooms are why a uniform 900 EUR fits
     better than the real cap (exploratorio_topes_falsos.json), the w = 1 share (900 EUR outside Annex II, 1,350 EUR in it)
     should fit about as well as the uniform 900 EUR share
     Added after the first run, because w = 1 fitted best of all (deviance 805, against 966 and 1,023): a uniform 1,350 EUR
     share; the same permutation as the test (Annex II label shuffled within population terciles), to see whether the real
     900 / 1,350 split fits better than shuffled ones; w = 1 next to the uniform 1,350 EUR share (like the -0.54 of the
     flat cap), without Madrid city and with a negative binomial
Usage:  python -P scripts/habitaciones.py   (after requisito_ingresos.py)  -> resultados/habitaciones.json
"""
import json
import pathlib
import sys

import numpy as np
import statsmodels.api as sm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT, share_above  # noqa: E402
import contraste  # noqa: E402
import simulador  # noqa: E402

ROOM_RATIO_PROPOSAL = 0.6  # proposal: room cap = 60 % of the flat cap, like the Plan's 600 EUR for 1,000 EUR
MAX_INCOME_MONTH_2024 = 3 * 14 * 600.0 / 12  # 3 x IPREM of 14 payments (2024), spread over 12 months
SHARERS = (2, 3)


def arithmetic():
    caps = {"actual_general": (600, 300), "actual_anexo_II": (900, 450),
            "plan_mas_de_10000_hab": (1000, 600), "plan_10000_hab_o_menos": (500, 250)}
    return {k: {"flat_cap": f, "room_cap": r,
                **{f"max_flat_rent_{n}_sharers_one_contract": f for n in SHARERS},
                **{f"max_flat_rent_{n}_sharers_room_contracts": n * r for n in SHARERS},
                "room_cap_over_max_income_pct": round(100 * r / MAX_INCOME_MONTH_2024, 1)}
            for k, (f, r) in caps.items()}


def caps_by_rule(s):
    """(flat cap, room cap) per municipality and rule, EUR/month."""
    small = s["pob_total_2024"].to_numpy() <= 10000
    now = s["tope_2024"].to_numpy(float)
    prop = simulador.rules(s)["necesidad_requisito_plan_p75_hasta_1000"][0]
    return {"actual_2024_55": (now, now / 2),
            "plan_estatal": (simulador.plan_cap(s), np.where(small, 250.0, 600.0)),
            "propuesta_p75_hasta_1000": (prop, np.round(ROOM_RATIO_PROPOSAL * prop / 50) * 50)}


def above(caps, p25, p75):
    return np.array([share_above(c, a, z) for c, a, z in zip(caps, p25, p75)])


def market(s):
    young = s["jovenes_20_34_2024"].to_numpy(float)
    groups = {"todos": np.ones(len(s), bool), "municipios_10000_hab_o_menos": s["pob_total_2024"].to_numpy() <= 10000,
              **{g: (s["grupo_necesidad"] == g).to_numpy() for g in sorted(s["grupo_necesidad"].unique())}}
    out = {"young_by_group": {g: round(float(young[k].sum())) for g, k in groups.items()}}
    for rule, (flat, room) in caps_by_rule(s).items():
        limits = {"one_tenant_or_couple": flat, **{f"{n}_sharers_best_route": np.maximum(flat, n * room) for n in SHARERS}}
        res = {}
        for who, lim in limits.items():
            sh = above(lim, s["serpavi_p25_2024"], s["serpavi_p75_2024"])
            res[who] = {g: round(float(np.average(sh[k], weights=young[k])), 3) for g, k in groups.items()}
        out[rule] = {"room_cap_range": [float(room.min()), float(room.max())], "share_above": res}
    return out


def negative_binomial(m, y, share):
    """contraste.fit's negative binomial with Nelder-Mead: its default optimizer stops short on the room-route share."""
    X = sm.add_constant(m[contraste.CONTROLS].assign(share=share))
    off = np.log(m["jovenes_20_34_2022"].to_numpy(float))
    return sm.NegativeBinomial(m[y].to_numpy(float), X, offset=off).fit(disp=0, maxiter=5000, method="nm")


def robustness(n_perm=2000):
    m = contraste.load()
    y, cap = "bono_solicitudes", m["cap"].to_numpy(float)
    flat, room3 = m["share_above_cap_2022"].to_numpy(), contraste.shares(m, 1.5 * cap)
    # outside Annex II, 3 sharers on room contracts fit up to 900 EUR: the same share as the uniform 900 EUR one
    assert np.allclose(room3[cap == 600], m.loc[cap == 600, "share_above_900_2022"])
    pct = lambda b: round(100 * (np.exp(0.1 * b) - 1), 2)  # noqa: E731

    def one(share):
        r = contraste.fit(m, y, share)
        b, (lo, hi) = float(r.params["share"]), r.conf_int().loc["share"]
        return {"beta": b, "ci95": [float(lo), float(hi)], "pct_per_10_points": pct(b), "deviance": float(r.deviance)}

    out = {"n_municipalities": len(m), "real_cap": one(flat), "uniform_900": one(m["share_above_900_2022"])}
    out["mix_flat_and_3_sharers_rooms"] = {str(w): one((1 - w) * flat + w * room3) for w in (0.25, 0.5, 0.75, 1.0)}
    out["all_beta_negative"] = all(v["beta"] < 0 for v in out["mix_flat_and_3_sharers_rooms"].values())
    # checks added after the first run (see docstring)
    out["uniform_1350"] = one(contraste.shares(m, np.full(len(m), 1350.0)))
    rng, terc, dev = np.random.default_rng(7), m["pop_tercile"].to_numpy(), out["mix_flat_and_3_sharers_rooms"]["1.0"]["deviance"]
    perm_dev = []
    for _ in range(n_perm):
        perm = cap.copy()
        for t in np.unique(terc):
            idx = np.flatnonzero(terc == t)
            perm[idx] = rng.permutation(cap[idx])
        perm_dev.append(contraste.fit(m, y, contraste.shares(m, 1.5 * perm)).deviance)
    perm_dev = np.array(perm_dev)
    out["w1_permutation_annex_label"] = {"n_perm": n_perm, "p_deviance_as_low": float((1 + np.sum(perm_dev <= dev)) / (1 + n_perm)),
                                         "median_deviance_shuffled": float(np.median(perm_dev)),
                                         "min_deviance_shuffled": float(perm_dev.min())}
    nm = m["ine"] != contraste.MADRID
    b_nm = contraste.fit(m[nm], y, room3[nm.to_numpy()]).params["share"]
    out["w1_without_madrid"] = {"beta": float(b_nm), "pct_per_10_points": pct(b_nm)}
    out["negative_binomial"] = {}
    for name, share in (("real_cap", flat), ("w1", room3)):
        nb = negative_binomial(m, y, share)
        out["negative_binomial"][name] = {"beta": float(nb.params["share"]), "pct_per_10_points": pct(nb.params["share"]),
                                          "log_likelihood": float(nb.llf), "converged": bool(nb.mle_retvals["converged"])}
    # like the -0.54 of the flat cap: what the room-route share adds next to a uniform threshold at the same height
    r = contraste.fit(m, y, room3, extra={"share_1350": contraste.shares(m, np.full(len(m), 1350.0))})
    out["w1_and_uniform_1350"] = {"w1": {"beta": float(r.params["share"]), "ci95": [float(v) for v in r.conf_int().loc["share"]]},
                                  "uniform_1350": {"beta": float(r.params["share_1350"]),
                                                   "ci95": [float(v) for v in r.conf_int().loc["share_1350"]]},
                                  "deviance": float(r.deviance)}
    return out


def main():
    s, _ = simulador.load()
    s["grupo_necesidad"] = simulador.need_groups(s)
    out = {"note": "EXPLORATORIO: no preregistrado, hecho tras el contraste real. Habitación = alquiler del piso / n "
                   "(sin gastos ni sobreprecio por alquilar por habitaciones): caso optimista; ver docstring",
           "rule_arithmetic": arithmetic(), "market_above_cap_2024": market(s),
           "h1_with_room_contracts": robustness()}
    text = json.dumps(out, indent=1, ensure_ascii=False, default=float)
    (ROOT / "resultados" / "habitaciones.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

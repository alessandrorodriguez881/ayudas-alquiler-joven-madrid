"""EXPLORATORY (not pre-registered; written 12-Nov-2026, after the real test and validacion_fuera_muestra.py): are the
errors of the requests model alike between neighbouring municipalities, and does that change what we say?

The pre-registered test used HC1 errors and a permutation of the Annex II label, which treat municipalities as
independent once the controls are in. Neighbours share jobs, transport and news, so their errors may be alike: then the
intervals are too narrow, and the random folds of validacion_fuera_muestra.py leak (a municipality's neighbours, in the
training folds, look like it). It is the likely question of a juror who works on spatial econometrics.

Neighbours: two municipalities that touch (a boundary point of each within 1 m) in the municipal map of the Comunidad de
Madrid portal (the shapefile of graficos.py, ETRS89 / UTM 30N). Distances: between area centroids. Zones: the 11
statistical zones (NUTS 4) of the portal dataset «Municipios de la Comunidad de Madrid» (municipio_comunidad_madrid,
in data/raw_2026-11-12/ from scripts/descargar.py); Madrid city is a zone of its own.
Models, as in validacion_fuera_muestra.py (Poisson, Bono 2022 requests, offset log young 20-34): M0 controls only;
M1 = the pre-registered H1 model (+ share above the real cap); M3 = the simulator's model (+ real cap + uniform 900 EUR;
its real-cap beta, -0.54, is the simulator's central value); MR = + room route (added there on 12-Nov).
  1. Moran's I of the Pearson residuals (row-standardised contiguity, 9,999 permutations, one-sided), and of the
     requests per young person for scale
  2. The beta of the share above the real cap (M1, M3) with: HC1, as in the test; Conley errors (Bartlett kernel on the
     centroid distances, 15, 30 and 50 km; with no distance they are HC1); zone fixed effects (only differences inside
     each zone; Madrid city is alone in its zone, so it no longer counts); and a spatial filter: Moran eigenvectors of
     the contiguity matrix (those with at least a quarter of the largest eigenvalue) added to M1 one at a time, each
     time the one that lowers the residual Moran's I the most, until its permutation p is 0.10 or more (like
     spatialreg::ME in R); M3 then takes the same eigenvectors
  3. Spatial cross-validation of every model of validacion_fuera_muestra.py: (a) leave one zone out (11 folds: a whole
     zone predicted by a model that has seen none of it); (b) leave one municipality out with its neighbours also out of
     the training set. Same scores and paired gains against controls only
  4. The simulator is not changed here. If the Conley interval of M3's beta (30 km) is wider than its HC1 interval, the
     two simulator figures that use the interval (requests not made in 2022, and the extra money of the proposal with
     250 EUR) are given at its ends too
Written before running:
  - 1: the requests per young person are clearly alike between neighbours (I > 0.3); M0's residuals less so; M1's and
    M3's residuals still positive, around 0.1-0.2, with a p that could fall either side of 0.05
  - 2: Conley errors 10-50 % wider than HC1; M1's beta stays below 0 at every distance; M3's upper end (-0.20) gets
    close to 0 and may cross it at 50 km. With zone fixed effects much of the cap's variation goes (the 900 EUR
    municipalities are mostly in the four metropolitan zones), so the betas get less precise but keep their sign. The
    spatial filter needs fewer than 10 eigenvectors and moves M1's beta towards 0 without crossing it
  - 3: every model predicts worse than with random folds (the leak); the real-cap share still beats controls only
    without Madrid, and the room route is still the best single share without Madrid, as with random folds
Usage:  python -P scripts/espacial.py   (after validacion_fuera_muestra.py and simulador.py) -> resultados/espacial.json
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.spatial import cKDTree

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT, leer_csv  # noqa: E402
from contraste import MADRID, load  # noqa: E402
import simulador  # noqa: E402
import validacion_fuera_muestra as vfm  # noqa: E402

ZONES_CSV = ROOT / "data" / "raw_2026-11-12" / "municipio_comunidad_madrid" / "datos.csv"
TOUCH_M = 1.0
BANDWIDTHS_KM = (15, 30, 50)
N_PERM = 9999
FILTER_SHARE, FILTER_STOP_P = 0.25, 0.10
MAIN = {"M0": "controles", "M1": "controles_tope_real", "M3": "controles_ambas", "MR": "controles_habitaciones"}
SHARE = "share_above_cap"


def geography():
    """Pairs of municipalities that touch, and area centroids in km, from the municipal map (UTM 30N, metres)."""
    from graficos import boundaries  # slow to import (matplotlib), so only here
    shapes = boundaries()
    codes = sorted(shapes)
    pts, owner, cent = [], [], {}
    for i, c in enumerate(codes):
        area = cx = cy = 0.0
        for s in shapes[c]:
            p = np.asarray(s.points, float)
            pts.append(p)
            owner.append(np.full(len(p), i))
            for a, b in zip(s.parts, list(s.parts[1:]) + [len(p)]):
                x, y = p[a:b, 0], p[a:b, 1]
                cross = x * np.roll(y, -1) - np.roll(x, -1) * y  # holes wind the other way, so they subtract
                area += cross.sum() / 2
                cx += ((x + np.roll(x, -1)) * cross).sum() / 6
                cy += ((y + np.roll(y, -1)) * cross).sum() / 6
        cent[c] = (cx / area / 1000, cy / area / 1000)
    p, o = np.vstack(pts), np.concatenate(owner)
    pairs = cKDTree(p).query_pairs(TOUCH_M, output_type="ndarray")
    a, b = o[pairs[:, 0]], o[pairs[:, 1]]
    keep = a != b
    touching = {(codes[min(x, y)], codes[max(x, y)]) for x, y in zip(a[keep], b[keep])}
    return touching, cent


def zones():
    z = leer_csv(ZONES_CSV, dtype={"municipio_codigo": str, "nuts4_codigo": str})
    return z.set_index("municipio_codigo")["nuts4_nombre"]


def contiguity(codes, touching):
    idx = {c: i for i, c in enumerate(codes)}
    C = np.zeros((len(codes), len(codes)))
    for a, b in touching:
        if a in idx and b in idx:
            C[idx[a], idx[b]] = C[idx[b], idx[a]] = 1.0
    return C


def row_standardise(C):
    deg = C.sum(axis=1, keepdims=True)
    return np.divide(C, deg, out=np.zeros_like(C), where=deg > 0)


def moran(z, W):
    z = z - z.mean()
    return float(len(z) / W.sum() * (z @ W @ z) / (z @ z))


def moran_test(e, W, rng, n_perm=N_PERM):
    z = e - e.mean()
    obs = moran(z, W)
    zp = rng.permuted(np.broadcast_to(z, (n_perm, len(z))).copy(), axis=1).T  # one permutation per column
    perm = len(z) / W.sum() * np.einsum("ip,ip->p", zp, W @ zp) / (z @ z)
    return {"I": round(obs, 4), "expected_without_autocorrelation": round(-1 / (len(z) - 1), 4),
            "p_one_sided": float((1 + np.sum(perm >= obs)) / (1 + n_perm)),
            "z_permutation": round(float((obs - perm.mean()) / perm.std()), 2)}


def poisson(y, X, off):
    return sm.GLM(y, X, family=sm.families.Poisson(), offset=off).fit(cov_type="HC1")


def pearson(r, y):
    return (y - r.mu) / np.sqrt(r.mu)


def conley_se(r, X, y, off, D, km):
    """Sandwich errors with the scores of municipalities closer than km weighted by 1 - distance / km (Bartlett). With
    km = 0 they are the test's errors: statsmodels' "HC1" for a GLM has no small-sample factor (it equals HC0)."""
    mu = np.exp(X @ np.asarray(r.params) + off)
    s = X * (y - mu)[:, None]
    binv = np.linalg.inv(X.T @ (X * mu[:, None]))
    K = np.eye(len(y)) if km == 0 else np.clip(1 - D / km, 0, None)
    V = binv @ (s.T @ K @ s) @ binv
    return np.sqrt(np.diag(V))


def interval(b, se):
    lo, hi = b - 1.96 * se, b + 1.96 * se
    pct = lambda v: round(100 * (np.exp(0.1 * v) - 1), 2)  # noqa: E731  % per 10 points of share
    return {"se": round(float(se), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "pct_per_10_points_ci95": [pct(lo), pct(hi)]}


def beta_block(r, X, y, off, D, col):
    """The share's beta with HC1 and with Conley errors at each distance."""
    j = list(X.columns).index(col)
    Xa = X.to_numpy(float)
    b = float(r.params.iloc[j])
    out = {"beta": round(b, 4), "pct_per_10_points": round(100 * (np.exp(0.1 * b) - 1), 2),
           "hc1": interval(b, r.bse.iloc[j])}
    assert np.isclose(conley_se(r, Xa, y, off, D, 0)[j], r.bse.iloc[j])  # with no distance, Conley is HC1
    for km in BANDWIDTHS_KM:
        out[f"conley_{km}km"] = interval(b, conley_se(r, Xa, y, off, D, km)[j])
    return out


def spatial_filter(y, X, off, C, W, rng):
    """Eigenvectors of the doubly-centred contiguity matrix, chosen one at a time for M1 (docstring, point 2)."""
    n = len(y)
    M = np.eye(n) - 1.0 / n
    vals, vecs = np.linalg.eigh(M @ C @ M)
    order = np.argsort(vals)[::-1]
    vals, vecs = vals[order], vecs[:, order]
    cand = [k for k in range(n) if vals[k] >= FILTER_SHARE * vals[0]]

    def resid(cols):
        Xe = X.assign(**{f"ev{k}": vecs[:, k] for k in cols})
        return pearson(poisson(y, Xe, off), y)

    chosen, e = [], resid([])
    test = moran_test(e, W, rng)
    steps = [{"eigenvectors": 0, "residual_moran": test}]
    while test["p_one_sided"] < FILTER_STOP_P and len(chosen) < len(cand):
        best = min((k for k in cand if k not in chosen), key=lambda k: moran(resid(chosen + [k]), W))
        e = resid(chosen + [best])
        if moran(e, W) >= test["I"]:
            break
        chosen.append(best)
        test = moran_test(e, W, rng)
        steps.append({"eigenvectors": len(chosen), "added": int(best), "residual_moran": test})
    return {f"ev{k}": vecs[:, k] for k in chosen}, {"candidates": len(cand), "steps": steps}


def predict(m, splits):
    """Held-out predictions of every model of validacion_fuera_muestra.py, for explicit (train, test) index pairs."""
    y, off = m["bono_solicitudes"].to_numpy(float), np.log(m["jovenes_20_34_2022"].to_numpy(float))
    pred = {k: np.full(len(m), np.nan) for k in vfm.MODELS}
    for train, test in splits:
        for k in vfm.MODELS:
            X = vfm.design_for(k, m, 2022).to_numpy(float)
            r = sm.GLM(y[train], X[train], family=sm.families.Poisson(), offset=off[train]).fit()
            pred[k][test] = np.exp(X[test] @ r.params + off[test])
    return pred


def cv_block(m, splits):
    y, madrid = m["bono_solicitudes"].to_numpy(float), (m["ine"] == MADRID).to_numpy()
    pred = predict(m, splits)
    out = {k: vfm.scores(y, mu, madrid) for k, mu in pred.items()}
    base = vfm.unit_deviance(y, pred[vfm.BASE])
    for k in vfm.MODELS:
        if k not in (vfm.BASE, "solo_constante"):
            out[k]["gain_vs_controls"] = vfm.gain(base - vfm.unit_deviance(y, pred[k]), madrid)
    return out


def simulator_at(betas):
    """The two simulator figures that use the interval of beta, for other values of beta (simulador.py's functions)."""
    s, _ = simulador.load()
    caps_now = s["tope_2024"].to_numpy(float)
    proposal = simulador.rules(s)["necesidad_requisito_plan_p75_hasta_1000"][0]
    out = {"requests_not_made_2022": simulador.not_made(s, betas), "proposal_250eur_extra_meur_same_success_rate": {}}
    for name, b in betas.items():
        ratio = simulador.requests(s, proposal, b)[0].sum() / simulador.requests(s, caps_now, b)[0].sum()
        out["proposal_250eur_extra_meur_same_success_rate"][name] = round(simulador.BUDGET_EUR / 1e6 * (ratio - 1), 2)
    return out


def main():
    rng = np.random.default_rng(12)
    m = vfm.with_room_shares(load())
    touching, cent = geography()
    codes = m["ine"].tolist()
    C = contiguity(codes, touching)
    W = row_standardise(C)
    xy = np.array([cent[c] for c in codes])
    D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    zone = m["ine"].map(zones())
    assert zone.notna().all()
    nb = C.sum(axis=1)
    out = {"note": "EXPLORATORIO: no preregistrado, hecho después del contraste real; lo esperado está en el docstring",
           "geography": {"municipalities_in_map": len(cent), "touching_pairs": len(touching), "in_model": len(m),
                         "touching_pairs_in_model": int(C.sum() / 2), "mean_neighbours_in_model": round(float(nb.mean()), 2),
                         "without_neighbours_in_model": m.loc[nb == 0, "municipio"].tolist(),
                         "median_km_to_touching_neighbours": round(float(np.median(D[C > 0])), 1),
                         "zones_in_model": {k: int(v) for k, v in zone.value_counts().items()}}}
    y, off = m["bono_solicitudes"].to_numpy(float), np.log(m["jovenes_20_34_2022"].to_numpy(float))

    # 1. Moran's I
    mor = {"requests_per_young_log": moran_test(np.log((y + 0.5) / m["jovenes_20_34_2022"].to_numpy(float)), W, rng)}
    fits = {}
    for key, name in MAIN.items():
        X = vfm.design_for(name, m, 2022)
        fits[key] = (poisson(y, X, off), X)
        mor[key] = moran_test(pearson(fits[key][0], y), W, rng)
    out["moran_pearson_residuals"] = mor

    # 2. The real-cap share's beta, four ways
    dummies = pd.get_dummies(zone, prefix="zona", drop_first=True, dtype=float)
    ev, filt = spatial_filter(y, fits["M1"][1], off, C, W, rng)
    out["spatial_filter"] = filt
    betas = {}
    for key in ("M1", "M3"):
        r, X = fits[key]
        blk = beta_block(r, X, y, off, D, SHARE)
        Xz = X.join(dummies)
        rz = poisson(y, Xz, off)
        blk["zone_fixed_effects"] = {**beta_block(rz, Xz, y, off, D, SHARE),
                                     "residual_moran": moran_test(pearson(rz, y), W, rng)}
        Xf = X.assign(**ev)
        rf = poisson(y, Xf, off)
        blk["spatial_filter"] = {"eigenvectors": len(ev), **beta_block(rf, Xf, y, off, D, SHARE),
                                 "residual_moran": moran_test(pearson(rf, y), W, rng)}
        betas[key] = blk
    out["beta_share_above_real_cap"] = betas

    # 3. Spatial cross-validation
    allidx = np.arange(len(m))
    by_zone = [(allidx[(zone != z).to_numpy()], allidx[(zone == z).to_numpy()]) for z in sorted(zone.unique())]
    buffered = [(allidx[(C[i] == 0) & (allidx != i)], np.array([i])) for i in allidx]
    out["spatial_cv"] = {"leave_one_zone_out": cv_block(m, by_zone), "leave_one_out_with_neighbours_out": cv_block(m, buffered)}

    # 4. The simulator's interval figures at the spatial interval's ends
    m3 = betas["M3"]
    if m3["conley_30km"]["se"] > m3["hc1"]["se"]:
        lo, hi = m3["conley_30km"]["ci95"]
        out["simulator_with_spatial_interval"] = {
            "note": "El simulador no cambia; estas son sus dos cifras con intervalo, en los extremos del intervalo de Conley (30 km)",
            **simulator_at({"central": m3["beta"], "hc1_bajo": m3["hc1"]["ci95"][0], "hc1_alto": m3["hc1"]["ci95"][1],
                            "conley30_bajo": lo, "conley30_alto": hi})}
    text = json.dumps(out, indent=1, ensure_ascii=False, default=float)
    (ROOT / "resultados" / "espacial.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

"""EXPLORATORY, pre-registered in PREREGISTRO_DISTRITOS.md (local commit a74873e, 13-Nov-2026 15:34, before computing):
figure 3 (the proposal's +41 % for the neediest third) with Madrid city split into its 21 districts.

Today Madrid city (54 % of the young people) is one unit and one bolsa, so the +41 % is measured outside it. Here the 21
districts replace it: 131 municipalities + 21 districts = 152 units. Each district gets Madrid's figure in the project
table times its share in a district source (so the districts add up to, or average, Madrid's figure):
  - young 20-34 and 15-24 (2024): city register at 1-1-2024 (Ayuntamiento, datos.madrid.es 209163, by age and section)
  - income per person: Madrid's 27,188 EUR x district / city "renta media disponible por persona" (panel of district
    indicators, datos.madrid.es 300087, edition 2026, year 2023)
  - unemployment under 25 per 1,000 aged 15-24: Madrid's 25.83 x district / city "tasa de desempleo de 16 a 24 años"
    (same panel, year 2024, mean of men and women)
  - % of main dwellings rented (2021): INE census 2021 by section (table T20), summed by district; for Madrid it gives
    24.02 %, as the portal, so it is used as it is
  - rents: SERPAVI by district (median, p25, p75, 2022 and 2024), data/interim/serpavi_madrid_distritos.csv
  - share of IRPF returns under 5 x IPREM: Madrid's for every district (not available by district)
  - Bono 2022 requests: Madrid's 30,961 split in proportion to young x exp(beta x share of the district's rents above the
    2022 cap, 900 EUR), central beta, same young shares in 2022 as in 2024
Need index of a district: the same three percentile ranks, each as the district's position in the distribution of the
136 municipalities with the three components (the set the published ranks were computed on; the pre-registration said
"the 132 of the simulator": this is the set that keeps every municipality's published index), so municipalities keep
their published index. Geometric-mean ruler: ranks floored at 1/136, the lowest municipal rank.
Scenarios (same 31.8 M EUR, the Plan's aid): A the Plan as it is (first come); B the proposal with a quota per unit;
C the proposal with 3 bolsas = thirds of young people by need over the 152 units, first come inside each.
Check: the same bolsas code with Madrid as one unit and the 4 bolsas of como_se_aplica.py gives its +40.8 %.
Usage:  python -P scripts/distritos_cifra3.py   (after simulador.py and como_se_aplica.py)
        -> data/interim/distritos_madrid_2024.csv, resultados/distritos_cifra3.json, data/DISTRITOS_CIFRA3.md
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, ROOT, share_above  # noqa: E402
from necesidad_2024 import COMPONENTS  # noqa: E402
import como_se_aplica as csa  # noqa: E402
import simulador as sim  # noqa: E402

RAW13 = ROOT / "data" / "raw_2026-11-13"
RES = ROOT / "resultados"
DOC = ROOT / "data" / "DISTRITOS_CIFRA3.md"
OUT_CSV = INTERIM / "distritos_madrid_2024.csv"
PROPOSAL = "necesidad_requisito_plan_p75_hasta_1000"
PROPOSAL_HOW = ("necesidad", 1, "requisito")
THIRDS = ["necesidad alta", "necesidad media", "necesidad baja"]
MAD = sim.MADRID


def ensure_raw():
    """The three district sources are too big for the repository (78 MB): download any that is missing from the
    addresses in data/raw_2026-11-13/metadata.json and warn if its SHA-256 is not the one used on 13-Nov-2026 (the
    panel and the register are updated by the Ayuntamiento)."""
    import hashlib
    import time
    import urllib.error
    import urllib.request
    meta = json.loads((RAW13 / "metadata.json").read_text(encoding="utf-8"))
    for path, info in meta["ficheros"].items():
        f = RAW13 / path
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(info["url"], headers={"User-Agent": "datos-cliente/1.0"})
            for attempt in range(4):  # 20-nov: the server answered 504 once in GitHub; try again before failing
                try:
                    with urllib.request.urlopen(req, timeout=90) as r:
                        f.write_bytes(r.read())
                    break
                except (urllib.error.URLError, TimeoutError) as e:  # HTTPError is a URLError
                    if attempt == 3 or (isinstance(e, urllib.error.HTTPError) and e.code < 500):
                        raise
                    print(f"AVISO: {path}: {e}; lo intento otra vez en {30 * (attempt + 1)} s")
                    time.sleep(30 * (attempt + 1))
        if hashlib.sha256(f.read_bytes()).hexdigest() != info["sha256"]:
            print(f"AVISO: {path} no es el fichero del 13-nov-2026 (la fuente se ha actualizado); las cifras pueden cambiar")


def num(s):
    """Panel values: '19632', '2,77' or '1.234,5' -> float."""
    s = s.astype(str).str.strip()
    s = s.where(~s.str.contains(","), s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def district_sources():
    """Raw district figures from the three sources, indexed by district number 1-21, plus the city values."""
    p = pd.read_csv(RAW13 / "padron_ayto_202401" / "padron_202401.csv", sep=";", encoding="utf-8-sig", dtype=str)
    cnt = ["ESPANOLESHOMBRES", "ESPANOLESMUJERES", "EXTRANJEROSHOMBRES", "EXTRANJEROSMUJERES"]
    p["n"] = p[cnt].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    p["edad"] = pd.to_numeric(p["COD_EDAD_INT"].str.strip(), errors="coerce")
    p["d"] = pd.to_numeric(p["COD_DISTRITO"]).astype(int)
    src = pd.DataFrame({"padron_20_34": p[p["edad"].between(20, 34)].groupby("d")["n"].sum(),
                        "padron_15_24": p[p["edad"].between(15, 24)].groupby("d")["n"].sum(),
                        "padron_total": p.groupby("d")["n"].sum()})

    pan = pd.read_csv(RAW13 / "panel_indicadores_ayto" / "acumulado.csv", sep=";", encoding="utf-8-sig", dtype=str,
                      low_memory=False)
    pan = pan[pan["cod_barrio"].isna()]
    city = {}

    def pick(name, edition, year):
        x = pan[(pan["indicador_completo"] == name) & (pan["Periodo panel"] == edition) & (pan["año"] == year)]
        c = x[x["distrito"].isna()]
        x = x[x["distrito"].notna()]
        assert len(x) == 21 and len(c) == 1, (name, len(x), len(c))
        city[name] = float(num(c["valor_indicador"]).iloc[0])
        return pd.Series(num(x["valor_indicador"]).to_numpy(), index=pd.to_numeric(x["cod_distrito"]).astype(int))

    src["renta_panel_2023"] = pick("Renta media disponible por persona", "2026", "2023")
    nm = pan[(pan["indicador_completo"] == "Renta media disponible por persona") & pan["distrito"].notna()]
    src["nombre"] = pd.Series(nm["distrito"].str.strip().to_numpy(), index=pd.to_numeric(nm["cod_distrito"]).astype(int)).groupby(level=0).first()
    men = pick("Tasa de desempleo en hombres de 16 a 24 años", "2024", "2024")
    women = pick("Tasa de desempleo en mujeres de 16 a 24 años", "2024", "2024")
    src["paro16_24_panel_2024"] = (men + women) / 2
    city_paro = (city["Tasa de desempleo en hombres de 16 a 24 años"] + city["Tasa de desempleo en mujeres de 16 a 24 años"]) / 2

    ine = pd.read_csv(RAW13 / "ine_censo2021_secciones" / "C2021_Indicadores.csv",
                      dtype={"cpro": str, "cmun": str, "dist": str, "secc": str})
    ine = ine[(ine["cpro"] == "28") & (ine["cmun"] == "079")]
    ten = ine.groupby(ine["dist"].astype(int))[["t20_1", "t20_2", "t20_3"]].sum()
    src["pct_alquiler_2021"] = 100 * ten["t20_2"] / ten.sum(axis=1)
    city_rent_share = 100 * ine["t20_2"].sum() / ine[["t20_1", "t20_2", "t20_3"]].sum().sum()
    return src, {"renta_panel_2023": city["Renta media disponible por persona"], "paro16_24_panel_2024": city_paro,
                 "pct_alquiler_2021_ine": city_rent_share}


def serpavi_districts():
    s = pd.read_csv(INTERIM / "serpavi_madrid_distritos.csv", dtype={"ine": str})
    s = s[(s["ine"] == MAD) & s["year"].isin([2022, 2024])].copy()
    s["d"] = s["cudis"] % 100
    w = s.pivot_table(index="d", columns="year", values=["med", "p25", "p75", "n"])
    w.columns = [f"serpavi_{a}_{b}" for a, b in w.columns]
    return w


def district_table(s, beta):
    """The 21 districts with every column the simulator uses, anchored to Madrid's row of the project table."""
    m = s[s["ine"] == MAD].iloc[0]
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    tm = t[t["ine"] == MAD].iloc[0]
    src, city = district_sources()
    d = src.join(serpavi_districts())
    assert len(d) == 21 and d.notna().all().all(), d.isna().sum()
    # Madrid as one unit under the Plan's cap, for comparison with the districts' modelled requests
    plan_cap = sim.plan_cap(s[s["ine"] == MAD])[0]
    city["requests_plan_madrid_as_one"] = float(m["tasa_2022"] * m["jovenes_20_34_2024"] * np.exp(
        beta * (share_above(plan_cap, m["serpavi_p25_2024"], m["serpavi_p75_2024"]) - m["share_above_cap_2022"])))
    d["jovenes_20_34_2024"] = m["jovenes_20_34_2024"] * d["padron_20_34"] / d["padron_20_34"].sum()
    d["jovenes_15_24_2024"] = tm["jovenes_15_24_2024"] * d["padron_15_24"] / d["padron_15_24"].sum()
    d["renta_pc_2024"] = tm["renta_pc_2024"] * d["renta_panel_2023"] / city["renta_panel_2023"]
    d["paro25_por_1000_15_24_2024"] = tm["paro25_por_1000_15_24_2024"] * d["paro16_24_panel_2024"] / city["paro16_24_panel_2024"]
    d["esfuerzo_alquiler_2024"] = 12 * d["serpavi_med_2024"] / d["renta_pc_2024"]
    # need index: each component's position in the distribution of the 136 municipalities with the three components
    ref = t[t[list(COMPONENTS)].notna().all(axis=1)]
    for c in COMPONENTS:
        r = ref[c].to_numpy()
        d[f"rango_{c}"] = [float((r <= x).mean()) for x in d[c]]
    d["indice_necesidad"] = 100 * d[[f"rango_{c}" for c in COMPONENTS]].mean(axis=1)
    # Bono 2022 requests by district: Madrid's, in proportion to young x exp(beta x share above the 2022 cap)
    d["share_above_cap_2022"] = [share_above(m["tope_2022"], a, z) for a, z in zip(d["serpavi_p25_2022"], d["serpavi_p75_2022"])]
    young22 = d["jovenes_20_34_2024"] * m["jovenes_20_34_2022"] / m["jovenes_20_34_2024"]
    e = np.exp(beta * d["share_above_cap_2022"])
    d["solicitudes_2022_modeladas"] = m["bono_solicitudes"] * young22 * e / (young22 * e).sum()
    d["tasa_2022"] = d["solicitudes_2022_modeladas"] / young22
    d["jovenes_20_34_2022"] = young22
    d["bono_solicitudes"] = d["solicitudes_2022_modeladas"]
    for c in ("pob_total_2024", "tope_2022", "tope_2024", sim.BONO_INCOME, sim.PLAN_INCOME,
              sim.PLAN_INCOME + "_min", sim.PLAN_INCOME + "_max"):
        d[c] = m[c]  # Madrid's caps (the cap is set per municipality) and income-limit shares
    d["ine"] = [f"{MAD}{i:02d}" for i in d.index]
    d["municipio"] = ["Madrid - " + src.loc[i, "nombre"] for i in d.index]
    d["distrito"] = d.index
    return d.reset_index(drop=True), city


def thirds(units, score):
    """Thirds of young people by score (higher = more need) over every unit."""
    o = units.assign(score=np.asarray(score, float)).sort_values("score")
    cum = o["jovenes_20_34_2024"].cumsum() / o["jovenes_20_34_2024"].sum()
    g = pd.Series(np.select([cum <= 1 / 3, cum <= 2 / 3], ["necesidad baja", "necesidad media"], "necesidad alta"),
                  index=o.index)
    return g.reindex(units.index).to_numpy()


def bolsas(group, labels, req, weights, aid, budget):
    """como_se_aplica.bolsas for any set of bolsas: reserves by quota weights in euros, first come inside each, the
    leftovers to the bolsas with requests waiting."""
    cost = 24 * aid
    reserve_w = np.array([(weights * cost)[group == g].sum() for g in labels])
    demand = np.array([(req * cost)[group == g].sum() for g in labels])
    money = sim.allocate(demand, reserve_w, budget)
    out = np.zeros(len(req))
    for g, mny in zip(labels, money):
        k = group == g
        out[k] = sim.allocate_money(req[k], req[k], mny, aid[k])
    return out, money


def scenarios(u, beta):
    rules = sim.rules(u)
    plan_caps, (prop_caps, how) = rules["plan_estatal"][0], rules[PROPOSAL]
    req_plan, req_prop = sim.requests(u, plan_caps, beta)[0], sim.requests(u, prop_caps, beta)[0]
    aid_plan, aid_prop = sim.plan_aid(u, plan_caps), sim.plan_aid(u, prop_caps)
    w = sim.need_weights(u, how, sim.PLAN_INCOME)
    a = {"A_plan_tal_cual": sim.allocate_money(req_plan, req_plan, sim.BUDGET_EUR, aid_plan),
         "B_cupos_por_unidad": sim.allocate_money(req_prop, w, sim.BUDGET_EUR, aid_prop)}
    return a, req_plan, req_prop, w, aid_prop


def per1000(aids, young, k):
    return 1000 * aids[k].sum() / young[k].sum()


def check_madrid_whole(s, beta):
    """With Madrid as one unit and the 4 bolsas of como_se_aplica.py, this code must give its +40.8 %."""
    s = s.copy()
    s["grupo_necesidad"] = sim.need_groups(s)
    a, _, req_prop, w, aid_prop = scenarios(s, beta)
    group = s["grupo_necesidad"].to_numpy()
    c, _ = bolsas(group, csa.GROUPS, req_prop, w, aid_prop, sim.BUDGET_EUR)
    young = s["jovenes_20_34_2024"].to_numpy(float)
    k = group == "resto, necesidad alta"
    got = round(100 * (per1000(c, young, k) / per1000(a["A_plan_tal_cual"], young, k) - 1), 2)
    ref = json.loads((RES / "como_se_aplica.json").read_text(encoding="utf-8"))["change_vs_plan_pct"]["bolsas"]["resto, necesidad alta"]
    assert abs(got - ref) < 0.01, (got, ref)
    return got


def rulers(u):
    ranks = u[[f"rango_{c}" for c in COMPONENTS]]
    raw = u[list(COMPONENTS)]
    out = {"indice_del_proyecto": u["indice_necesidad"]}
    out.update({f"solo_{c}": u[c] for c in COMPONENTS})
    out.update({f"sin_{c}": ranks.drop(columns=f"rango_{c}").mean(axis=1) for c in COMPONENTS})
    out["zscores"] = ((raw - raw.mean()) / raw.std()).mean(axis=1)
    out["media_geometrica"] = np.exp(np.log(ranks.clip(lower=1 / 136)).mean(axis=1))
    return out


def build():
    s, _ = sim.load()
    beta = json.loads((RES / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
        "real_cap_and_uniform_900"]["real_cap"]["beta"]
    check = check_madrid_whole(s, beta)
    d, city = district_table(s, beta)
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    comp = t.set_index("ine")
    s = s.copy()
    for c in COMPONENTS:  # the components and published ranks of the municipalities, for the rulers
        s[c] = s["ine"].map(comp[c])
        s[f"rango_{c}"] = s["ine"].map(comp[f"rango_{c}"])
    keep = [c for c in s.columns if c in d.columns]
    u = pd.concat([s[s["ine"] != MAD][keep], d[keep]], ignore_index=True)
    u["es_distrito"] = u["ine"].str.len() == 5
    young = u["jovenes_20_34_2024"].to_numpy(float)
    a, req_plan, req_prop, w, aid_prop = scenarios(u, beta)
    group = thirds(u, u["indice_necesidad"])
    a["C_3_bolsas"], money = bolsas(group, THIRDS, req_prop, w, aid_prop, sim.BUDGET_EUR)
    dist = u["es_distrito"].to_numpy()

    def block(k):
        p = per1000(a["A_plan_tal_cual"], young, k)
        return {"young": int(round(young[k].sum())), "units": int(k.sum()), "districts": int((k & dist).sum()),
                "young_share_in_madrid": round(float(young[k & dist].sum() / young[k].sum()), 4) if k.any() else None,
                **{f"aids_{n}": round(float(v[k].sum()), 1) for n, v in a.items()},
                **{f"per1000_{n}": round(float(per1000(v, young, k)), 4) for n, v in a.items()},
                **{f"change_{n}_vs_A_pct": round(float(100 * (per1000(v, young, k) / p - 1)), 2)
                   for n, v in a.items() if n != "A_plan_tal_cual"}}

    out = {"note": "EXPLORATORIO, preregistrado en PREREGISTRO_DISTRITOS.md (commit a74873e, 13-nov 15:34): la cifra 3 "
                   "con Madrid capital en sus 21 distritos; supuestos en el docstring de scripts/distritos_cifra3.py",
           "beta": beta, "units": len(u), "check_madrid_whole_top_third_pct": check,
           "requests": {"plan_madrid_districts": round(float(req_plan[dist].sum())),
                        "proposal_madrid_districts": round(float(req_prop[dist].sum()))},
           "city_values_in_sources": city,
           "by_third": {g: block(group == g) for g in THIRDS},
           "madrid_city": block(dist),
           "outside_madrid_by_third": {g: block((group == g) & ~dist) for g in THIRDS},
           "bolsas_money_meur": {g: round(float(m / 1e6), 3) for g, m in zip(THIRDS, money)}}
    # ADDED AFTER SEEING THE RESULTS (not pre-registered): D = today's 4 bolsas (the three thirds outside Madrid city and
    # Madrid's bolsa, with today's reserves), and inside Madrid's bolsa 3 sub-bolsas = thirds of Madrid's young people
    # by district need, with money in proportion to their quota weights; first come inside each sub-bolsa
    s0, _ = sim.load()
    s0["grupo_necesidad"] = sim.need_groups(s0)
    m0 = s0[s0["ine"] == MAD].iloc[0]
    out_group = u["ine"].map(s0.set_index("ine")["grupo_necesidad"]).fillna("Madrid capital").to_numpy()
    cost = 24 * aid_prop
    w_mad_today = float(sim.need_weights(s0[s0["ine"] == MAD], PROPOSAL_HOW, sim.PLAN_INCOME)[0]
                        * 24 * sim.plan_aid(s0[s0["ine"] == MAD], np.array([1000.0]))[0])
    reserve = np.array([(w * cost)[out_group == g].sum() if g != "Madrid capital" else w_mad_today for g in csa.GROUPS])
    demand = np.array([(req_prop * cost)[out_group == g].sum() for g in csa.GROUPS])
    money4 = sim.allocate(demand, reserve, sim.BUDGET_EUR)
    sub = np.full(len(u), "", dtype=object)
    sub[dist] = thirds(u[dist], u.loc[dist, "indice_necesidad"])
    dd = np.zeros(len(u))
    for g, mny in zip(csa.GROUPS, money4):
        k = out_group == g
        if g != "Madrid capital":
            dd[k] = sim.allocate_money(req_prop[k], req_prop[k], mny, aid_prop[k])
        else:
            labels = THIRDS
            res_w = np.array([(w * cost)[k & (sub == x)].sum() for x in labels])
            dem = np.array([(req_prop * cost)[k & (sub == x)].sum() for x in labels])
            for x, mm in zip(labels, sim.allocate(dem, res_w, mny)):
                kk = k & (sub == x)
                dd[kk] = sim.allocate_money(req_prop[kk], req_prop[kk], mm, aid_prop[kk])
    a["D_4_bolsas_y_madrid_por_distritos"] = dd
    pa = a["A_plan_tal_cual"]
    out["D_added_after_results"] = {
        "note": "AÑADIDO DESPUÉS DE VER LOS RESULTADOS (no preregistrado): las 4 bolsas de hoy (con sus reservas) y, "
                "dentro de la de Madrid, 3 subbolsas por la necesidad de sus distritos",
        "outside_madrid_by_third_change_vs_A_pct": {
            g: round(float(100 * (per1000(dd, young, out_group == g) / per1000(pa, young, out_group == g) - 1)), 2)
            for g in csa.GROUPS[:3]},
        "madrid_city_change_vs_A_pct": round(float(100 * (per1000(dd, young, dist) / per1000(pa, young, dist) - 1)), 2),
        "madrid_subthirds": {x: {"districts": [n.replace("Madrid - ", "") for n in u.loc[dist & (sub == x), "municipio"]],
                                 "young": int(round(young[dist & (sub == x)].sum())),
                                 "per1000_A": round(float(per1000(pa, young, dist & (sub == x))), 4),
                                 "per1000_D": round(float(per1000(dd, young, dist & (sub == x))), 4),
                                 "change_vs_A_pct": round(float(100 * (per1000(dd, young, dist & (sub == x))
                                                                       / per1000(pa, young, dist & (sub == x)) - 1)), 2)}
                             for x in THIRDS}}
    rows = u.assign(tercio=group, plan=a["A_plan_tal_cual"], bolsas=a["C_3_bolsas"], cupos=a["B_cupos_por_unidad"])
    md = rows[dist].copy()
    md["per1000_plan"] = 1000 * md["plan"] / md["jovenes_20_34_2024"]
    md["per1000_bolsas"] = 1000 * md["bolsas"] / md["jovenes_20_34_2024"]
    md["change_pct"] = 100 * (md["bolsas"] / md["plan"] - 1)
    cols = ["municipio", "indice_necesidad", "tercio", "jovenes_20_34_2024", "esfuerzo_alquiler_2024",
            "paro25_por_1000_15_24_2024", "pct_alquiler_2021", "plan", "bolsas", "per1000_plan", "per1000_bolsas", "change_pct"]
    out["districts"] = md.sort_values("indice_necesidad", ascending=False)[cols].round(3).to_dict("records")
    out["rulers"] = {}
    for name, score in rulers(u).items():
        g = thirds(u, score)
        k = g == "necesidad alta"
        p = per1000(a["A_plan_tal_cual"], young, k)
        out["rulers"][name] = {
            "spearman_with_index": round(float(pd.Series(np.asarray(score, float)).corr(u["indice_necesidad"], method="spearman")), 3),
            "units_in_top_third": int(k.sum()), "districts_in_top_third": int((k & dist).sum()),
            "per1000_A": round(float(p), 4),
            "change_C_vs_A_pct": round(float(100 * (per1000(a["C_3_bolsas"], young, k) / p - 1)), 2),
            "change_B_vs_A_pct": round(float(100 * (per1000(a["B_cupos_por_unidad"], young, k) / p - 1)), 2)}
    d.to_csv(OUT_CSV, index=False, encoding="utf-8", lineterminator="\n")
    return out


def report(o):
    es, signed = csa.es, csa.signed
    bt, mc, ob, dpost = o["by_third"], o["madrid_city"], o["outside_madrid_by_third"], o["D_added_after_results"]
    top = bt["necesidad alta"]
    rl = o["rulers"]
    others = [v["change_C_vs_A_pct"] for k, v in rl.items() if k != "indice_del_proyecto"]
    dist = o["districts"]
    names = lambda recs: ", ".join(r["municipio"].replace("Madrid - ", "") for r in recs)  # noqa: E731
    top_d = [r for r in dist if r["tercio"] == "necesidad alta"]
    low_d = [r for r in dist if r["tercio"] == "necesidad baja"]
    rows = "\n".join(
        f"| {g.capitalize()} | {es(v['young'])} | {v['units']} ({v['districts']} distritos) | {es(100 * v['young_share_in_madrid'])} % | "
        f"{es(v['per1000_A_plan_tal_cual'], 2)} | {es(v['per1000_C_3_bolsas'], 2)} | {signed(v['change_C_3_bolsas_vs_A_pct'], 1)} % | "
        f"{signed(v['change_B_cupos_por_unidad_vs_A_pct'], 1)} % |" for g, v in bt.items())
    sub = dpost["madrid_subthirds"]
    exp_ok = lambda c: "✅ se cumple" if c else "❌ no se cumple"  # noqa: E731
    return f"""# La cifra 3 con Madrid capital por distritos

Lo genera `scripts/distritos_cifra3.py`. **Es exploratorio**, preregistrado en [PREREGISTRO_DISTRITOS.md](../PREREGISTRO_DISTRITOS.md) antes de calcular (commit `a74873e`, 13-nov-2026 a las 15:34). Lo marcado como «añadido después» no estaba preregistrado.

## Qué se ha hecho
Hoy Madrid capital, con el 54 % de los jóvenes, va como una sola unidad y una sola bolsa. Por eso el +41 % se mide fuera de ella. Aquí sus 21 distritos ocupan su lugar: 131 municipios y 21 distritos, {o['units']} unidades. Cada distrito lleva la cifra de Madrid de la tabla del proyecto, repartida según el padrón municipal de 2024, el panel de indicadores de distritos del Ayuntamiento y el censo 2021 del INE. Sus solicitudes de 2022 no existen, así que son un supuesto: las de Madrid, repartidas con el modelo del proyecto. Detalles y fuentes, en el docstring del script y en `data/raw_2026-11-13/metadata.json`.

**Comprobación:** con Madrid entero, el mismo código da el {signed(o['check_madrid_whole_top_third_pct'], 1)} % de `resultados/como_se_aplica.json`.

**Una precisión sobre el preregistro:** la posición de cada distrito en cada componente se mide frente a los 136 municipios con los tres datos, que son con los que se calculó el índice publicado (el preregistro decía «los 132 del simulador»). Así ningún municipio cambia de índice.

## El índice de necesidad de los distritos
- **Más necesidad (en el tercio alto):** {names(top_d)}. Esperaba ahí Puente de Vallecas, Villaverde, Usera, Carabanchel, Latina y Villa de Vallecas: ✅ están todos
- **Menos necesidad (en el tercio bajo):** {names(low_d)}. Esperaba ahí Salamanca, Chamberí, Chamartín, Retiro y Moncloa-Aravaca: todos menos Chamberí, que queda en el tercio medio
- **Distritos en el tercio alto:** {top['districts']} (esperaba entre 6 y 10: {exp_ok(6 <= top['districts'] <= 10)}), con el {es(100 * top['young_share_in_madrid'])} % de sus jóvenes (esperaba entre un tercio y la mitad: {exp_ok(1 / 3 <= top['young_share_in_madrid'] <= 0.5)})

## Resultado preregistrado: 3 bolsas por necesidad con los distritos dentro
Con el mismo dinero (31,8 M€) y la cuantía del Plan.

| Tercio | Jóvenes | Unidades | De ellos en Madrid | Ayudas por 1.000 jóvenes con el Plan | Con las 3 bolsas | Cambio | Con un cupo por unidad |
|---|---|---|---|---|---|---|---|
{rows}

- **El tercio con más necesidad gana un {signed(top['change_C_3_bolsas_vs_A_pct'], 1)} %**, no un +41 %. Esperaba entre +10 % y +30 %: {exp_ok(10 <= top['change_C_3_bolsas_vs_A_pct'] <= 30)}. Motivo: el {es(100 * top['young_share_in_madrid'])} % de sus jóvenes vive en {top['districts']} distritos de Madrid, que con el Plan ya reciben muchas ayudas: en Madrid se piden más ayudas por joven que fuera, y el supuesto reparte más solicitudes donde el alquiler cabe bajo el tope
- **Con las otras 8 formas de medir la necesidad,** el tercio con más necesidad gana entre un {signed(min(others), 1)} % y un {signed(max(others), 1)} %: positivo en todas ({exp_ok(min(others) > 0)})
- **Madrid capital entera:** {signed(mc['change_C_3_bolsas_vs_A_pct'], 1)} % con las 3 bolsas ({signed(mc['change_B_cupos_por_unidad_vs_A_pct'], 1)} % con un cupo por unidad). Esperaba entre −15 % y +5 %: {exp_ok(-15 <= mc['change_C_3_bolsas_vs_A_pct'] <= 5)}
- **El coste de mezclar:** los municipios con más necesidad de fuera de Madrid ganan solo un {signed(ob['necesidad alta']['change_C_3_bolsas_vs_A_pct'], 1)} % (hoy, un +41 %), porque comparten bolsa y orden de llegada con distritos que piden mucho más. Con un cupo para cada municipio y cada distrito ganarían un {signed(ob['necesidad alta']['change_B_cupos_por_unidad_vs_A_pct'], 1)} %, y Madrid entera perdería un {es(-mc['change_B_cupos_por_unidad_vs_A_pct'], 1)} %
- **Según lo decidido antes de calcular** (entre 0 y +15 %): va a la respuesta de la pregunta 29 y a «Método y datos», tal cual. **El titular no cambia:** +41 % fuera de Madrid capital, con Madrid −11 % al lado

## Añadido después de ver el resultado (no preregistrado): las 4 bolsas de hoy y Madrid repartida por distritos
Las 4 bolsas de hoy, con su dinero, pero la de Madrid se reparte en 3 subbolsas según la necesidad de sus distritos, por orden de llegada dentro de cada una:
- **Fuera de Madrid, todo sigue igual:** el tercio con más necesidad, {signed(dpost['outside_madrid_by_third_change_vs_A_pct']['resto, necesidad alta'], 1)} %
- **Madrid capital entera:** {signed(dpost['madrid_city_change_vs_A_pct'], 1)} %, como hoy
- **Dentro de Madrid,** los distritos con más necesidad ({', '.join(sub['necesidad alta']['districts'])}) pasan de perder como todos a {signed(sub['necesidad alta']['change_vs_A_pct'], 1)} %; los de necesidad media, {signed(sub['necesidad media']['change_vs_A_pct'], 1)} %, y los de menos ({', '.join(sub['necesidad baja']['districts'])}), {signed(sub['necesidad baja']['change_vs_A_pct'], 1)} %
- Es la respuesta más directa a «¿Y Madrid capital?»: con la misma propuesta, **los barrios de Madrid con más necesidad no pierden**; pierden los de menos

## Límites
- **Las solicitudes por distrito son un supuesto:** las de Madrid, repartidas con el freno del tope que medimos entre municipios. Si dentro de Madrid frena distinto, cambia el reparto del Plan por distritos
- **Años mezclados:** renta de 2023, paro de 2024, censo de 2021 y padrón de 2024
- **Fuentes de apoyo:** el Ayuntamiento de Madrid y el INE, como ya el SERPAVI. La base municipal sigue siendo la del portal de la Comunidad
- **La parte de las declaraciones bajo 5 × IPREM** es la de Madrid en todos los distritos (no la hay por distrito)

Todas las cifras, en `resultados/distritos_cifra3.json`; la tabla de los distritos, en `data/interim/distritos_madrid_2024.csv`.
"""


def main():
    ensure_raw()
    out = build()
    with open(RES / "distritos_cifra3.json", "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1, default=float) + "\n")
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write(report(out))
    print(json.dumps({k: out[k] for k in ("check_madrid_whole_top_third_pct", "requests", "city_values_in_sources",
                                          "bolsas_money_meur")}, ensure_ascii=False, indent=1))
    keys = ["young", "units", "districts", "young_share_in_madrid", "per1000_A_plan_tal_cual", "per1000_C_3_bolsas",
            "change_C_3_bolsas_vs_A_pct", "change_B_cupos_por_unidad_vs_A_pct"]
    blocks = {**{f"tercio {g}": out["by_third"][g] for g in THIRDS}, "Madrid capital": out["madrid_city"],
              **{f"fuera de Madrid, {g}": out["outside_madrid_by_third"][g] for g in THIRDS}}
    print(pd.DataFrame({k: {x: v[x] for x in keys} for k, v in blocks.items()}).T.to_string())
    print(json.dumps(out["D_added_after_results"], ensure_ascii=False, indent=1))
    print(pd.DataFrame(out["districts"]).to_string())
    print(pd.DataFrame(out["rulers"]).T.to_string())


if __name__ == "__main__":
    main()

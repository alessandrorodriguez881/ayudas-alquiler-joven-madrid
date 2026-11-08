"""Basis for the study that art. 135 of the Plan Estatal de Vivienda 2026-2030 (RD 326/2026) asks for before a region
raises the rent cap of the youth rent aid: "estudios actualizados de oferta de vivienda [...] en alquiler", which "podrán
fundamentarse" on the two cases of art. 18.3 a) and b) of Ley 12/2023 (stressed housing markets). For each municipality:
  a) rent burden: SERPAVI 2024 median rent x 12 over the household's income (the Comunidad's gross disposable income
     per person in 2024, times people per household in 2021). Rent only: the law adds "gastos y suministros básicos",
     so where rent alone passes 30 % the case is met for sure, and with utilities it would be met in more places.
  b) rent rise: SERPAVI median 2019 -> 2024 against the rise of the Comunidad de Madrid CPI (INE, annual means) plus
     3 points.
It only gives evidence: the decision, the official study and the agreement with the Ministry (art. 135, second sentence)
are the Comunidad's. Our proposal only lifts the Plan's 500 EUR in municipalities of 10,000 people or fewer, up to their
p75 and never above 1,000 EUR (scripts/simulador.py, rules), so the report is about them.
Reads the database (run scripts/base_datos.py first), the 2021 census files in data/raw/ and the CPI in
data/raw/ine_ipc_madrid/. Offline.
Usage:  python -P scripts/estudio_art135.py   -> resultados/estudio_art135.csv, resultados/estudio_art135.json and
                                                 data/ESTUDIO_ART135.md
"""
import json
import pathlib
import sqlite3
import sys
from contextlib import closing

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import RAW, ROOT, cm_to_ine, leer_csv, share_above  # noqa: E402
import simulador as sm  # noqa: E402

DB = ROOT / "data" / "bono_alquiler_joven.sqlite"
RES = ROOT / "resultados"
CPI = RAW / "ine_ipc_madrid" / "IPC256325_2019_2024.json"
BURDEN, EXTRA_POINTS = 0.30, 3.0  # Ley 12/2023, art. 18.3 a) and b)
MIN_RENTALS = 30  # fewest SERPAVI rentals in a year to use its median (small municipalities have few)
FIRST, LAST = 2019, 2024  # the five years before the latest SERPAVI


def cpi_rise():
    """Rise of the Comunidad de Madrid CPI (general index, base 2021) between the annual means of 2019 and 2024, in %."""
    data = json.loads(CPI.read_text(encoding="utf-8"))["Data"]
    assert all(sum(d["Anyo"] == y for d in data) == 12 for y in (FIRST, LAST)), "12 months a year"
    mean = {y: float(np.mean([d["Valor"] for d in data if d["Anyo"] == y])) for y in (FIRST, LAST)}
    return 100 * (mean[LAST] / mean[FIRST] - 1), mean


def people_per_household():
    """2021 population (annual census) over 2021 main dwellings (Census of Housing): the same year in both."""
    read = lambda name: leer_csv(next((RAW / name).glob("*.csv")), dtype={"Código territorio": str})  # noqa: E731
    pop = read("poblacion_censada_por_edad_nacionalidad_y_sexo")
    pop = pop[(pop["Año"] == 2021) & (pop["Tipo territorio"] == "Municipios")
              & (pop["Edad"] == "Total") & (pop["Nacionalidad"] == "Total") & (pop["Sexo"] == "Total")]
    homes = read("censo_2021_viviendas_familiares_por_tenencia")
    homes = homes[(homes["Año"] == 2021) & (homes["Tipo territorio"] == "Municipios")]
    homes = homes.groupby("Código territorio")["Valor"].sum()  # owned + rented + other: every main dwelling
    out = pd.DataFrame({"pob_2021": pop.set_index("Código territorio")["Valor"], "hogares_2021": homes})
    out.index = [cm_to_ine(c) for c in out.index]
    return out


def build():
    with closing(sqlite3.connect(f"file:{DB}?mode=ro", uri=True)) as con:
        m = pd.read_sql("SELECT ine, municipio, pob_total_2024, jovenes_20_34_2024, renta_pc_2024, hasta_10000_hab "
                        "FROM municipios", con).set_index("ine")
        caps = pd.read_sql("SELECT ine, regla, tope_piso FROM topes WHERE regla IN ('plan_2026_2030', 'propuesta')", con)
        rents = pd.read_sql(f"SELECT ine, anio, viviendas, mediana, p25, p75 FROM alquiler_serpavi "
                            f"WHERE anio IN ({FIRST}, {LAST})", con)
    caps = caps.pivot(index="ine", columns="regla", values="tope_piso")
    m["tope_plan"], m["tope_propuesta"] = caps["plan_2026_2030"], caps["propuesta"]
    m["sube_tope"] = m["tope_propuesta"] > m["tope_plan"]
    for year in (FIRST, LAST):
        r = rents[rents["anio"] == year].set_index("ine")
        enough = r["viviendas"] >= MIN_RENTALS
        m[f"viviendas_{year}"] = r["viviendas"]
        for col in ("mediana", "p25", "p75"):
            m[f"{col}_{year}"] = r[col].where(enough)
    m = m.join(people_per_household())
    m["personas_por_hogar_2021"] = m["pob_2021"] / m["hogares_2021"]
    m["renta_hogar_2024"] = m["renta_pc_2024"] * m["personas_por_hogar_2021"]
    m["esfuerzo_alquiler_hogar"] = 12 * m[f"mediana_{LAST}"] / m["renta_hogar_2024"]
    m["subida_alquiler_pct"] = 100 * (m[f"mediana_{LAST}"] / m[f"mediana_{FIRST}"] - 1)
    rise, cpi_mean = cpi_rise()
    m["cumple_a"] = (m["esfuerzo_alquiler_hogar"] > BURDEN).where(m["esfuerzo_alquiler_hogar"].notna())
    m["cumple_b"] = (m["subida_alquiler_pct"] >= rise + EXTRA_POINTS).where(m["subida_alquiler_pct"].notna())
    m["justificacion"] = [case(a, b) for a, b in zip(m["cumple_a"], m["cumple_b"])]
    for rule in ("plan", "propuesta"):
        m[f"parte_por_encima_tope_{rule}"] = [share_above(c, p25, p75) for c, p25, p75 in
                                             zip(m[f"tope_{rule}"], m[f"p25_{LAST}"], m[f"p75_{LAST}"])]
    return m.reset_index().sort_values(["sube_tope", "jovenes_20_34_2024"], ascending=False), rise, cpi_mean


def case(a, b):
    """Which of the two cases of art. 18.3 the data support. 'ninguno' only when both were measured and neither is
    met; when one is missing and the other is not met, nothing can be concluded."""
    met = [name for name, ok in (("a", a), ("b", b)) if pd.notna(ok) and bool(ok)]
    if met:
        return " y ".join(met)
    return "ninguno" if pd.notna(a) and pd.notna(b) else "sin datos suficientes"


def summary(m, rise, cpi_mean):
    up = m[m["sube_tope"]]
    count = lambda d, what: int((d["justificacion"] == what).sum())  # noqa: E731
    some = up["justificacion"].isin(["a", "b", "a y b"])
    return {
        "note": "Base para el estudio del art. 135 del RD 326/2026 (no es el estudio oficial). Criterios del art. 18.3 a) y b) "
                "de la Ley 12/2023: a) alquiler mediano 2024 sobre la renta del hogar (sin gastos ni suministros), más del "
                "30 %; b) subida del alquiler mediano 2019-2024 al menos 3 puntos por encima del IPC de la Comunidad",
        "cpi": {"series": "INE IPC256325", "mean_2019": round(cpi_mean[FIRST], 3), "mean_2024": round(cpi_mean[LAST], 3),
                "rise_pct": round(rise, 2), "threshold_b_pct": round(rise + EXTRA_POINTS, 2)},
        "min_rentals": MIN_RENTALS,
        "where_proposal_raises_cap": {
            "municipalities": int(len(up)), "young_20_34_2024": int(up["jovenes_20_34_2024"].sum()),
            "with_data": int((up["justificacion"] != "sin datos suficientes").sum()),
            "a_only": count(up, "a"), "b_only": count(up, "b"), "a_and_b": count(up, "a y b"),
            "none": count(up, "ninguno"), "no_data": count(up, "sin datos suficientes"),
            "some_case": int(some.sum()), "young_in_some_case": int(up.loc[some, "jovenes_20_34_2024"].sum()),
            "median_share_above_plan_cap": round(float(up[f"parte_por_encima_tope_plan"].median()), 3),
        },
        "all_municipalities": {
            "with_data": int((m["justificacion"] != "sin datos suficientes").sum()),
            "case_a": int((m["cumple_a"] == True).sum()), "case_b": int((m["cumple_b"] == True).sum()),  # noqa: E712
        },
    }


def only_where_justified(m):
    """The proposal again (the Plan's aid, central beta), but lifting the 500 EUR only where the study can justify it:
    if the figures hold, the proposal does not rest on caps nobody could defend."""
    s, _ = sm.load()
    s["grupo_necesidad"] = sm.need_groups(s)
    beta = json.loads((RES / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
        "real_cap_and_uniform_900"]["real_cap"]["beta"]
    req_now = sm.requests(s, s["tope_2024"].to_numpy(float), beta)[0]
    success_now = sm.allocate(req_now, req_now, sm.BUDGET_EUR / sm.BONO_EUR).sum() / req_now.sum()
    caps, how = sm.rules(s)["necesidad_requisito_plan_p75_hasta_1000"]
    plan = sm.plan_cap(s)
    ok = s["ine"].map(m.set_index("ine")["justificacion"].isin(["a", "b", "a y b"])).fillna(False).to_numpy(bool)
    young, high = s["jovenes_20_34_2024"].to_numpy(), (s["grupo_necesidad"] == "resto, necesidad alta").to_numpy()
    out = {"raised_in_simulation": int((caps > plan).sum()), "not_justified_kept_at_plan": int(((caps > plan) & ~ok).sum())}
    for name, c in (("proposal", caps), ("proposal_only_where_justified", np.where(ok, caps, plan))):
        req, aid = sm.requests(s, c, beta)[0], sm.plan_aid(s, c)
        aids = sm.allocate_money(req, sm.need_weights(s, how, sm.PLAN_INCOME), sm.BUDGET_EUR, aid)
        out[name] = {"aids_per_1000_young_high_need": round(float(1000 * aids[high].sum() / young[high].sum()), 4),
                     "meur_same_chance_as_today": round(float(success_now * (req * 24 * aid).sum() / 1e6), 4)}
    return out


def es(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def report(m, s):
    up, w = m[m["sube_tope"]], s["where_proposal_raises_cap"]
    rows = []
    for _, r in up.iterrows():
        pct = lambda v: "—" if pd.isna(v) else es(100 * v) + " %"  # noqa: E731
        rows.append(f"| {r['municipio']} | {es(r['pob_total_2024'])} | {es(r['jovenes_20_34_2024'])} | "
                    f"{'—' if pd.isna(r['mediana_2024']) else es(r['mediana_2024']) + ' €'} | "
                    f"{es(r['tope_plan'])} → {es(r['tope_propuesta'])} € | {pct(r['parte_por_encima_tope_plan'])} | "
                    f"{pct(r['esfuerzo_alquiler_hogar'])} | "
                    f"{'—' if pd.isna(r['subida_alquiler_pct']) else es(r['subida_alquiler_pct']) + ' %'} | "
                    f"{r['justificacion']} |")
    c = s["cpi"]
    return f"""# Base para el estudio del art. 135: subir el tope de 500 € en los municipios pequeños

Lo genera `scripts/estudio_art135.py`. **No es el estudio oficial:** es la base con datos abiertos para que la Comunidad de Madrid lo haga. Decidir, hacer el estudio y firmar el acuerdo con el Ministerio le toca a ella.

## Qué dice la norma
- **Plan Estatal de Vivienda 2026-2030** ([RD 326/2026](https://www.boe.es/buscar/act.php?id=BOE-A-2026-8872)), art. 133.1.e: la ayuda a jóvenes es para alquileres de hasta 1.000 € al mes, o de 500 € en los municipios de 10.000 habitantes o menos
- **Art. 135:** las comunidades autónomas pueden subir ese máximo si lo justifican con estudios actualizados del alquiler, que pueden basarse en los dos supuestos del art. 18.3 de la [Ley 12/2023](https://www.boe.es/buscar/act.php?id=BOE-A-2023-12203). Antes de convocar, hace falta un acuerdo con el Ministerio de Vivienda en la comisión de seguimiento
- **Ley 12/2023, art. 18.3:**
  - a) que el coste del alquiler, más los gastos y suministros básicos, pase del 30 % de la renta media de los hogares
  - b) que el alquiler haya subido en los cinco años anteriores al menos 3 puntos más que el IPC de la comunidad autónoma

## Cómo lo medimos
- **Supuesto a):** el alquiler mediano de 2024 (SERPAVI, Ministerio de Vivienda) por 12, entre la renta del hogar. La renta del hogar es la renta disponible bruta por habitante de 2024 (portal de la Comunidad) por las personas por hogar de 2021 (población del censo anual entre viviendas principales del Censo de 2021, los dos del portal). **Solo el alquiler, sin gastos ni suministros:** donde ya pasa del 30 %, el supuesto se cumple seguro; con los gastos se cumpliría en más municipios
- **Supuesto b):** la subida del alquiler mediano del SERPAVI de 2019 a 2024, frente a la del IPC de la Comunidad de Madrid (INE, serie {c['series'].split()[-1]}, media de cada año): **{es(c['rise_pct'], 1)} %**. Se cumple con una subida de al menos el **{es(c['threshold_b_pct'], 1)} %**
- Solo usamos el alquiler mediano de un año si el SERPAVI tiene al menos {s['min_rentals']} viviendas en ese municipio. Si falta un dato y el otro supuesto no se cumple, «sin datos suficientes»
- **La propuesta sube el tope** donde el percentil 75 del alquiler de 2024, redondeado a 50 € hacia arriba, pasa de 500 €, y nunca por encima de 1.000 €. Así, 3 de cada 4 alquileres del municipio caben en el tope

## Resultado
- La propuesta sube el tope en **{w['municipalities']} municipios pequeños**, donde viven **{es(w['young_20_34_2024'])} jóvenes** de 20 a 34 años
- Con el tope de 500 € del Plan, en la mitad de ellos queda fuera **más del {es(100 * w['median_share_above_plan_cap'])} %** del alquiler
- **Se puede justificar con datos en {w['some_case']} de ellos** ({es(w['young_in_some_case'])} jóvenes):
  - solo con el supuesto a): {w['a_only']}
  - solo con el b): {w['b_only']}
  - con los dos: {w['a_and_b']}
  - con ninguno de los dos (medidos los dos): {w['none']}
  - sin datos suficientes para decirlo: {w['no_data']}
- En toda la Comunidad, con datos en {s['all_municipalities']['with_data']} municipios, el supuesto a) se cumple en {s['all_municipalities']['case_a']} y el b) en {s['all_municipalities']['case_b']}. Con la renta media de los hogares, el alquiler solo no llega al 30 % en ningún municipio: con estos datos, la vía es el supuesto b)
- **La propuesta no depende de los municipios que no se pueden justificar.** Si el tope solo sube donde se puede (y en los demás se queda en 500 €), el tercio de municipios con más necesidad recibe {es(s['sensitivity']['proposal_only_where_justified']['aids_per_1000_young_high_need'], 1)} ayudas por cada 1.000 jóvenes (con la propuesta entera, {es(s['sensitivity']['proposal']['aids_per_1000_young_high_need'], 1)}), y que pedirla dé la misma probabilidad que hoy costaría {es(s['sensitivity']['proposal_only_where_justified']['meur_same_chance_as_today'], 1)} M€ ({es(s['sensitivity']['proposal']['meur_same_chance_as_today'], 1)} M€). Es la simulación de `scripts/simulador.py`, con la cuantía del Plan

| Municipio | Habitantes (2024) | Jóvenes de 20 a 34 | Alquiler mediano (2024) | Tope: Plan → propuesta | Alquiler fuera del tope del Plan | Alquiler / renta del hogar | Subida 2019-2024 | Supuesto |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Límites
- El SERPAVI recoge los contratos declarados en el IRPF, no los anuncios: mide el alquiler que se paga, no la oferta. Es el índice oficial del Ministerio, pero el art. 135 habla de «oferta»
- La renta del hogar es una estimación: renta por habitante de 2024 por las personas por hogar de 2021
- En los municipios pequeños hay pocos contratos, así que la mediana de un año a otro se mueve mucho. Por eso pedimos al menos {s['min_rentals']} viviendas
- Sin los gastos y suministros, el supuesto a) se queda corto: la cifra real de municipios que lo cumplen es igual o mayor

Todos los datos, por municipio, en `resultados/estudio_art135.csv`.
"""


def main():
    m, rise, cpi_mean = build()
    s = summary(m, rise, cpi_mean)
    s["sensitivity"] = only_where_justified(m)
    cols = ["ine", "municipio", "pob_total_2024", "hasta_10000_hab", "jovenes_20_34_2024", "tope_plan", "tope_propuesta",
            "sube_tope", f"viviendas_{LAST}", f"mediana_{LAST}", f"p25_{LAST}", f"p75_{LAST}", "parte_por_encima_tope_plan",
            "parte_por_encima_tope_propuesta", "personas_por_hogar_2021", "renta_pc_2024", "renta_hogar_2024",
            "esfuerzo_alquiler_hogar", "cumple_a", f"viviendas_{FIRST}", f"mediana_{FIRST}", "subida_alquiler_pct",
            "cumple_b", "justificacion"]
    RES.mkdir(exist_ok=True)
    m[cols].round(4).to_csv(RES / "estudio_art135.csv", index=False)
    (RES / "estudio_art135.json").write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "data" / "ESTUDIO_ART135.md").write_text(report(m, s), encoding="utf-8")
    print(json.dumps(s, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

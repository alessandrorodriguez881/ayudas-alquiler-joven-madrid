"""Data for the app: what the scripts in scripts/ already wrote, read once and cached. No numbers are made up here:
caps, shares above the cap and the simulator come from the same functions as the report (scripts/simulador.py)."""
import json
import pathlib
import sqlite3
import sys
from contextlib import closing
from decimal import ROUND_HALF_UP, Decimal

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import reglas_bono as rb  # noqa: E402,F401  (the calculator's rules, one function per article)
import simulador  # noqa: E402
from comun import INTERIM, share_above  # noqa: E402

RES = ROOT / "resultados"
DB = ROOT / "data" / "bono_alquiler_joven.sqlite"  # scripts/base_datos.py
DISTRICTS = "distritos_madrid_wgs84.geojson"  # scripts/distritos_madrid.py
MIN_YOUNG = 500  # as in graficos.py: the rate of a village with 1 or 2 bonos is noise
PROPOSAL = "necesidad_requisito_plan_p75_hasta_1000"
# Reference palette of the dataviz method, the same as the figures (scripts/graficos.py)
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORANGE = ["#fde4d8", "#f9c2a8", "#f39a74", "#eb6834", "#c94f1f", "#9c3c17", "#6e2a10"]
SLOT1, SLOT2, NO_DATA = "#2a78d6", "#eb6834", "#e1e0d9"
SOURCE = ("Fuentes: Portal de Datos Abiertos de la Comunidad de Madrid (Bono Alquiler Joven 2022, población, renta, paro, "
          "IRPF por tramos, límites municipales; CC BY 4.0) y SERPAVI (Ministerio de Vivienda).")


def es(x, decimals=0):
    """Spanish number format: 1.234,5 (halves rounded up)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "sin dato"
    q = Decimal(str(float(x))).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    return f"{q:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x, decimals=0):
    return "sin dato" if x is None or np.isnan(x) else es(100 * x, decimals) + " %"


@st.cache_data(show_spinner=False)
def simulation_base():
    """The simulator's table (136 municipalities with every figure it needs) and its need groups."""
    s, cover = simulador.load()
    s["grupo_necesidad"] = simulador.need_groups(s)
    return s, cover


@st.cache_data(show_spinner=False)
def municipalities():
    """One row per municipality (179): need, coverage, caps and share of the market above each cap."""
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    young22 = t["jovenes_20_34_2022"].where(t["jovenes_20_34_2022"] >= MIN_YOUNG)
    t["solicitudes_1000_2022"] = 1000 * t["bono_solicitudes"] / young22
    t["cobertura_2022"] = 1000 * t["bono_aceptadas"] / young22
    s, _ = simulation_base()
    rules = simulador.rules(s)
    caps = {"plan": simulador.plan_cap(s), "propuesta": rules[PROPOSAL][0]}
    extra = s[["ine", "grupo_necesidad", simulador.BONO_INCOME, simulador.PLAN_INCOME]].copy()
    for k, c in caps.items():
        extra[f"tope_{k}"] = c
        extra[f"fuera_{k}"] = [share_above(v, a, z) for v, a, z in zip(c, s["serpavi_p25_2024"], s["serpavi_p75_2024"])]
    # three young people sharing a flat on room contracts: the flat may cost 3 x the room cap (habitaciones.py)
    extra["fuera_3_comparten_hoy"] = [share_above(1.5 * v, a, z) for v, a, z in
                                      zip(s["tope_2024"], s["serpavi_p25_2024"], s["serpavi_p75_2024"])]
    # bonos recomputed here, not read from simulador_municipios.csv: that file keeps 1 decimal, and rounding it again
    # turned Parla's 64.48 bonos into 65
    beta = result("exploratorio_topes_falsos")["real_cap_and_uniform_900"]["real_cap"]["beta"]
    n_bonos = simulador.BUDGET_EUR / simulador.BONO_EUR
    req0 = simulador.requests(s, s["tope_2024"].to_numpy(float), beta)[0]
    extra["bonos_actual_2024_55"] = simulador.allocate(req0, req0, n_bonos)
    cap, how = rules[PROPOSAL]
    req = simulador.requests(s, cap, beta)[0]
    extra["bonos_propuesta"] = simulador.allocate(req, simulador.need_weights(s, how), n_bonos)
    return t.merge(extra, on="ine", how="left")


@st.cache_data(show_spinner=False)
def shapes(name="municipios_wgs84.geojson"):
    """Municipal boundaries (WGS84) on a grid of 0.001 degrees (about 100 m), without repeated points: 50,000 points
    instead of 160,000, and neighbours still share their borders because both snap to the same grid. With DISTRICTS,
    Madrid city's 21 districts, which fit the municipalities around them on the same grid."""
    g = json.loads((INTERIM / name).read_text(encoding="utf-8"))

    def ring(r):
        out = []
        for x, y in r:
            p = [round(x, 3), round(y, 3)]
            if not out or out[-1] != p:
                out.append(p)
        return out if len(out) >= 4 else None

    feats = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        kept = []
        for poly in polys:
            rings = [ring(r) for r in poly]
            if rings[0] is not None:
                kept.append([r for r in rings if r is not None])
        feats.append({"ine": f["properties"]["ine"], "nombre": f["properties"].get("nombre"),
                      "geometry": {"type": "MultiPolygon", "coordinates": kept}})
    return feats


@st.cache_data(show_spinner=False)
def madrid_districts():
    """Madrid city's 21 districts ('07901' Centro ... '07921' Barajas, as on the map) with their SERPAVI 2024 rents, in
    the columns of municipalities()."""
    s = pd.read_csv(INTERIM / "serpavi_madrid_distritos.csv", dtype={"ine": str})
    s = s[(s["ine"] == "079") & (s["year"] == 2024)]
    names = {f["ine"]: f["nombre"] for f in shapes(DISTRICTS)}
    return pd.DataFrame({"ine": "079" + s["cudis"].astype("int64").astype(str).str[-2:],  # 2807901 -> '07901'
                         "serpavi_n_2024": s["n"], "serpavi_med_2024": s["med"], "serpavi_p25_2024": s["p25"],
                         "serpavi_p75_2024": s["p75"]}).assign(distrito=lambda d: d["ine"].map(names))


@st.cache_data(show_spinner=False)
def map_spec(col, bins, colors, title, fmt):
    """Vega-Lite spec of the map of one column, built once per measure (Altair takes seconds on this much geometry)."""
    t = municipalities()
    return choropleth(t.set_index("ine")[col], dict(zip(t["ine"], t["municipio"])), list(bins), list(colors), title,
                      fmt).to_dict()


@st.cache_data(show_spinner=False)
def query(sql, params=()):
    """Rows of the project's SQLite database, opened read-only."""
    with closing(sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)) as con:
        return pd.read_sql(sql, con, params=params)


@st.cache_data(show_spinner=False)
def result(name):
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def choropleth(values, names, bins, colors, title, fmt, height=520, areas=None):
    """Altair map of one measure (threshold colour scale, grey where there is no figure); click selects a municipality.
    areas: the shapes to draw, the municipalities by default."""
    feats = [{"type": "Feature", "geometry": f["geometry"],
              "properties": {"ine": f["ine"], "municipio": names.get(f["ine"], f["ine"]),
                             "valor": None if pd.isna(values.get(f["ine"])) else float(values.get(f["ine"]))}}
             for f in (shapes() if areas is None else areas)]
    pick = alt.selection_point(fields=["ine"], name="municipio", on="click", clear="dblclick")
    color = (alt.when("datum.valor === null").then(alt.value(NO_DATA))
             .otherwise(alt.Color("valor:Q", title=title, scale=alt.Scale(type="threshold", domain=bins, range=colors),
                                  legend=alt.Legend(format=fmt, orient="bottom", direction="horizontal", titleLimit=400))))
    return (alt.Chart(alt.Data(values=feats))
            .transform_calculate(ine="datum.properties.ine", municipio="datum.properties.municipio",
                                 valor="datum.properties.valor")
            .mark_geoshape(stroke="white", strokeWidth=0.5)
            .encode(color=color, opacity=alt.when(pick).then(alt.value(1)).otherwise(alt.value(0.55)),
                    tooltip=[alt.Tooltip("municipio:N", title="Municipio"), alt.Tooltip("valor:Q", title=title, format=fmt)])
            .add_params(pick)
            .project(type="mercator")
            .properties(height=height))

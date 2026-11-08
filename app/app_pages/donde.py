"""Where does the aid reach? For one young person (income, alone or sharing a flat), every municipality with the share
of 2024 rents that fit under the flat cap of each rule, the aid and what they would pay after it. The rules are the
calculator's (scripts/reglas_bono.py) and the caps come from the database, so the figures match the other pages. Rents
are SERPAVI 2024 (collective dwellings): a guide to where the aid works, not a listing of flats."""
import numpy as np
import pandas as pd
import streamlit as st

from datos import BLUE, SOURCE, choropleth, es, municipalities, pct, query, rb, share_above

RULE_IN_DB = {"hoy": "bono_2024", "plan": "plan_2026_2030", "propuesta": "propuesta"}
RULE_NAME = {"hoy": "Hoy", "plan": "Plan 2026-2030", "propuesta": "Propuesta"}
RULE_LONG = {"hoy": "la regla de hoy (Bono 2024)", "plan": "el Plan 2026-2030", "propuesta": "nuestra propuesta"}
MIN_RENTALS = 50  # SERPAVI rentals behind a municipality's 2024 percentiles: below this they are too noisy to show


@st.cache_data(show_spinner=False)
def fit(rule):
    """Per municipality: flat cap of the rule and share of 2024 rents at or under it (NaN without enough rentals)."""
    t = municipalities()[["ine", "municipio", "serpavi_n_2024", "serpavi_med_2024", "serpavi_p25_2024",
                          "serpavi_p75_2024"]]
    caps = query("SELECT ine, tope_piso, tope_habitacion FROM topes WHERE regla = ?", (RULE_IN_DB[rule],)).set_index("ine")
    t = t.assign(tope=t["ine"].map(caps["tope_piso"]), tope_habitacion=t["ine"].map(caps["tope_habitacion"]))
    ok = t["serpavi_n_2024"] >= MIN_RENTALS
    t["entra"] = [1 - share_above(c, a, z) if k else np.nan
                  for c, a, z, k in zip(t["tope"], t["serpavi_p25_2024"], t["serpavi_p75_2024"], ok)]
    return t


@st.cache_data(show_spinner=False)
def fit_map(rule):
    """Vega-Lite spec of the map, built once per rule (Altair takes seconds on this much geometry)."""
    t = fit(rule)
    return choropleth(t.set_index("ine")["entra"], dict(zip(t["ine"], t["municipio"])), [0.2, 0.35, 0.5, 0.65, 0.8, 0.9],
                      BLUE, "Alquileres de 2024 que entran en el tope", ".0%").to_dict()


st.title("¿Dónde te llega la ayuda?")
st.caption("Dinos cómo buscarías piso y te enseñamos en qué municipios entran más alquileres en el tope, cuánto te darían "
           "y cuánto pagarías tú. Con los alquileres reales de 2024 (SERPAVI): es una guía de dónde funciona la ayuda, no "
           "un buscador de anuncios. No se guarda nada de lo que escribes.")

with st.container(border=True):
    a, b = st.columns(2, vertical_alignment="bottom")
    rule = a.segmented_control("Con qué regla", list(RULE_NAME), format_func=RULE_NAME.get, default="hoy",
                               key="donde_regla") or "hoy"
    how = b.segmented_control("Cómo vivirías", ["Solo o sola", "Compartiendo piso"], default="Solo o sola",
                              key="donde_como") or "Solo o sola"
    a, b = st.columns(2, vertical_alignment="bottom")
    income = a.number_input("Tus ingresos del último año (€ al año)", min_value=0, max_value=1000000, value=18000,
                            step=500, key="donde_ingresos")
    n = 1
    if how == "Compartiendo piso":
        n = int(b.number_input("¿Cuántos jóvenes firmáis el contrato, contándote?", min_value=2, max_value=6, value=2,
                               key="donde_n", help="Cada uno pide su ayuda; el alquiler y la ayuda se reparten."))

t = fit(rule)
rows = []
for r in t.dropna(subset=["entra"]).itertuples():
    rent = min(r.serpavi_med_2024, r.tope)  # a typical flat that fits: the median, or the cap where the median is above
    case = rb.Case(age=27, kind="piso", price=float(rent), includes="vivienda", expenses_included=False,
                   living="jovenes" if n > 1 else "solo", sharers=n, income=float(income), others_income=0.0,
                   regular_income=True, nationality=True, disability="no", exclusions=frozenset(), other_rent_aid=False)
    res = rb.evaluate(case, rule, float(r.tope), float(r.tope_habitacion))
    aid = res.monthly if res.eligible else 0.0
    rows.append({"ine": r.ine, "municipio": r.municipio, "entra": r.entra, "mediana": r.serpavi_med_2024, "tope": r.tope,
                 "alquiler": rent, "ayuda": aid, "pagas": rent / n - aid,
                 "esfuerzo": (rent / n - aid) / (income / 12) if income else np.nan, "res": res})
d = pd.DataFrame(rows).sort_values(["entra", "pagas"], ascending=[False, True])
failed = [ch for ch in d["res"].iloc[0].checks if not ch.ok]  # all else is set to pass: only income can fail
if failed:
    st.error(f"Con {RULE_LONG[rule]} no cumplirías el límite de ingresos. {failed[0].text}.",
             icon=":material/cancel:")

half = d[d["entra"] >= 0.5]
cheap = d.loc[d["pagas"].idxmin()]
KPIS = [  # short label and value (metric labels are cut to one line on a phone), what it means below
    ("Municipios con la mitad dentro", f"{len(half)} de {len(d)}",
     "con al menos la mitad de los alquileres de 2024 dentro del tope"),
    ("Donde menos pagarías", f"{es(cheap['pagas'])} €/mes", f"en {cheap['municipio']}, con su alquiler mediano y la ayuda"),
    ("La ayuda, al mes", f"hasta {es(d['ayuda'].max())} €" if d["ayuda"].max() else "0 €",
     "por persona: hoy, 250 € y nunca más que el alquiler; con el Plan y la propuesta, hasta 300 € y nunca más del 60 %"),
]
for col, (label, value, note) in zip(st.columns(3), KPIS):
    with col.container(border=True, height="stretch"):
        st.metric(label, value)
        st.caption(note)

left, right = st.columns([3, 2], gap="large")
with left:
    event = st.vega_lite_chart(spec=fit_map(rule), on_select="rerun", key="donde_mapa",
                               alt="Mapa de la parte de los alquileres de 2024 que entran en el tope, por municipio")
    st.caption(f"En gris, municipios con menos de {MIN_RENTALS} alquileres en el SERPAVI de 2024: su reparto de precios "
               "no es fiable. " + SOURCE)

names = sorted(d["municipio"], key=str.lower)
picked = [p.get("ine") for p in event.selection.get("municipio", [])] if event else []
pick = d.loc[d["ine"] == picked[0], "municipio"].iloc[0] if picked and (d["ine"] == picked[0]).any() else None
if pick and pick != st.session_state.get("donde_ultimo_clic"):  # a new click on the map moves the selector
    st.session_state["donde_ultimo_clic"] = st.session_state["donde_municipio"] = pick
if st.session_state.get("donde_municipio") not in names:
    st.session_state["donde_municipio"] = "Parla" if "Parla" in names else names[0]
with right:
    name = st.selectbox("Mira un municipio (o haz clic en el mapa)", names, key="donde_municipio")
    r = d.set_index("municipio").loc[name]
    with st.container(border=True):
        st.subheader(name)
        a, b = st.columns(2)
        a.metric("Alquileres dentro del tope", pct(r["entra"]))
        b.metric("Tope del piso", es(r["tope"]) + " €")
        a.metric("Alquiler mediano (2024)", es(r["mediana"]) + " €")
        b.metric("Te darían al mes", es(r["ayuda"]) + " €")
        a.metric("Pagarías tú al mes", es(r["pagas"]) + " €",
                 help=f"Con un alquiler de {es(r['alquiler'])} € (el mediano, o el tope si el mediano pasa del tope)"
                      + (f", repartido entre {n}" if n > 1 else "") + ", menos la ayuda.")
        b.metric("De tus ingresos", pct(r["esfuerzo"]) if income else "sin dato",
                 help="Lo que pagarías tú, sobre tus ingresos brutos de un mes (los del año entre 12). Por encima del "
                      "30 %, el alquiler pesa demasiado.")
        if st.button("Comprobar mi caso aquí, requisito a requisito", icon=":material/checklist:", type="primary",
                     width="stretch", key="donde_ir"):
            st.session_state.update({"calc_municipio": name, "calc_precio": int(round(r["alquiler"])),
                                     "calc_ingresos": int(income), "calc_tipo": "Piso entero",
                                     "calc_convivencia": "jovenes" if n > 1 else "solo"})
            if n > 1:
                st.session_state["calc_n"] = n
            st.switch_page("app_pages/calculadora.py")

st.subheader("Todos los municipios")
st.dataframe(d.drop(columns=["ine", "res", "alquiler"]).assign(entra=100 * d["entra"], esfuerzo=100 * d["esfuerzo"]),
             hide_index=True, width="stretch", height=380,
             column_config={"municipio": "Municipio",
                            "entra": st.column_config.ProgressColumn("Alquileres dentro del tope", format="%.0f %%",
                                                                     min_value=0, max_value=100),
                            "mediana": st.column_config.NumberColumn("Alquiler mediano", format="%d €"),
                            "tope": st.column_config.NumberColumn("Tope", format="%d €"),
                            "ayuda": st.column_config.NumberColumn("Ayuda al mes", format="%d €"),
                            "pagas": st.column_config.NumberColumn("Pagarías tú", format="%d €"),
                            "esfuerzo": st.column_config.NumberColumn("De tus ingresos", format="%.0f %%")},
             alt="Tabla de municipios con la parte de los alquileres que entran en el tope, la ayuda y lo que pagarías")
st.caption("Suponemos que cumples lo demás (edad, nacionalidad, no tener otra vivienda…): compruébalo en «¿Puedo "
           "pedirla?». Cumplir no asegura la ayuda: hoy se da por orden de llegada mientras queda dinero.")

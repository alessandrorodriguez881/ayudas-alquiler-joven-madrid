import altair as alt
import numpy as np
import streamlit as st

from datos import BLUE, SLOT1, SLOT2, SOURCE, es, municipalities, pct, query

PROGRAMMES = {"bono_alquiler_joven": "Bono Alquiler Joven", "ayudas_alquiler_jovenes": "Ayudas al alquiler para jóvenes",
              "ayudas_alquiler_escasos_recursos": "Ayudas al alquiler, escasos recursos"}


def rent_chart(rent, caps):
    """Median rent with its p25-p75 band (SERPAVI) and today's and the Plan's caps as dashed lines."""
    x = alt.X("anio:O", title=None, axis=alt.Axis(labelAngle=0))
    band = alt.Chart(rent).mark_area(color=BLUE[1], opacity=0.5).encode(
        x=x, y=alt.Y("p25:Q", title="€ al mes"), y2="p75:Q")
    line = alt.Chart(rent).mark_line(color=SLOT1, strokeWidth=2, point=alt.OverlayMarkDef(size=60, filled=True)).encode(
        x=x, y="mediana:Q",
        tooltip=[alt.Tooltip("anio:O", title="Año"), alt.Tooltip("mediana:Q", title="Mediano (€)", format=",.0f"),
                 alt.Tooltip("p25:Q", title="Uno de cada cuatro paga menos de (€)", format=",.0f"),
                 alt.Tooltip("p75:Q", title="Uno de cada cuatro paga más de (€)", format=",.0f")])
    rules = alt.Chart(caps).mark_rule(strokeDash=[6, 4], strokeWidth=2).encode(
        y="tope:Q", color=alt.Color("nombre:N", title=None, scale=alt.Scale(range=[SLOT2, "#8a8a8a"]),
                                    legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("nombre:N", title="Tope"), alt.Tooltip("tope:Q", title="€ al mes", format=",.0f")])
    return (band + line + rules).properties(height=300)

t = municipalities()
options = sorted(t["municipio"], key=lambda n: n.lower())
st.session_state.setdefault("municipio", "Parla")
name = st.selectbox("Municipio", options, key="municipio", bind="query-params")
r = t.set_index("municipio").loc[name]
rest = t[t["ine"] != "079"]
rest_rate = 1000 * rest["bono_aceptadas"].sum() / rest["jovenes_20_34_2022"].sum()

st.title(name)
if isinstance(r["grupo_necesidad"], str):
    st.badge(r["grupo_necesidad"].capitalize(), icon=":material/group:")

with st.container(horizontal=True):
    st.metric("Jóvenes de 20 a 34 años (2024)", es(r["jovenes_20_34_2024"]), border=True, height="stretch")
    st.metric("Índice de necesidad (0-100)", es(r["indice_necesidad"]), border=True, height="stretch")
    st.metric("Solicitudes del Bono 2022 por 1.000 jóvenes", es(r["solicitudes_1000_2022"], 1), border=True,
              height="stretch")
    st.metric("Bonos 2022 por 1.000 jóvenes", es(r["cobertura_2022"], 1), border=True, height="stretch",
              help=f"En el resto de la Comunidad sin Madrid capital: {es(rest_rate, 1)}. Sin dato si hay menos de 500 jóvenes.")

st.subheader("El tope y el alquiler")
if np.isnan(r["serpavi_p25_2024"]):
    st.info("El SERPAVI no da alquileres de 2024 para este municipio, así que no se puede medir qué parte supera el tope.",
            icon=":material/info:")
else:
    st.caption(f"Alquiler mediano de 2024: {es(r['serpavi_med_2024'])} € al mes; uno de cada cuatro pasa de "
               f"{es(r['serpavi_p75_2024'])} € (SERPAVI).")
    rows = [("Bono 2022", r["tope_2022"], r["share_above_tope_2022_en_2024"]),
            ("Bono 2024 (hoy)", r["tope_2024"], r["share_above_tope_2024_en_2024"]),
            ("Plan 2026-2030", r["tope_plan"], r["fuera_plan"]),
            ("Propuesta: Plan o alquiler local, hasta 1.000 €", r["tope_propuesta"], r["fuera_propuesta"])]
    st.table({"Regla": [x[0] for x in rows], "Tope del piso": [es(x[1]) + " €" for x in rows],
              "Alquileres de 2024 por encima": [pct(x[2]) if not np.isnan(x[2]) else "—" for x in rows]},
             alt=f"Topes del Bono en {name} y parte del alquiler de 2024 que los supera")
    st.caption(f"Tres jóvenes que comparten piso con contratos de habitación pueden pagar entre los tres hasta "
               f"{es(1.5 * r['tope_2024'])} € (3 × {es(r['tope_2024'] / 2)} €). Con ese límite queda fuera el "
               f"{pct(r['fuera_3_comparten_hoy'])} de los alquileres de 2024, si la habitación cuesta el alquiler del piso "
               f"entre tres (el caso optimista).")

left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("El alquiler, año a año")
    rent = query("SELECT anio, mediana, p25, p75 FROM alquiler_serpavi WHERE ine = ? AND mediana IS NOT NULL "
                 "ORDER BY anio", (r["ine"],))
    caps = query("SELECT regla, tope_piso AS tope FROM topes WHERE ine = ? AND regla IN ('bono_2024', 'plan_2026_2030')",
                 (r["ine"],))
    caps["nombre"] = caps["regla"].map({"bono_2024": "Tope del Bono hoy", "plan_2026_2030": "Tope del Plan 2026-2030"})
    if len(rent) < 2:
        st.caption("El SERPAVI no tiene una serie de alquileres para este municipio.")
    else:
        st.altair_chart(rent_chart(rent, caps.sort_values("regla")),
                        alt=f"Alquiler mensual mediano en {name} de {rent['anio'].min()} a {rent['anio'].max()}, con "
                            f"los topes del Bono y del Plan")
        st.caption("Línea: alquiler mensual mediano de vivienda colectiva. Banda: la mitad central de los alquileres "
                   "(del p25 al p75). Fuente: SERPAVI (Ministerio de Vivienda y Agenda Urbana).")
with right:
    st.subheader("Solicitudes")
    req = query("SELECT programa, anio_convocatoria, solicitudes, aceptadas FROM solicitudes WHERE ine = ? "
                "ORDER BY programa DESC, anio_convocatoria", (r["ine"],))
    if req.empty:
        st.caption("No hay solicitudes de este municipio en los datos abiertos.")
    else:
        st.dataframe(req.assign(programa=req["programa"].map(PROGRAMMES)), hide_index=True, width="stretch",
                     column_config={"programa": "Programa", "anio_convocatoria": st.column_config.NumberColumn(
                         "Año", format="%d"), "solicitudes": "Solicitudes", "aceptadas": "Aceptadas"})
        st.caption("Del Portal de Datos Abiertos de la Comunidad de Madrid. Las Ayudas para jóvenes tienen los mismos "
                   "topes que el Bono.")

st.subheader("El límite de ingresos y el reparto")
with st.container(horizontal=True):
    st.metric("Declaraciones del IRPF por debajo de 3 × IPREM (2024)", pct(r["share_irpf_bajo_3iprem_2024"]),
              border=True, height="stretch",
              help="Parte de las declaraciones con base imponible de hasta 25.200 €, de todas las edades: compara "
                   "municipios, no cuenta jóvenes.")
    st.metric("Ídem, por debajo de 5 × IPREM: el límite del Plan", pct(r["share_irpf_bajo_5iprem_2024"]),
              border=True, height="stretch",
              help="Base imponible de hasta 42.000 €. El Plan 2026-2030 mira los ingresos de la persona, no los del "
                   "hogar (art. 133.1.d).")
    st.metric("Bonos con la regla de hoy (simulación)", es(r["bonos_actual_2024_55"]), border=True, height="stretch",
              help="5.300 bonos (31,8 M€) por orden de llegada, con los topes de 2024.")
    delta = r["bonos_propuesta"] - r["bonos_actual_2024_55"]
    st.metric("Bonos con la propuesta (simulación)", es(r["bonos_propuesta"]),
              delta=None if np.isnan(delta) else es(delta), border=True, height="stretch",
              help="El mismo dinero, con topes del Plan o del alquiler local (hasta 1.000 €) y cupos por jóvenes × "
                   "necesidad × parte por debajo del límite de ingresos.")
st.caption(SOURCE + " Simulación con β = −0,54 (solo la parte del efecto que se debe al tope); ver «Método y datos».")

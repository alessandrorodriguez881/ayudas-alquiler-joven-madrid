import numpy as np
import streamlit as st

from datos import SOURCE, es, municipalities, pct

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

st.subheader("El límite de ingresos y el reparto")
with st.container(horizontal=True):
    st.metric("Declaraciones del IRPF por debajo de 3 × IPREM (2024)", pct(r["share_irpf_bajo_3iprem_2024"]),
              border=True, height="stretch",
              help="Parte de las declaraciones con base imponible de hasta 25.200 €, de todas las edades: compara "
                   "municipios, no cuenta jóvenes.")
    st.metric("Bonos con la regla de hoy (simulación)", es(r["bonos_actual_2024_55"]), border=True, height="stretch",
              help="5.300 bonos (31,8 M€) por orden de llegada, con los topes de 2024.")
    delta = r["bonos_propuesta"] - r["bonos_actual_2024_55"]
    st.metric("Bonos con la propuesta (simulación)", es(r["bonos_propuesta"]),
              delta=None if np.isnan(delta) else es(delta), border=True, height="stretch",
              help="El mismo dinero, con topes del Plan o del alquiler local (hasta 1.000 €) y cupos por jóvenes × "
                   "necesidad × parte por debajo del límite de ingresos.")
st.caption(SOURCE + " Simulación con β = −0,54 (solo la parte del efecto que se debe al tope); ver «Método y datos».")

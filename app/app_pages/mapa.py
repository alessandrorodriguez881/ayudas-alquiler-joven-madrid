import math

import streamlit as st

from datos import BLUE, ORANGE, SOURCE, es, map_spec, municipalities, pct, result

st.title("Donde el alquiler supera el tope, los jóvenes piden menos el Bono")
st.caption("Bono Alquiler Joven de la Comunidad de Madrid: 250 € al mes durante 2 años, solo para alquileres de hasta "
           "600 o 900 € (habitación: 300 o 450 €). No es un buscador de pisos: medimos si la ayuda llega a quien más la "
           "necesita y proponemos cómo hacer que llegue.")

test = result("contraste_real")
h1 = test["H1"]
sim = result("simulador_reparto")
group = lambda rule, g: sim["plan_amount"][rule]["aids_per_1000_young_by_group"][g]  # noqa: E731
high = lambda rule: group(rule, "resto, necesidad alta")  # noqa: E731
capital = lambda rule: group(rule, "Madrid capital")  # noqa: E731
gap = sim["gap_above_cap"]
# the cap's own part, without expensive rent as such (exploratory; the simulator's beta): the summary of the form says it
cap_part = 100 * (math.exp(0.1 * result("exploratorio_topes_falsos")["real_cap_and_uniform_900"]["real_cap"]["beta"]) - 1)
KPIS = [  # short label, value, what it means (in sight: metric labels are cut to one line)
    ("Menos solicitudes", f"{es(h1['pct_per_10_points'], 1)} %",
     f"por cada 10 % más de alquileres por encima del tope; la parte del propio tope, {es(cap_part, 1)} %. Contraste "
     f"registrado antes de hacerlo ({test['n_municipalities']} municipios con todos los datos)"),
    ("Alquiler fuera del tope", pct(gap["2024_rents_plan_estatal"]["10000_or_fewer"]),
     f"en los municipios pequeños con el Plan 2026-2030, que les pone 500 € (hoy, "
     f"{pct(gap['2024_rents_2024_list']['10000_or_fewer'])})"),
    ("Más ayudas donde más falta", "+" + pct(high("necesidad_requisito_plan_p75_hasta_1000") / high("plan_estatal") - 1),
     "en los municipios con más necesidad fuera de Madrid capital, con nuestra propuesta frente al Plan y el mismo "
     "dinero (31,8 M€). Madrid capital, que hoy recibe más ayudas por joven que el resto, baja un "
     f"{pct(1 - capital('necesidad_requisito_plan_p75_hasta_1000') / capital('plan_estatal'))}"),
]
for col, (label, value, note) in zip(st.columns(3), KPIS):
    with col.container(border=True, height="stretch"):
        st.metric(label, value)
        st.caption(note)
with st.container(horizontal=True):
    if st.button("¿Puedo pedirla?", icon=":material/checklist:", type="primary"):
        st.switch_page("app_pages/calculadora.py")
    if st.button("¿Dónde me llega la ayuda?", icon=":material/explore:", type="primary"):
        st.switch_page("app_pages/donde.py")
    if st.button("Simular el reparto (para la Consejería)", icon=":material/tune:"):
        st.switch_page("app_pages/simular.py")
st.divider()
st.caption("Haz clic en un municipio para ver sus cifras.")

t = municipalities()
names = dict(zip(t["ine"], t["municipio"]))
MEASURES = {
    "Necesidad": ("indice_necesidad", [30, 40, 50, 60, 70, 80], BLUE, "Índice de necesidad (2024)", ".0f",
                  "De 0 a 100: media de la posición de cada municipio en esfuerzo del alquiler sobre la renta (2024), "
                  "paro de menores de 25 años (2024) y hogares que viven de alquiler (Censo 2021)."),
    "Cobertura del Bono": ("cobertura_2022", [2, 4, 6, 8, 10, 12], ORANGE, "Bonos 2022 por 1.000 jóvenes", ".1f",
                           "Bonos concedidos en 2022 por cada 1.000 jóvenes de 20 a 34 años. En gris, sin dato o con "
                           "menos de 500 jóvenes (la tasa no es fiable)."),
    "Alquiler por encima del tope": ("share_above_tope_2024_en_2024", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], BLUE,
                                     "Parte del alquiler por encima del tope (2024)", ".0%",
                                     "Parte de los alquileres de 2024 (SERPAVI) que pasa del tope de 2024 (600 o 900 €)."),
    "Con el Plan 2026-2030": ("fuera_plan", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], BLUE,
                              "Parte del alquiler por encima del tope del Plan", ".0%",
                              "Con los topes del Plan Estatal 2026-2030: 1.000 €, y 500 € en los municipios de 10.000 "
                              "habitantes o menos."),
}
choice = st.segmented_control("Qué mostrar", list(MEASURES), default="Necesidad", key="medida")
col, bins, colors, title, fmt, note = MEASURES[choice or "Necesidad"]

left, right = st.columns([3, 2], gap="large")
with left:
    event = st.vega_lite_chart(spec=map_spec(col, tuple(bins), tuple(colors), title, fmt), on_select="rerun", key="mapa",
                               alt=f"Mapa de los municipios de la Comunidad de Madrid: {title.lower()}")
    st.caption(note + " " + SOURCE)

picked = [p.get("ine") for p in event.selection.get("municipio", [])] if event else []
with right:
    if picked and picked[0] in names:
        r = t.set_index("ine").loc[picked[0]]
        with st.container(border=True):
            st.subheader(r["municipio"])
            a, b = st.columns(2)
            a.metric("Jóvenes de 20 a 34 años (2024)", es(r["jovenes_20_34_2024"]))
            b.metric("Índice de necesidad", es(r["indice_necesidad"]))
            a.metric("Bonos 2022 por 1.000 jóvenes", es(r["cobertura_2022"], 1))
            b.metric("Tope del piso (2024)", es(r["tope_2024"]) + " €")
            a.metric("Alquiler por encima del tope", pct(r["share_above_tope_2024_en_2024"]))
            b.metric("Con el Plan 2026-2030", pct(r["fuera_plan"]))
            if st.button("Ver la ficha completa", icon=":material/arrow_forward:", width="stretch"):
                st.session_state["municipio"] = r["municipio"]
                st.switch_page("app_pages/ficha.py")
    else:
        st.info("Haz clic en un municipio del mapa para ver sus cifras. Doble clic para quitar la selección.",
                icon=":material/touch_app:")

    under = result("infraatendidos")
    st.subheader("Infraatendidos en 2022")
    st.caption(f"Municipios con {under['min_young_2022']} jóvenes o más, del tercio con más necesidad, que recibieron menos "
               f"bonos por joven que el resto de la Comunidad sin Madrid capital ({es(under['coverage_rest_without_madrid_per_1000'], 1)} "
               f"por cada 1.000). Son {under['n']}, con {es(under['young_2024'])} jóvenes.")
    st.dataframe(
        [{"Municipio": m["municipio"], "Necesidad": m["indice_necesidad"], "Bonos por 1.000 jóvenes": m["cobertura_2022"],
          "Tope 2022": m["tope_2022"], "Tope 2024": m["tope_2024"]} for m in under["municipalities"]],
        hide_index=True, height=300,
        column_config={"Necesidad": st.column_config.NumberColumn(format="%.0f"),
                       "Bonos por 1.000 jóvenes": st.column_config.NumberColumn(format="%.1f"),
                       "Tope 2022": st.column_config.NumberColumn(format="%d €"),
                       "Tope 2024": st.column_config.NumberColumn(format="%d €")},
        alt="Tabla de los municipios infraatendidos en 2022",
    )

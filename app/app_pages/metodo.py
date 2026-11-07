import numpy as np
import streamlit as st

from datos import INTERIM, RES, es, result

pct10 = lambda b: 100 * (np.exp(0.1 * b) - 1)  # noqa: E731  (% change in requests per 10 points above the cap)
h1 = result("contraste_real")["H1"]
fake = result("exploratorio_topes_falsos")
cap_only = fake["real_cap_and_uniform_900"]["real_cap"]
income = result("requisito_ingresos")["h1_with_income_rule_control"]["h1_plus_elig"]
rooms = result("habitaciones")["h1_with_room_contracts"]

st.title("Método y datos")
st.subheader("Lo que probamos, con la regla escrita antes de mirar")
st.markdown(
    f"- **Hipótesis principal, confirmada:** donde más parte del alquiler supera el tope, menos jóvenes piden el Bono. "
    f"Por cada 10 puntos más, un **{es(-h1['pct_per_10_points'], 1)} % menos** de solicitudes por joven "
    f"(intervalo del {es(-pct10(h1['ci95'][1]), 1)} % al {es(-pct10(h1['ci95'][0]), 1)} %; permutación p = {es(h1['p_perm'], 4)}).\n"
    f"- **Lo que no salió:** un umbral de 900 € igual para todos explica las solicitudes mejor que el tope real, y la "
    f"comparación entre municipios parecidos con tope de 600 y de 900 € no es precisa. Separando las dos cosas, la parte "
    f"del tope es un {es(-pct10(cap_only['beta']), 1)} % menos por cada 10 puntos: es la que usa el simulador.\n"
    f"- **Después, como exploratorio:** con el límite de ingresos (3 × IPREM) como control, el efecto queda en un "
    f"{es(-income['pct_per_10_points'], 1)} % menos. Contando los contratos de habitación de tres jóvenes que comparten "
    f"piso, el efecto sigue siendo negativo y el modelo ajusta mejor (desviación {es(rooms['mix_flat_and_3_sharers_rooms']['1.0']['deviance'])}, "
    f"frente a {es(rooms['real_cap']['deviance'])} con el tope del piso): es una pista, no una prueba."
)
st.image(str(RES / "figuras" / "contraste_todas_las_pruebas.png"),
         alt="Todas las estimaciones del efecto del tope, también las que no salieron, con sus intervalos")

st.subheader("Datos")
st.table({
    "Fuente": ["Portal de Datos Abiertos de la Comunidad de Madrid", "SERPAVI, Ministerio de Vivienda y Agenda Urbana",
               "Base de Datos Nacional de Subvenciones"],
    "Qué usamos": ["Bono Alquiler Joven 2022 (solicitudes, aceptadas y rechazadas por municipio); Ayudas al alquiler para "
                   "jóvenes; población por edad; renta disponible; declaraciones del IRPF por tramo; paro registrado por "
                   "edad; Censo 2021 (viviendas en alquiler); alquiler medio; límites municipales",
                   "Alquiler mediano, p25 y p75 por municipio, de 2022 a 2024",
                   "Municipios con tope de 900 € en cada convocatoria: 29 hasta 2023 y 55 desde 2024"],
    "Licencia": ["CC BY 4.0", "Reutilización permitida citando la fuente", "Textos oficiales publicados"],
}, alt="Datos que usa el proyecto, su fuente y su licencia")
st.caption("Todo es estadística agregada por municipio: ningún dato personal. Las licencias y las huellas de cada "
           "descarga están en el README y en data/VERIFICACION.md del repositorio.")

st.subheader("Descargas")
with st.container(horizontal=True):
    st.download_button("Indicadores por municipio (CSV)", (INTERIM / "municipios_2024.csv").read_bytes(),
                       "municipios_2024.csv", "text/csv", icon=":material/table:")
    st.download_button("Reparto simulado por regla (CSV)", (INTERIM / "simulador_municipios.csv").read_bytes(),
                       "simulador_municipios.csv", "text/csv", icon=":material/table:")
    st.download_button("Resultado del contraste (JSON)", (RES / "contraste_real.json").read_bytes(),
                       "contraste_real.json", "application/json", icon=":material/data_object:")

import numpy as np
import streamlit as st

from datos import DB, INTERIM, RES, es, query, result

pct10 = lambda b: 100 * (np.exp(0.1 * b) - 1)  # noqa: E731  (% change in requests per 10 points above the cap)
h1 = result("contraste_real")["H1"]
fake = result("exploratorio_topes_falsos")
cap_only = fake["real_cap_and_uniform_900"]["real_cap"]
income = result("requisito_ingresos")["h1_with_income_rule_control"]["h1_plus_elig"]
rooms = result("habitaciones")["h1_with_room_contracts"]
oos = result("validacion_fuera_muestra")
cv, ay = oos["A_bono_2022_cross_validation"]["leave_one_out"], oos["B_bono_2022_to_ayudas_jovenes_2023"]

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
    f"frente a {es(rooms['real_cap']['deviance'])} con el tope del piso): es una pista, no una prueba.\n"
    f"- **Con municipios que el modelo no ha visto** (exploratorio): saber qué parte del alquiler pasa del tope baja el "
    f"error típico de las solicitudes del {es(cv['controles']['median_abs_pct_error_10_or_more'])} % al "
    f"{es(cv['controles_tope_real']['median_abs_pct_error_10_or_more'])} % (dejando fuera un municipio cada vez). Y el "
    f"modelo del simulador, con el tope y los 900 € juntos, entrenado con el Bono 2022 predice las Ayudas para jóvenes de "
    f"2023, otro programa y otro año, con un {es(100 * (1 - ay['controles_ambas']['deviance'] / ay['controles']['deviance']))} % "
    f"menos de desviación que sin esas dos partes (correlación de {es(ay['controles']['spearman_rate'], 2)} a "
    f"{es(ay['controles_ambas']['spearman_rate'], 2)}). El umbral de 900 € igual para todos también predice bien: el "
    f"alquiler caro frena por sí solo."
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
                   "Alquiler mediano, p25 y p75 por municipio, de 2011 a 2024",
                   "Municipios con tope de 900 € en cada convocatoria: 29 hasta 2023 y 55 desde 2024"],
    "Licencia": ["CC BY 4.0", "Reutilización permitida citando la fuente", "Textos oficiales publicados"],
}, alt="Datos que usa el proyecto, su fuente y su licencia")
st.caption("Todo es estadística agregada por municipio: ningún dato personal. Las licencias y las huellas de cada "
           "descarga están en el README y en data/VERIFICACION.md del repositorio.")

st.subheader("La base de datos")
tables = query("SELECT tabla, COUNT(*) AS columnas FROM diccionario GROUP BY tabla")
meta = query("SELECT clave, valor FROM metadatos").set_index("clave")["valor"]
st.markdown(
    f"Todo lo que usa el proyecto está en **un solo fichero SQLite** de {es(DB.stat().st_size / 1e6, 1)} MB, con "
    f"{len(tables)} tablas unidas por el código INE del municipio y un diccionario de cada columna (unidad, qué es y de "
    f"dónde sale). Lo crea un comando (`python scripts/base_datos.py`), que además comprueba que la base dice lo mismo "
    f"que los ficheros de origen. Esta versión es del {meta['creada']}.\n"
    "- `municipios`: población, renta, paro, alquiler, índice de necesidad y límite de ingresos\n"
    "- `reglas` y `topes`: cada convocatoria (Bono 2022 y 2024, Ayudas 2022-2025, Plan 2026-2030 y propuesta) y su tope "
    "en cada municipio\n"
    "- `solicitudes`: Bono 2022 y Ayudas 2022-2023 por municipio\n"
    "- `alquiler_serpavi`: el alquiler de 2011 a 2024\n"
    "- `simulacion`: cada escenario del simulador\n"
    "- `fuentes`, `diccionario` y `metadatos`")
st.code("SELECT municipio, tope_hoy, tope_plan, tope_propuesta, alquiler_p75_2024\nFROM ficha_municipio\n"
        "WHERE alquiler_p75_2024 > tope_hoy\nORDER BY jovenes_20_34_2024 DESC;", language="sql")
with st.expander("Diccionario de la base"):
    st.dataframe(query("SELECT tabla, columna, unidad, descripcion, fuente FROM diccionario"), hide_index=True,
                 width="stretch", column_config={"tabla": "Tabla", "columna": "Columna", "unidad": "Unidad",
                                                 "descripcion": "Qué es", "fuente": "De dónde sale"})

st.subheader("Descargas")
with st.container(horizontal=True):
    st.download_button("Base de datos (SQLite)", DB.read_bytes(), DB.name, "application/vnd.sqlite3",
                       icon=":material/database:")
    st.download_button("Indicadores por municipio (CSV)", (INTERIM / "municipios_2024.csv").read_bytes(),
                       "municipios_2024.csv", "text/csv", icon=":material/table:")
    st.download_button("Reparto simulado por regla (CSV)", (INTERIM / "simulador_municipios.csv").read_bytes(),
                       "simulador_municipios.csv", "text/csv", icon=":material/table:")
    st.download_button("Resultado del contraste (JSON)", (RES / "contraste_real.json").read_bytes(),
                       "contraste_real.json", "application/json", icon=":material/data_object:")

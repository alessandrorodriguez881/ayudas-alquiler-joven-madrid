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
geo = result("espacial")
less = lambda new, old: es(100 * (1 - new / old))  # noqa: E731  (% less deviance)
room_cv = less(cv["controles_habitaciones"]["deviance_without_madrid"], cv["controles_tope_real"]["deviance_without_madrid"])
room_ay = less(ay["controles_habitaciones"]["deviance"], ay["controles_tope_real"]["deviance"])
mor, h1_geo = geo["moran_pearson_residuals"], geo["beta_share_above_real_cap"]["M1"]
zone_out = geo["spatial_cv"]["leave_one_zone_out"]
ci_pct = lambda block: f"del {es(-block['pct_per_10_points_ci95'][1], 1)} % al {es(-block['pct_per_10_points_ci95'][0], 1)} %"  # noqa: E731

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
    f"piso (hasta 900 €, o 1.350 € donde el tope es de 900 €), el efecto sigue siendo negativo y el modelo ajusta mejor "
    f"(desviación {es(rooms['mix_flat_and_3_sharers_rooms']['1.0']['deviance'])}, frente a "
    f"{es(rooms['real_cap']['deviance'])} con el tope del piso). Lo vimos después de mirar los datos, así que lo "
    f"comprobamos con municipios que el modelo no ha visto (abajo).\n"
    f"- **Con municipios que el modelo no ha visto** (exploratorio): saber qué parte del alquiler pasa del tope baja el "
    f"error típico de las solicitudes del {es(cv['controles']['median_abs_pct_error_10_or_more'])} % al "
    f"{es(cv['controles_tope_real']['median_abs_pct_error_10_or_more'])} % (dejando fuera un municipio cada vez). Y el "
    f"modelo del simulador, con el tope y los 900 € juntos, entrenado con el Bono 2022 predice las Ayudas para jóvenes de "
    f"2023, otro programa y otro año, con un {es(100 * (1 - ay['controles_ambas']['deviance'] / ay['controles']['deviance']))} % "
    f"menos de desviación que sin esas dos partes (correlación de {es(ay['controles']['spearman_rate'], 2)} a "
    f"{es(ay['controles_ambas']['spearman_rate'], 2)}). El umbral de 900 € igual para todos también predice bien: el "
    f"alquiler caro frena por sí solo. La medida de las habitaciones es la que mejor predice: frente al tope del piso, "
    f"la desviación baja un {room_cv} % en los municipios que el modelo no ha visto (sin contar Madrid capital: cuando la "
    f"dejamos fuera, esta medida la predice peor) y un {room_ay} % en las Ayudas de 2023. También gana a un umbral de "
    f"1.350 € igual para todos.\n"
    f"- **Los vecinos y las zonas** (exploratorio): los municipios vecinos piden de forma parecida (I de Moran de "
    f"{es(mor['requests_per_young_log']['I'], 2)}; p = {es(mor['requests_per_young_log']['p_one_sided'], 3)}), pero lo que el "
    f"modelo no explica ya no se parece entre vecinos ({es(mor['M1']['I'], 2)}; p = {es(mor['M1']['p_one_sided'], 2)}). "
    f"Si dejamos que los errores de los municipios a menos de 30 km se parezcan (errores de Conley), el intervalo va "
    f"{ci_pct(h1_geo['conley_30km'])} menos, casi el mismo que el registrado ({ci_pct(h1_geo['hc1'])}). Comparando solo "
    f"municipios de la misma zona estadística (las 11 "
    f"del portal), el efecto es algo mayor: un {es(-h1_geo['zone_fixed_effects']['pct_per_10_points'], 1)} % menos. Y "
    f"dejando fuera una zona entera cada vez, saber qué parte del alquiler pasa del tope sigue mejorando la predicción "
    f"(sin Madrid capital, la desviación baja de {es(zone_out['controles']['deviance_without_madrid'])} a "
    f"{es(zone_out['controles_tope_real']['deviance_without_madrid'])})."
)
st.image(str(RES / "figuras" / "contraste_todas_las_pruebas.png"),
         alt="Todas las estimaciones del efecto del tope, también las que no salieron, con sus intervalos")

limit = result("requisito_ingresos")["plan_limit_5iprem"]
more = limit["returns_let_in_vs_3iprem"]["by_group_weighted_by_young"]
plan = result("simulador_reparto")["plan_income_limit"]
chance = lambda p: es(100 * plan[p]["plan_estatal"]["chance_of_aid"])  # noqa: E731
high = lambda p, rule: es(plan[p][rule]["aids_per_1000_young_by_group"]["resto, necesidad alta"], 1)  # noqa: E731
st.subheader("Lo que cambia con el Plan 2026-2030 (simulación, con 31,8 M€)")
st.markdown(
    f"- **Paga más por ayuda:** hasta 300 € al mes y nunca más del 60 % del alquiler (art. 137). Con el mismo dinero "
    f"salen {es(plan['p_0']['plan_estatal']['aids'])} ayudas, no 5.300.\n"
    f"- **Deja entrar a más gente:** ingresos de hasta 5 × IPREM de la persona ({es(limit['threshold_eur_year_2024'])} € al "
    f"año), no 3 × IPREM del hogar (25.200 €) (art. 133.1.d). En las declaraciones del IRPF son "
    f"{es(limit['returns_let_in_vs_3iprem']['all_weighted_by_young'], 2)} veces más personas, y más donde la renta es alta: "
    f"{es(more['resto, necesidad baja'], 2)} veces en el tercio de menos necesidad y {es(more['resto, necesidad alta'], 2)} "
    f"en el de más (exploratorio: son declaraciones de todas las edades).\n"
    f"- **Por orden de llegada, como hoy:** de cada 100 que la piden, hoy la consiguen unos "
    f"{es(100 * plan['chance_today'])}. Con el Plan, unos {chance('p_0')} si la piden los mismos que en 2022, y unos "
    f"{chance('p_0.5')} o {chance('p_1')} si la pide también la mitad o el total de los que entran nuevos. Y las ayudas se "
    f"van un poco hacia los municipios ricos: el tercio de más necesidad baja de {high('p_0', 'plan_estatal')} a "
    f"{high('p_1', 'plan_estatal')} ayudas por cada 1.000 jóvenes.\n"
    f"- **Con cupos por necesidad (la propuesta),** ese tercio recibe {high('p_0', 'necesidad_requisito_plan_p75_hasta_1000')} "
    f"pida quien pida: los cupos no dependen de quién llega antes."
)

st.subheader("Para quién es y cuánto cuesta mantenerlo")
st.markdown(
    "- **La Consejería de Vivienda:** el Plan 2026-2030 le deja subir el tope si lo justifica con un estudio actualizado "
    "de la oferta de alquiler (art. 135). Este proyecto le da la base de ese estudio, repetible con un comando (de los 63 "
    "municipios pequeños donde proponemos subir el tope de 500 €, en 46 se puede justificar con los datos), y el "
    "simulador le deja probar topes y cupos antes de sacar la convocatoria, con su coste.\n"
    "- **Ayuntamientos y oficinas de juventud:** la ficha de cada municipio, «¿Dónde me llega la ayuda?» y la calculadora, "
    "para orientar a quien pregunta.\n"
    "- **Los jóvenes:** saber en dos minutos si pueden pedirla, cuánto cobrarían y dónde les llega.\n"
    "- **Asistentes de IA:** el servidor MCP responde con nuestras cifras y cita la fuente de cada una.\n\n"
    "**Mantenerlo cuesta casi nada:** el código es abierto (MIT) y los datos, públicos. Cuando el portal o el SERPAVI "
    "publican un año nuevo, se descarga y se vuelven a ejecutar los scripts; las pruebas automáticas avisan si algo "
    "cambia (`probar_app.py`, `probar_reglas.py`, `probar_servidor.py`). La app puede funcionar en un servicio gratuito "
    "como Streamlit Community Cloud, y la base de datos es un solo fichero de medio megabyte.\n\n"
    "**Límites:** el SERPAVI solo ve los alquileres declarados en el IRPF y llega hasta 2024; el efecto del tope sobre las "
    "solicitudes es una asociación entre municipios, no un experimento; la parte de la gente por debajo del límite de "
    "ingresos sale de declaraciones de todas las edades; y en la base del estudio del art. 135, el supuesto b) depende de "
    "medir la subida con la mediana del SERPAVI: con el índice de precios del alquiler del portal no se cumpliría en "
    "ninguno de los municipios grandes que lo tienen."
)

st.subheader("Datos")
st.table({
    "Fuente": ["Portal de Datos Abiertos de la Comunidad de Madrid", "SERPAVI, Ministerio de Vivienda y Agenda Urbana",
               "Base de Datos Nacional de Subvenciones"],
    "Qué usamos": ["Bono Alquiler Joven 2022 (solicitudes, aceptadas y rechazadas por municipio); Ayudas al alquiler para "
                   "jóvenes; población por edad; renta disponible; declaraciones del IRPF por tramo; paro registrado por "
                   "edad; Censo 2021 (viviendas en alquiler); alquiler medio e índices de precios del alquiler (para "
                   "comprobar el SERPAVI, también por distritos); límites de los municipios y de los distritos de Madrid",
                   "Alquiler mediano, p25 y p75 por municipio, de 2011 a 2024, y por distrito de Madrid (2024)",
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
    "- `alquiler_distritos_madrid`: el mismo alquiler en los 21 distritos de Madrid capital\n"
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

# Diccionario de `data/interim/municipios.csv`

Una fila por municipio del CSV del Bono Alquiler Joven 2022 (159). La genera `scripts/preparar_datos.py` a partir de `data/raw/` (cada carpeta trae su `metadata.json` con la fuente y la licencia). Tablas auxiliares: `serpavi_madrid_municipios.csv` y `serpavi_madrid_distritos.csv` (SERPAVI 2011-2024 de la Comunidad de Madrid en formato largo: `n`, `med`, `p25`, `p75` por año).

| Columna | Qué es | Fuente |
|---|---|---|
| `ine` | Código INE del municipio (3 cifras) | Bono (portal) |
| `municipio` | Nombre, tal como viene en el CSV del Bono | Bono (portal) |
| `cap` | Tope de alquiler del Bono: 900 € en los 29 municipios del Anexo II del Acuerdo de 14-sep-2022 y 600 € en el resto | Acuerdo (`docs_oficiales/`) |
| `bono_solicitudes`, `bono_aceptadas`, `bono_rechazadas` | Bono Alquiler Joven 2022 | `spacm_bono_alquiler_joven_2022` |
| `ayudas51_solicitudes`, `ayudas51_aceptadas` | Ayudas al alquiler para jóvenes (programa 5.1), 2022 + 2023 | `spacm_ayudas_alquiler_…` |
| `ayudas2_solicitudes`, `ayudas2_aceptadas` | Ayudas al alquiler para escasos recursos y mayores de 65 (programa 2), 2022 + 2023 | `spacm_ayudas_alquiler_…` |
| `pob_total_2022` | Población total, 2022 | `poblacion_censada_por_edad_nacionalidad_y_sexo` |
| `jovenes_20_34_2022` | Población de 20 a 34 años, 2022 (no hay tramo de 18 a 35) | idem |
| `jovenes_15_24_2022` | Población de 15 a 24 años, 2022 | idem |
| `renta_pc_2022` | Renta disponible bruta per cápita, 2022 (€) | `irpf_indicador_renta` |
| `paro_menor25_2022` | Parados registrados menores de 25 años, media de los 12 meses de 2022 | `paro_registrado_edad_municipio` (cruce por nombre; «de»/«del» ignorados) |
| `paro25_por_1000_15_24` | `paro_menor25_2022` por cada 1.000 jóvenes de 15 a 24 | calculado |
| `hogares_alquiler_2021`, `hogares_total_2021`, `pct_alquiler_2021` | Hogares (viviendas principales) de alquiler, total y % (Censo 2021; redondeados a múltiplos de 3) | `censo_2021_viviendas_familiares_por_tenencia` |
| `serpavi_{n,med,p25,p75}_{2022,2023}` | Viviendas colectivas en alquiler y alquiler mensual mediano, p25 y p75 (€) | SERPAVI (MIVAU) |
| `share_above_cap_{año}` | Parte estimada del mercado por encima del tope **del municipio** (log-normal ajustada a p25 y p75) | calculado |
| `share_above_600_{año}`, `share_above_900_{año}` | Lo mismo con un tope igual para todos (para la comprobación con topes falsos) | calculado |
| `alq_medio_portal_2023` | Alquiler medio mensual de viviendas habituales, solo municipios de más de 20.000 habitantes (€) | `alquiler_medio_mensual_…_mas_20000` |

**Cobertura (2-nov):** SERPAVI 2022 en 133 de 159; paro en 159; hogares en 158; alquiler del portal en 37. Con todas las variables del modelo M1: **132 municipios** (48.298 de 48.383 solicitudes).

# Diccionario de `data/interim/topes_900_convocatorias.csv` (6-nov)
Una fila por municipio de la Comunidad (179). Sale de `scripts/topes_convocatorias.py`, que lee la lista de municipios con tope de 900 € en el texto oficial de cada convocatoria (ver `docs_oficiales/FUENTES.md`).

| Columna | Qué es | Fuente |
|---|---|---|
| `ine`, `ine5`, `nombre_estadistica_cm` | Código INE (3 y 5 cifras) y nombre oficial | `codigos_municipios.csv` |
| `tope_bono_2022` | Tope del Bono Alquiler Joven 2022: 900 en los 29 del Anexo II, 600 en el resto (€/mes, vivienda) | Acuerdo de 14-sep-2022 |
| `tope_ayudas_2022`, `tope_ayudas_2023` | Tope de las Ayudas al alquiler (programa de jóvenes) de 2022 y 2023: la misma lista de 29 | Anexo I de las convocatorias (BDNS 654786 y 721190) |
| `tope_ayudas_2024`, `tope_ayudas_2025` | Lo mismo en 2024 y 2025: **55 municipios** con 900 € | Anexo I (BDNS 793423 y 864406) |
| `tope_bono_2024` | Tope del Bono Alquiler Joven 2024 (solicitudes desde el 3-feb-2025): los mismos 55 | Anexo II del Acuerdo de 26-dic-2024 (certificado en BDNS 805618) |
| `sube_a_900_en_2024` | `True` en los **26 municipios** que pasan de 600 a 900 € entre 2023 y 2024 | calculado |

Las familias numerosas tienen 900 € en todos los municipios en las Ayudas al alquiler; esta tabla recoge el tope general.

# Diccionario de `data/interim/municipios_2024.csv` (7-nov, periodo de desarrollo)
Una fila por municipio (179). Sale de `scripts/necesidad_2024.py`. **No la usa el contraste preregistrado**: es la versión 2024 para el producto (índice de necesidad y simulador). Renta y paro salen de `data/raw_2026-11-06/`; población, Censo y SERPAVI, de `data/raw/`.

| Columna | Qué es | Fuente |
|---|---|---|
| `ine`, `municipio` | Código INE de 3 cifras y nombre oficial | `topes_900_convocatorias.csv` |
| `tope_2022`, `tope_2024` | Tope del Bono 2022 (29 municipios con 900 €) y del Bono 2024 (55) | idem |
| `sube_a_900_en_2024` | `True` en los 26 que pasan de 600 a 900 € | idem |
| `pob_total_2024`, `jovenes_20_34_2024`, `jovenes_15_24_2024` | Población total y por edad, 2024 | `poblacion_censada_por_edad_nacionalidad_y_sexo` |
| `renta_pc_2024` | Renta disponible bruta per cápita, 2024 (€) | `irpf_indicador_renta` (descarga del 6-nov) |
| `paro_menor25_2024`, `paro25_por_1000_15_24_2024` | Parados menores de 25 (media de los 12 meses de 2024) y por cada 1.000 jóvenes de 15 a 24 | `paro_registrado_edad_municipio` (descarga del 6-nov) |
| `pct_alquiler_2021` | % de hogares de alquiler (Censo 2021) | `censo_2021_viviendas_familiares_por_tenencia` |
| `serpavi_{n,med,p25,p75}_{2023,2024}` | Viviendas colectivas en alquiler y alquiler mensual mediano, p25 y p75 (€) | SERPAVI (MIVAU) |
| `share_above_tope_2022_en_2024`, `share_above_tope_2024_en_2024` | Parte del mercado de 2024 por encima del tope con la lista de 2022 y con la de 2024 | calculado |
| `share_above_1000_2024` | Parte del mercado de 2024 por encima de 1.000 € (tope general del Plan Estatal 2026-2030) | calculado |
| `share_above_600_2023` | Parte del mercado de 2023 por encima de 600 € (lo que podía ver la Comunidad al ampliar la lista en dic-2024) | calculado |
| `esfuerzo_alquiler_2024` | 12 × alquiler mediano 2024 / renta per cápita 2024 | calculado |
| `rango_*` | Rango percentil (0-1) de cada componente entre los municipios con los tres | calculado |
| `indice_necesidad` | **Índice de necesidad (0-100):** media de los rangos de esfuerzo de alquiler, paro juvenil y % de hogares de alquiler. Hay valor en 136 municipios (99,6 % de los jóvenes de 20 a 34) | calculado |
| `tercil_necesidad` | baja / media / alta (tercios de municipios, no de población) | calculado |
| `bono_solicitudes`, `bono_aceptadas`, `jovenes_20_34_2022`, `share_above_cap_2022` | Datos del Bono 2022, base del simulador | `municipios.csv` |

# Diccionario de `data/interim/simulador_municipios.csv` (7-nov)
Una fila por municipio del simulador (132; 99,8 % de las solicitudes de 2022 y 99,6 % de los jóvenes de 2024). Sale de `scripts/simulador.py` con el β₁ central (−0,54: solo la parte del tope, del modelo exploratorio con el umbral de 900 €). Además de `pob_total_2024`, el índice y su tercio, `grupo_necesidad` es Madrid capital aparte y el resto en tres tercios de jóvenes por necesidad, y `share_irpf_bajo_3iprem_2024` es la parte de las declaraciones del IRPF por debajo del límite de ingresos (un municipio sin dato lleva la mediana). La regla `necesidad_requisito_plan_p75_hasta_1000` reparte por jóvenes × necesidad × esa parte. Para cada regla `<regla>`: `tope_<regla>` (€/mes), `solicitudes_<regla>` (a la escala de 2022) y `bonos_<regla>` (de los 5.300 que pagan 31,8 M€). Reglas (las del Plan Estatal 2026-2030 incluyen los 500 € de los municipios de 10.000 habitantes o menos) y supuestos, en el docstring del script; resumen con todos los β₁ en `resultados/simulador_reparto.json`.

# Diccionario de `data/interim/municipios_wgs84.geojson` (7-nov)
Límites de los 179 municipios para el mapa de la app, en WGS84 (EPSG:4326), con 4 decimales (unos 10 m). Cada `Feature` tiene `id` y `properties.ine` = código INE de 3 cifras, el mismo de los CSV. Madrid capital llega como sus 21 distritos y aquí van juntos en un solo `MultiPolygon` (código `079`). Sale de `scripts/graficos.py` a partir del shapefile «Municipios y Distritos de Madrid (2020)» del portal de datos abiertos de la Comunidad de Madrid (dataset `covid19_tia_muni_y_distritos`, CC BY 4.0, ETRS89 / UTM 30N), guardado en `data/raw_2026-11-07/`.

# `resultados/infraatendidos.json` (7-nov)
Municipios con 500 jóvenes o más, del tercio con más necesidad (índice 2024), cuya **cobertura** del Bono 2022 (bonos concedidos por cada 1.000 jóvenes de 20 a 34 años en 2022) queda por debajo de la del resto de la Comunidad sin Madrid capital. Incluye la cobertura de referencia, el corte del tercio alto, cuántos son, cuántos jóvenes viven en ellos y la lista ordenada por jóvenes. Sale de `scripts/graficos.py` (figura `resultados/figuras/cuadrante_necesidad_cobertura.png`).

# Diccionario de `data/interim/requisito_ingresos.csv` (7-nov)
Una fila por municipio con dato en el dataset «Declaraciones del IRPF por tramo base imponible. Municipios» del portal (CC BY 4.0). `share_irpf_bajo_3iprem_2021` y `share_irpf_bajo_3iprem_2024`: parte de las declaraciones con base imponible de hasta 3 veces el IPREM de 14 pagas (23.725,80 € con los ingresos de 2021, los que se miraron en el Bono 2022; 25.200 € en 2024). El tramo de 21.035 a 30.050 € se reparte en línea recta; `_min` y `_max` son los dos extremos de ese tramo. `declaraciones_2024`: total de declaraciones. Son declaraciones de todas las edades, no jóvenes: sirve para comparar municipios, no para contar cuántos jóvenes cumplen el requisito. La columna `Unidad` del portal dice «Miles euros» en el tramo de 12.020 a 18.030 €, pero es un número de declaraciones (los tramos suman el total; el script lo comprueba). Sale de `scripts/requisito_ingresos.py` (exploratorio), con el resumen en `resultados/requisito_ingresos.json`.

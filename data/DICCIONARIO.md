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

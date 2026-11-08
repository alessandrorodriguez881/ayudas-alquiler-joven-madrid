# Diccionario de `data/bono_alquiler_joven.sqlite`

Una sola base SQLite con todo lo que usa el proyecto, por municipio. La genera `scripts/base_datos.py` (este fichero también, con el mismo diccionario que va dentro de la base, en la tabla `diccionario`). La leen la app y, más adelante, el servidor MCP.

Hecha el 2026-11-08 desde el commit `26a433c (con cambios sin commit)`. Clave de municipio: `ine` (3 cifras). Vista `ficha_municipio`: los topes de hoy, del Plan y de la propuesta junto al alquiler de 2024.

```sql
SELECT municipio, tope_hoy, tope_plan, tope_propuesta, alquiler_p75_2024
FROM ficha_municipio WHERE alquiler_p75_2024 > tope_hoy ORDER BY jovenes_20_34_2024 DESC;
```

## `municipios` (179 filas)

Una fila por municipio de la Comunidad de Madrid. Clave: `ine`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `ine` | TEXT |  | Código INE del municipio, 3 cifras (provincia 28) | codigos_municipios.csv |
| `ine5` | TEXT |  | Código INE de 5 cifras | codigos_municipios.csv |
| `municipio` | TEXT |  | Nombre oficial | Instituto de Estadística de la Comunidad de Madrid |
| `pob_total_2024` | INTEGER | personas | Población total, 2024 | poblacion_censada_por_edad_nacionalidad_y_sexo |
| `jovenes_20_34_2022` | INTEGER | personas | Población de 20 a 34 años, 2022 (no hay tramo de 18 a 35) | poblacion_censada_por_edad_nacionalidad_y_sexo |
| `jovenes_20_34_2024` | INTEGER | personas | Población de 20 a 34 años, 2024 | poblacion_censada_por_edad_nacionalidad_y_sexo |
| `jovenes_15_24_2024` | INTEGER | personas | Población de 15 a 24 años, 2024 | poblacion_censada_por_edad_nacionalidad_y_sexo |
| `renta_pc_2024` | REAL | € por persona y año | Renta disponible bruta per cápita, 2024 | irpf_indicador_renta |
| `paro_menor25_2024` | REAL | personas | Parados registrados menores de 25 años, media de los 12 meses de 2024 | paro_registrado_edad_municipio |
| `paro25_por_1000_15_24_2024` | REAL | por 1.000 | Parados menores de 25 por cada 1.000 jóvenes de 15 a 24, 2024 | calculado |
| `pct_alquiler_2021` | REAL | % | Hogares (viviendas principales) de alquiler, Censo 2021 | censo_2021_viviendas_familiares_por_tenencia |
| `esfuerzo_alquiler_2024` | REAL | proporción | 12 × alquiler mediano 2024 / renta per cápita 2024 | calculado (SERPAVI y renta) |
| `indice_necesidad` | REAL | 0-100 | Índice de necesidad: media de los rangos de esfuerzo de alquiler, paro juvenil y hogares de alquiler (136 municipios con los tres) | calculado (necesidad_2024.py) |
| `tercil_necesidad` | TEXT |  | baja, media o alta (tercios de municipios) | calculado (necesidad_2024.py) |
| `grupo_necesidad` | TEXT |  | Grupo del simulador: Madrid capital aparte y el resto en tercios de jóvenes por necesidad (132 municipios) | calculado (simulador.py) |
| `parte_irpf_bajo_3iprem_2024` | REAL | proporción | Declaraciones del IRPF con base imponible de hasta 3 × IPREM (25.200 €), de todas las edades: compara municipios, no cuenta jóvenes | irpf_declaraciones_por_tramo (requisito_ingresos.py) |
| `parte_irpf_bajo_5iprem_2024` | REAL | proporción | Ídem con 5 × IPREM (42.000 €), el límite de la persona en el Plan 2026-2030; el tramo que lo contiene es ancho (30.051-60.101 €) | irpf_declaraciones_por_tramo (requisito_ingresos.py) |
| `anexo_ii_2022` | INTEGER | 0/1 | 1 si tenía tope de 900 € en el Bono 2022 (29 municipios) | Acuerdo de 14-sep-2022 |
| `anexo_ii_2024` | INTEGER | 0/1 | 1 si tiene tope de 900 € en el Bono 2024 (55 municipios) | Acuerdo de 26-dic-2024 (BDNS 805618) |
| `hasta_10000_hab` | INTEGER | 0/1 | 1 si tiene 10.000 habitantes o menos en 2024 (tope de 500 € en el Plan) | calculado |

## `reglas` (8 filas)

Cada convocatoria o regla, con lo que dice su norma. Clave: `regla`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `regla` | TEXT |  | Clave de la regla |  |
| `nombre` | TEXT |  | Nombre |  |
| `norma` | TEXT |  | Norma que la fija |  |
| `estado` | TEXT |  | Situación a 8-nov-2026 |  |
| `topes` | TEXT |  | Cómo se fija el tope del alquiler |  |
| `limite_ingresos_iprem` | REAL | veces el IPREM | Límite de ingresos anuales (NULL si no lo hemos leído en la norma) |  |
| `ingresos_que_cuentan` | TEXT |  | De quién son los ingresos que cuentan |  |
| `ayuda_max_piso` | REAL | €/mes | Ayuda máxima por persona, vivienda |  |
| `ayuda_max_habitacion` | REAL | €/mes | Ayuda máxima por persona, habitación |  |
| `ayuda_max_pct_alquiler` | REAL | % | La ayuda no pasa de este porcentaje del alquiler |  |
| `meses` | INTEGER | meses | Duración de la ayuda |  |
| `nota` | TEXT |  | Lo demás que conviene saber |  |

## `topes` (1432 filas)

Tope del alquiler por municipio y regla. Clave: `ine, regla`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `ine` | TEXT |  | Código INE del municipio |  |
| `regla` | TEXT |  | Clave de la regla (tabla reglas) |  |
| `tope_piso` | REAL | €/mes | Alquiler máximo de la vivienda entera | norma de la regla; propuesta: reglas_bono.caps |
| `tope_habitacion` | REAL | €/mes | Alquiler máximo de una habitación (NULL si no lo hemos leído en la norma) | norma de la regla; propuesta: reglas_bono.caps |

## `solicitudes` (700 filas)

Solicitudes por municipio, programa y año de convocatoria. Clave: `ine, programa, anio_convocatoria`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `ine` | TEXT |  | Código INE del municipio |  |
| `programa` | TEXT |  | bono_alquiler_joven, ayudas_alquiler_jovenes (programa 5.1) o ayudas_alquiler_escasos_recursos (programa 2) |  |
| `anio_convocatoria` | INTEGER | año | Año de la convocatoria |  |
| `solicitudes` | INTEGER | solicitudes | Solicitudes presentadas | spacm_bono_alquiler_joven_2022, spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos |
| `aceptadas` | INTEGER | solicitudes | Solicitudes aceptadas | idem |
| `rechazadas` | INTEGER | solicitudes | Solicitudes rechazadas (por requisitos o por crédito agotado) | idem |

## `alquiler_serpavi` (2506 filas)

Alquiler de vivienda colectiva por municipio y año, 2011-2024. Clave: `ine, anio`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `ine` | TEXT |  | Código INE del municipio |  |
| `anio` | INTEGER | año | Año |  |
| `viviendas` | INTEGER | viviendas | Viviendas colectivas en alquiler con declaración del IRPF | SERPAVI (MIVAU) |
| `mediana` | REAL | €/mes | Alquiler mensual mediano | SERPAVI (MIVAU) |
| `p25` | REAL | €/mes | Percentil 25 del alquiler mensual | SERPAVI (MIVAU) |
| `p75` | REAL | €/mes | Percentil 75 del alquiler mensual | SERPAVI (MIVAU) |

## `simulacion` (1320 filas)

Escenarios del simulador de reparto con el β central (−0,54) y 31,8 M€. Clave: `ine, escenario`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `ine` | TEXT |  | Código INE del municipio |  |
| `escenario` | TEXT |  | Regla del simulador (scripts/simulador.py, rules) |  |
| `reparto` | TEXT |  | llegada (orden de llegada) o cupos (jóvenes × necesidad, a veces × límite de ingresos: aquí, el de hoy, 3 × IPREM, porque son bonos de 250 €) |  |
| `tope_piso` | REAL | €/mes | Tope del piso en el escenario | simulador.py |
| `solicitudes` | REAL | solicitudes | Solicitudes esperadas con ese tope | simulador.py |
| `bonos` | REAL | bonos | Bonos que recibiría (5.300 en total) | simulador.py |
| `parte_por_encima` | REAL | proporción | Parte de los alquileres de 2024 por encima del tope | simulador.py |

## `fuentes` (8 filas)

Datos usados, con su licencia. Clave: `fuente`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `fuente` | TEXT |  | Nombre del conjunto de datos |  |
| `titulo` | TEXT |  | Título |  |
| `publica` | TEXT |  | Quién lo publica |  |
| `licencia` | TEXT |  | Licencia |  |
| `url` | TEXT |  | Dirección |  |
| `actualizado` | TEXT |  | Fecha de la última actualización según la fuente |  |
| `carpeta` | TEXT |  | Carpeta del repositorio con la copia y su metadata.json |  |

## `diccionario` (70 filas)

Cada columna de cada tabla. Clave: `tabla, columna`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `tabla` | TEXT |  | Tabla |  |
| `columna` | TEXT |  | Columna |  |
| `tipo` | TEXT |  | Tipo SQL |  |
| `unidad` | TEXT |  | Unidad |  |
| `descripcion` | TEXT |  | Qué es |  |
| `fuente` | TEXT |  | De dónde sale |  |

## `metadatos` (6 filas)

Cómo y cuándo se hizo el fichero. Clave: `clave`.

| Columna | Tipo | Unidad | Qué es | Fuente |
|---|---|---|---|---|
| `clave` | TEXT |  | Clave |  |
| `valor` | TEXT |  | Valor |  |

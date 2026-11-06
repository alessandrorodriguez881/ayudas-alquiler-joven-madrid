# DataMad 2026: trabajo hecho antes del periodo de desarrollo (para declararlo)

Proyecto: **«¿Llegan las ayudas al alquiler a quien más las necesita?»** (Bono Alquiler Joven, Comunidad de Madrid).
Periodo de desarrollo según las bases: del 7 al 26 de noviembre de 2026. Este documento recoge **todo** lo hecho antes, con fechas, para declararlo.

## Qué dicen las bases (apartado 6, «Proyectos preexistentes»)
Fuente: `docs_oficiales/BASES_DATAMAD_2026.pdf` (descargado el 27-oct de [la web oficial](https://eventos.urjc.es/155632/detail/datamad-2026.html); MD5 `da0ce349…`).
- Se puede usar código, herramientas, investigaciones o recursos hechos antes, **siempre que se identifiquen**
- Pero la propuesta tiene que **desarrollarse o evolucionar de forma sustancial** entre el 7 y el 26-nov, y no se puede presentar como nueva una solución ya terminada
- Las bases **no** prohíben explorar datos antes. Nuestra regla propia, más prudente, es: **antes del 7-nov, solo idea, datos y comprobar que la hipótesis se puede probar. Nada de producto** (ni app, ni mapa, ni índices, ni simulador)
- Otros apartados que tocan a esto: el 5 (el equipo se puede cambiar hasta el **7-nov**) y el 7 (IA permitida; el participante responde del contenido)

## Texto corto para declarar (README y diapositiva 2)
> Antes del periodo de desarrollo (21 y 27 de octubre y 2, 5 y 6 de noviembre de 2026) hicimos solo trabajo previo:
> - elegir la idea y leer la normativa del Bono Alquiler Joven
> - descargar los datos abiertos y unirlos en una tabla por municipio
> - comprobar que la hipótesis se podía probar
> - dejar escrito y probado con datos inventados el contraste estadístico, antes de verlo con los datos reales (`PREREGISTRO.md`)
> - preparar los datos para que otros los reutilicen: tabla de códigos de municipio entre fuentes, comprobación de las descargas, nota MELODA de cada dataset y la lista oficial de municipios con tope de 900 € en cada convocatoria (2022-2025)
>
> Scripts de esa fase: `descargar.py`, `explorar.py`, `viabilidad.py`, `hipotesis_tope.py`, `comun.py`, `preparar_datos.py`, `contraste.py`, `codigos_municipios.py`, `verificar_descargas.py`, `meloda.py` y `topes_convocatorias.py`. El historial del repositorio (desde el 6-nov) lo muestra con fechas.
>
> El contraste con datos reales, los índices, el mapa, el simulador, la app y la presentación se hicieron entre el 7 y el 26 de noviembre. Usamos IA (Claude, de Anthropic) para buscar fuentes y escribir código y documentos; revisamos y entendemos cada resultado.

## Registro, día a día
| Fecha | Qué se hizo | Archivos |
|---|---|---|
| 21-oct-2026 | Lectura de las bases e inscripción (individual) | `BASES_RESUMEN.md` |
| 21-oct-2026 | Tres ideas comparadas con los criterios del jurado; elegida la del Bono Alquiler Joven | `IDEAS.md`, `PLAN.md` |
| 21-oct-2026 | Descarga de 12 datasets del portal de la Comunidad | `scripts/descargar.py`, `data/raw/` |
| 21-oct-2026 | Primera comprobación: el Bono viene por municipio (159 + «Otro»), 22,2 % de aceptación, y los cruces por nombre funcionan | `scripts/explorar.py`, `scripts/viabilidad.py` |
| 27-oct-2026 | Bases releídas en el PDF original (apartado 6) y guardadas | `docs_oficiales/` |
| 27-oct-2026 | Normativa comprobada en fuentes oficiales: topes de 600 y 900 €, lista de los 29 municipios con 900 €, requisitos y regla del crédito | `docs_oficiales/` |
| 27-oct-2026 | «Datos que faltan» reunidos: alquiler por municipio (SERPAVI, Ministerio) y 3 datasets más del portal | `data/raw/serpavi_mivau/` y 3 carpetas nuevas |
| 27-oct-2026 | Exploración de viabilidad con reglas escritas antes de ejecutar | `scripts/hipotesis_tope.py`, `data/interim/exploracion_tope_municipios.csv` |
| 2-nov-2026 | Búsqueda de ediciones anteriores de DataMad y del jurado; comprobación de las reglas de las Ayudas al alquiler para jóvenes (mismos topes de 600 y 900 € que el Bono) | `PLAN.md` |
| 2-nov-2026 | **Preregistro** del contraste principal, escrito antes de ejecutar ningún modelo con datos reales, con dos enmiendas fechadas | `PREREGISTRO.md` |
| 2-nov-2026 | Tabla limpia por municipio (159 filas, 34 columnas; 132 municipios con todas las variables) y su diccionario | `scripts/preparar_datos.py`, `scripts/comun.py`, `data/interim/municipios.csv`, `data/DICCIONARIO.md` |
| 2-nov-2026 | Código del contraste, probado **solo con resultados inventados** (con efectos plantados) para comprobar que funciona y medir su potencia. **No se ha ejecutado con los datos reales:** el script lo bloquea hasta el 7-nov | `scripts/contraste.py`, `resultados/potencia_sintetica*.json` |
| 2-nov-2026 | Con la prueba de datos inventados se endureció la regla antes de ver los datos reales: la permutación pasa de p < 0,05 a **p < 0,01** porque, sin efecto, daba un 8-10 % de «sí» falsos (enmienda 4 del preregistro) | `PREREGISTRO.md` |
| 2-nov-2026 | Formato de la formación comprobado en la web oficial: híbrida, de 9:30 a 13:30 el 5 y 6-nov | `PLAN.md` |
| 5-nov-2026 | Formación del jueves (el candidato, online) y lectura del repositorio y las diapositivas del ponente | `PREGUNTAS_FORMACION.md`, `PLAN.md` |
| 5-nov-2026 | Normativa nueva comprobada: Bono 2024 (mismos topes, BOCM 10-ene-2025) y Plan Estatal de Vivienda 2026-2030 (RD 326/2026: tope de 1.000 € y art. 135) | `PLAN.md` |
| 5-nov-2026 | **Tabla de equivalencias de códigos** de los 179 municipios entre fuentes (código de la Comunidad, INE y nombres), en CSV y JSON | `scripts/codigos_municipios.py`, `data/interim/codigos_municipios.{csv,json}` |
| 5-nov-2026 | **Verificación de todas las descargas** frente al portal (filas de la API y contenido). Descubre que el portal pasó de Latin-1 a UTF-8: los scripts ahora leen las dos codificaciones, y las tablas salen idénticas byte a byte | `scripts/verificar_descargas.py`, `scripts/comun.py`, `data/VERIFICACION.md` |
| 5-nov-2026 | Nota MELODA 5 de los 15 datasets del portal (spain.meloda.org) | `scripts/meloda.py`, `data/MELODA.md` |
| 6-nov-2026 | Repositorio privado en GitHub con todo el trabajo previo (primer commit `f20f196`), README, licencia MIT y `requirements.txt`. La tabla de municipios se regenera idéntica (MD5 `f4b7b1c4…`). El contraste real sigue sin ejecutar | [repositorio](https://github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid), `README.md` |
| 6-nov-2026 | **Topes de cada convocatoria** sacados de los textos oficiales de la BDNS: 29 municipios con 900 € en el Bono 2022 y en las Ayudas 2022-2023; **55** en las Ayudas 2024-2025 y en el Bono 2024 (26 pasan de 600 a 900 €). Corrige una nota del 5-nov: el Anexo II del Bono 2024 sí estaba en la BDNS | `scripts/topes_convocatorias.py`, `data/interim/topes_900_convocatorias.csv`, `docs_oficiales/FUENTES.md` |
| 6-nov-2026 | Datos nuevos del portal en una carpeta aparte (renta e IRPF de 2024, paro hasta 2026), sin tocar la copia congelada del contraste; y el dataset de la bolsa de vivienda joven (solo contexto) | `scripts/descargar.py --destino`, `data/raw_2026-11-06/`, `data/raw/1914500/` |

## Datos reunidos
Todos son datos abiertos oficiales, cada uno en su carpeta de `data/raw/` con su `metadata.json` (título, licencia, fecha y enlace).

**Del Portal de Datos Abiertos de la Comunidad de Madrid** (licencia CC BY 4.0):
| Dataset | Para qué | Descargado |
|---|---|---|
| `spacm_bono_alquiler_joven_2022` | Solicitudes, aceptadas y rechazadas del Bono por municipio | 21-oct |
| `spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos` | Ayudas al alquiler 2022-2023 (programas 2 y 5.1): posible comparación | 21-oct |
| `poblacion_censada_por_edad_nacionalidad_y_sexo` | Jóvenes de 20 a 34 años por municipio (2021-2025, tramos de 5 años) | 21-oct |
| `paro_registrado_edad_municipio` | Paro de menores de 25 años por municipio (mensual, 2005-2026) | 21-oct |
| `irpf_indicador_renta`, `irpf_declaraciones_por_tramo` | Renta por municipio | 21-oct |
| `302038`, `grado_juventud_por_edad` | Paro total y peso de los jóvenes | 21-oct |
| `1934258`, `1934261`, `1934430`, `1934246` | Alquiler en Madrid capital (código postal y distrito) | 21-oct |
| `alquiler_medio_mensual_viviendas_arrendadas_valor_catastral_municipios_mas_20000` | Alquiler medio de los 37 municipios de más de 20.000 habitantes (2023-2024): segunda fuente del alquiler, del propio portal | **27-oct** |
| `1934445` | Índice de precios del alquiler de 54 municipios de más de 10.000 habitantes (2011-2024) | **27-oct** |
| `censo_2021_viviendas_familiares_por_tenencia` | Hogares que viven de alquiler por municipio (Censo 2021) | **27-oct** |

**Fuente externa** (permitida por las bases si se respeta su licencia):
| Dataset | Para qué | Licencia | Descargado |
|---|---|---|---|
| `serpavi_mivau`: base del Sistema Estatal de Índices de Alquiler de Vivienda 2011-2024 (Ministerio de Vivienda; 68 MB; MD5 `bff6497f…`) | Alquiler mensual mediano, percentil 25 y percentil 75 de **todos** los municipios con datos (133 de los 159 del Bono, y los 46 con ≥ 50 solicitudes) | Aviso legal del MIVAU: reutilización libre citando la fuente y la fecha de actualización (9-jul-2026) | **27-oct** |

**Los «datos que faltan» de `PLAN.md`, uno por uno:**
- Alquiler por municipio en toda la Comunidad → **conseguido** (SERPAVI 2022; el portal lo da solo para municipios grandes)
- Jóvenes por municipio → **comprobado**: ya estaba; se usa 20-34 años porque los datos vienen en tramos de 5 años (no hay 18-35 exacto)
- Paro juvenil por municipio → **comprobado**: ya estaba; el tramo es «menor de 25 años» (no hay 18-35)
- Motivos de rechazo del Bono → **justificado que no se usan**. No hay datos agregados. El listado de excluidos con su motivo está en la sede, pero es nominativo (nombres y DNI): son datos personales y no se descargan (bases, apartado 6.6)

## Normativa comprobada (fuentes oficiales, 27-oct)
- **Tope del alquiler:** 600 €/mes (300 € por habitación) en general y **900 € (450 €) en los 29 municipios del Anexo II** del Acuerdo de 14-sep-2022. La lista del Anexo coincide con la de la sede; los 29 están en el CSV del Bono
- **Requisitos (art. 4):** hasta 35 años; ingresos de **todos los que viven en la vivienda** ≤ 3 veces el IPREM (en habitación, solo los del joven)
- **Crédito (art. 9):** se aprueban las solicitudes que cumplen **mientras quede dinero**. El crédito se declaró **agotado el 6-nov-2023** (BOCM n.º 271), y la Orden de 1-ago-2024 (BOCM n.º 195) excluyó a los que no cumplían **y** a todos los que quedaban sin atender por falta de crédito
- **Consecuencia:** las 40.258 «rechazadas» del CSV mezclan incumplir requisitos y quedarse sin dinero. **No se puede decir que «4 de cada 5 no cumplían»**

## Exploración de viabilidad (27-oct)
**Reglas escritas antes de ejecutar** (en la cabecera de `scripts/hipotesis_tope.py`). La hipótesis se puede probar desde el 7-nov si:
| Regla | Resultado | ¿Pasa? |
|---|---|---|
| F1. Hay alquiler para ≥ 80 % de los municipios con ≥ 50 solicitudes | 46 de 46 (100 %) | ✅ |
| F2. ≥ 10 municipios con ≥ 50 solicitudes en cada grupo de tope | 17 con 600 € y 29 con 900 € | ✅ |
| F3. La parte del mercado por encima del tope varía (rango intercuartílico ≥ 10 puntos) | Del 6,7 % al 44,0 % (37 puntos) | ✅ |
| F4. Los dos grupos se solapan en alquiler (≥ 5 municipios por grupo en el tramo común) | Tramo de 580 a 767 €: 10 con 600 € y 18 con 900 € | ✅ |

**Conclusión: la hipótesis se puede probar.** Hay datos, hay variación y existe el «experimento natural» (mismo alquiler, distinto tope).

**Primera mirada** (solo descriptiva, prevista de antemano; se esperaba que la aceptación bajara donde más mercado supera el tope):
- La tasa de aceptación es **plana**: 23,1 % con tope de 600 € y 23,9 % con 900 €; 24,5 / 23,6 / 24,1 % por tercios de «mercado por encima del tope»; correlación −0,13
- Lectura: el tope **no** explica quién es rechazado. Encaja con lo del BOCM: muchas solicitudes se quedaron fuera porque se acabó el dinero

**Segunda mirada** (escrita después de ver la primera y antes de ejecutarla, y así se declara): si el tope actúa **antes** de pedir, habrá menos solicitudes donde más mercado lo supera.
- Solicitudes por cada 1.000 jóvenes de 20-34 años: **39,2 → 30,5 → 23,5** de menos a más mercado por encima del tope (correlación −0,53; Spearman −0,48). Por cada 1.000 hogares de alquiler: 101 → 84 → 58
- Con alquileres parecidos (tramo de 580 a 767 €): **26,6 solicitudes por cada 1.000 jóvenes con tope de 600 € frente a 39,1 con 900 €** (un 32 % menos; 67 frente a 100 por cada 1.000 hogares de alquiler)

**Lo que esto NO prueba todavía** (se trabaja del 7 al 26-nov):
- Es descriptivo y con pocos municipios (10 frente a 18 en el tramo común)
- Los municipios con tope de 600 € son más pequeños y rurales; puede pesar el tamaño, la renta, el paro o lo conocido que sea el Bono
- Madrid capital es el 64 % de las solicitudes con municipio (30.961 de 48.383) y el Bono no viene por distrito
- La parte del mercado por encima del tope se estima suponiendo alquileres log-normales a partir de los percentiles 25 y 75 del SERPAVI 2022

## Lo que NO se ha hecho antes del 7-nov
- Ni producto, ni app, ni mapa, ni índice de necesidad o cobertura, ni simulador, ni presentación
- **El modelo estadístico con controles no se ha ejecutado con los datos reales.** Está programado y probado con datos inventados; el resultado real sale a partir del 7-nov
- No hay repositorio público todavía
- Las tablas de `data/interim/` son datos preparados, no el producto

## Código y recursos previos que se reutilizan (para declararlos)
- Los 10 scripts de `scripts/` (21 y 27-oct, 2 y 5-nov), descritos arriba, y el preregistro
- Método de trabajo propio de competiciones anteriores (fijar reglas antes de mirar los datos, validar con datos reservados): es una forma de trabajar, no código
- Ningún código de otros hackathones (Airwallex, PayPal, SAS, Name That LLM, NFL) se usa en DataMad

## Uso de IA
- Claude (Anthropic), con supervisión del participante, para: buscar y comprobar fuentes oficiales, descargar los datos, escribir los scripts de exploración y redactar estos documentos
- Las bases lo permiten de forma expresa (apartado 7). El participante revisa cada resultado y responde de él

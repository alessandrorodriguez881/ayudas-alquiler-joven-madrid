# Los invisibles del Bono

**¿Llegan las ayudas al alquiler a quien más las necesita?** Los invisibles son los jóvenes cuyo alquiler pasa del tope del Bono Alquiler Joven: si no lo piden, no salen en sus estadísticas, ni siquiera entre los rechazados.

**La app:** [invisibles-del-bono.streamlit.app](https://invisibles-del-bono.streamlit.app), publicada el 12-nov-2026.

Proyecto para **DataMad 2026** (URJC, UCM y Comunidad de Madrid), sobre el **Bono Alquiler Joven** en la Comunidad de Madrid. El periodo de desarrollo va del 7 al 26 de noviembre de 2026.

## En 30 segundos
- **El hallazgo: −7,6 % de solicitudes cuando 10 de cada 100 alquileres más pasan del tope.** Es un contraste registrado antes de hacerlo ([PREREGISTRO.md](PREREGISTRO.md)). No decimos que el tope sea la única causa: separando el alquiler caro en sí (un análisis hecho después), la parte del propio tope es un −5,3 %, la que usa el simulador.
- **Lo que viene: el 58 % de los alquileres, fuera.** El Plan Estatal 2026-2030 pone el tope en 500 € en los municipios de 10.000 habitantes o menos. Allí quedaría por encima el 58 % de los alquileres; hoy, el 26 %. Y no solo en Madrid: con el mismo código, 1.132.424 personas viven en 209 pueblos de ocho comunidades donde ese tope dejaría fuera más de la mitad del alquiler, y Madrid es la 2.ª donde más pesa, después de Baleares ([en toda España](data/ESPANA_TOPE500.md)).
- **La propuesta: +41 % de ayudas en los municipios con más necesidad fuera de Madrid capital, con el mismo dinero.** Topes según el alquiler de cada municipio (sube en 63 pueblos, con la base del estudio que permite el art. 135 del Plan) y el dinero repartido por necesidad en 4 bolsas, no solo por orden de llegada ([cómo se aplica](data/COMO_SE_APLICA.md)). Madrid capital, que hoy recibe más ayudas por joven que el resto y también tiene mucha necesidad, recibe un 11 % menos.
- **Para usarlo hoy:** la [app](https://invisibles-del-bono.streamlit.app), la [base del estudio del art. 135](data/ESTUDIO_ART135.md), una base SQLite con su diccionario, una ficha DCAT-AP-ES, los indicadores como Smart Data Models y un servidor MCP. **Todo se rehace con un comando.**

## Pruébalo
```bash
pip install -r requirements.txt                 # Python 3.12
streamlit run app/streamlit_app.py              # la app, en local
python scripts/rehacer_todo.py --comprobar      # rehace todos los resultados (unos 6 min) y dice si algo cambia
```
GitHub repite ese último comando en Linux en cada subida, con todas las pruebas, y enseña en qué se diferencia de los resultados del repositorio ([comprobaciones](https://github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid/actions/workflows/comprobar.yml)).

## La pregunta
El Bono Alquiler Joven (RD 42/2022) da 250 € al mes, pero solo si el alquiler no pasa de **600 €**, o de **900 €** en los 29 municipios del Anexo II del Acuerdo del Consejo de Gobierno de 14-sep-2022.

Donde casi todos los pisos cuestan más que el tope, ¿piden la ayuda menos jóvenes? Si es así, el tope no solo rechaza: también **frena las solicitudes**. Y eso no se ve en el número de solicitudes rechazadas, porque quien no llega al tope ni siquiera la pide.

El nuevo Plan Estatal de Vivienda 2026-2030 (RD 326/2026, art. 133.1.e) pone el tope en 1.000 €, o en **500 € en los municipios de 10.000 habitantes o menos**, y deja que cada comunidad lo suba si lo justifica con estudios actualizados de la oferta de alquiler (art. 135). Este proyecto quiere ser una base abierta y repetible para ese estudio en la Comunidad de Madrid.

## Resultados
Una línea por resultado. Cada uno tiene su script y su fichero en `resultados/`; el detalle, con los intervalos, está en **[ANALISIS.md](ANALISIS.md)**. «Exploratorio» quiere decir que no estaba en el preregistro.

**Registrado antes de hacer el contraste**
- **El contraste (7-nov):** por cada 10 puntos más de alquileres por encima del tope, un 7,6 % menos de solicitudes del Bono por joven (del 3,9 % al 11,1 %). Cumple las tres condiciones fijadas antes.
- **Lo que no salió:** un umbral de 900 € igual para todos explica las solicitudes mejor que el tope real, así que una parte es el alquiler caro en sí. Separando las dos cosas (después), la parte del tope es un −5,3 % por cada 10 puntos (del −8,5 % al −2,0 %).
- **Una predicción para 2024, escrita antes de tener los datos:** en los 26 municipios que pasaron de 600 a 900 € en 2024, las solicitudes crecerán de 2022 a 2024 un 30 % más que en los que siguieron con 600 € (del 10 % al 53 %). Se sabrá cuando se publiquen.

**Exploratorio: ¿aguanta?**
- **La franja de 600 a 900 €, como placebo:** apunta al tope en la dirección; el tamaño no es fiable.
- **Antes del cambio de 2024,** esos 26 municipios no venían creciendo más: un 16 % menos, de −37 % a +13 %, que no se distingue de cero.
- **El límite de ingresos no lo explica:** con él como control, −7,4 %, y la parte del tope sigue en −5,3 %.
- **Las habitaciones** (con tope de 300 o 450 €) pueden explicar por qué el umbral de 900 € ajustaba mejor. Es la medida que mejor predice.
- **El mismo municipio en 2022 y en 2023:** con esos datos no se puede saber (0, del −25 % al +34 %).
- **Con municipios y un programa que el modelo no ha visto,** el error típico baja del 21 % al 18 %, y predice las Ayudas para jóvenes de 2023 con un 27 % menos de desviación.
- **Los vecinos y las zonas:** lo que el modelo no explica no se parece entre vecinos (I de Moran de 0,03; p = 0,24). Con errores de Conley, el intervalo va del −10,9 % al −4,1 %.
- **¿El simulador reparte como el Bono de verdad?** Con las aceptadas de 2022, sí: Madrid capital se llevó el 63,8 % y el simulador le da el 65,3 %; por municipio, la correlación de rangos es de 0,95.

**Exploratorio: el Plan 2026-2030 y la propuesta**
- **Las reglas del Plan, leídas en el BOE:** con su cuantía, de hasta 300 €, los 31,8 M€ dan unas 4.420 ayudas, no 5.300. Con los cupos de la propuesta, el tercio de municipios con más necesidad recibe 4,3 ayudas por cada 1.000 jóvenes: un 41 % más que con el Plan tal cual (del 34 % al 48 %).
- **Midiendo la necesidad de otras 8 formas,** ese tercio recibe siempre más que con el Plan: entre un 31 % y un 52 % más. La lista sí cambia, así que la fórmula tiene que fijarse en la convocatoria.
- **El 58 %, con pueblos de pocos contratos:** leyendo el alquiler de otras dos formas, el mismo 58 %; sin los de menos de 30 contratos, el 59 %, y sin los de menos de 100, el 65 %. El 58 % es la cifra prudente.
- **En el resto de España,** Madrid es la 2.ª de las 14 comunidades con datos suficientes, después de Baleares ([data/ESPANA_TOPE500.md](data/ESPANA_TOPE500.md)).
- **¿Quién publica el Bono por municipio?** En datos abiertos, que sepamos, solo Madrid, y solo de 2022. De 2024 hay un avance en PDF, en una respuesta del Gobierno a la Asamblea, con las ayudas concedidas y no las solicitudes. Los datos existen: se envían al Ministerio cada semestre, por municipio (RD 42/2022, art. 134) ([data/BONO_POR_COMUNIDADES.md](data/BONO_POR_COMUNIDADES.md)).
- **En una convocatoria abierta todo el año,** como pide el Plan, la propuesta reparte el dinero en 4 bolsas por necesidad y, dentro de cada una, por orden de llegada. El tercio con más necesidad recibe un 40,8 % más que con el Plan tal cual; pierden Madrid capital (309 ayudas, un 10,7 % menos) y el tercio con menos necesidad (12 ayudas) ([data/COMO_SE_APLICA.md](data/COMO_SE_APLICA.md)).
- **Madrid capital, por distritos:** si su bolsa se reparte por la necesidad de sus distritos, los que más la necesitan (Puente de Vallecas, Usera, Villaverde…) reciben un 2,2 % más que con el Plan, en vez de perder ([data/DISTRITOS_CIFRA3.md](data/DISTRITOS_CIFRA3.md)).
- **La base del estudio del art. 135:** la propuesta sube el tope en 63 municipios pequeños (46.458 jóvenes), y hay base en los datos en 49 (42.485 jóvenes). No es el estudio oficial: decidir y acordarlo con el Ministerio le toca a la Comunidad ([data/ESTUDIO_ART135.md](data/ESTUDIO_ART135.md)).
- **Una extrapolación:** si en 2022 el tope hubiera cubierto todo el alquiler, el modelo da unas 9.300 solicitudes más, sobre 48.300 (de 3.200 a 16.300). Sale de una asociación entre municipios, no de un efecto causal probado.

## Qué hay en el repositorio
- **La app** (`app/`): «¿Puedo pedirla?», «¿Dónde me llega la ayuda?», el mapa, la ficha de cada municipio, el simulador para la Consejería, «¿Cómo se aplica?» y el método. Lee la base de datos y usa las mismas funciones que los scripts, así que sus cifras son las mismas.
- **La base de datos** (`data/bono_alquiler_joven.sqlite`, 0,6 MB): 10 tablas unidas por el código INE, con un diccionario de cada columna ([data/DICCIONARIO_BASE_DE_DATOS.md](data/DICCIONARIO_BASE_DE_DATOS.md)).
- **El servidor MCP** (`servidor_mcp/`): seis herramientas de solo lectura para que un asistente de IA consulte nuestras cifras, y cada respuesta trae sus fuentes. GitHub lo prueba con el cliente oficial de MCP en cada subida. Lo probamos con modelos de verdad, con lo esperado escrito antes: con dos de Claude (Sonnet y Haiku), las 7 cifras bien y con su fuente; con uno abierto pequeño en local (Llama 3.2 de 3.200 millones), ninguna ([la prueba, también lo que no salió como esperábamos](servidor_mcp/PRUEBA_CON_MODELO.md)).
- **La ficha DCAT-AP-ES** (`data/dcat_ap_es.ttl`), comprobada con las plantillas SHACL oficiales de datos.gob.es: cumple todo salvo el publicador, que tiene que ser un organismo con código DIR3.
- **Smart Data Models** (`data/smart_data_models/`): los indicadores de cada municipio como 739 entidades KeyPerformanceIndicator, validadas con el esquema oficial.
- **El trabajo previo, declarado** ([TRABAJO_PREVIO.md](TRABAJO_PREVIO.md)), y los preregistros ([PREREGISTRO.md](PREREGISTRO.md) y [PREREGISTRO_DISTRITOS.md](PREREGISTRO_DISTRITOS.md)). Las notas internas de planificación no están en el repositorio.

Cada pieza, en detalle: [ANALISIS.md](ANALISIS.md), «Lo que entregamos».

## Cómo repetirlo
Python 3.12 (probado con 3.12.10). `requirements.txt` fija las versiones exactas con las que se ha probado todo; NumPy 1.26 no tiene versión para Python 3.13 o posterior.

Todo, en orden y con un comando. Si un paso falla, se para y enseña el error; con `--comprobar`, al final dice si algún resultado del repositorio ha cambiado:

```bash
pip install -r requirements.txt
python scripts/rehacer_todo.py --comprobar
```

En Windows da exactamente lo mismo. En Linux (GitHub, 17-nov), todo sale igual salvo cuatro números de análisis exploratorios, que cambian a partir de la quinta cifra: el ajuste de las habitaciones (−0,70868 frente a −0,70870) y tres extremos de intervalos (del panel 2022-2023 y del placebo), hacia la novena. GitHub lo comprueba en cada subida (`scripts/comparar_con_tolerancia.py`). Los ficheros de texto se guardan con finales de línea LF (`.gitattributes`), así que la comparación mira el contenido, no los finales de línea. Los datos descargados (`data/raw*/`) se guardan byte a byte, como vinieron, porque sus huellas se comparan con las del portal. Las figuras (PNG) salen aparte: usan la fuente Segoe UI, o DejaVu Sans donde no está, así que sus píxeles cambian de un sistema a otro.

<details>
<summary>Los pasos, uno a uno (también se pueden lanzar por separado)</summary>

```bash
python scripts/preparar_datos.py          # data/interim/municipios.csv (159 municipios)
python scripts/potencia_umbral.py         # tabla de potencia del preregistro, con las simulaciones guardadas
python scripts/contraste.py               # contraste real (a partir del 7-nov-2026)
python scripts/exploratorio_topes_falsos.py  # exploratorio, no preregistrado: los topes falsos, más de cerca
python scripts/placebo_franja.py            # exploratorio: la franja de 600 a 900 €, como placebo
python scripts/necesidad_2024.py          # tabla de 2024 e índice de necesidad (desarrollo)
python scripts/requisito_ingresos.py      # exploratorio: el límite de ingresos (3 × IPREM) con el IRPF por tramos
python scripts/habitaciones.py            # exploratorio: los topes de las habitaciones (300 / 450 €; Plan, 600 / 250 €)
python scripts/panel_ayudas.py            # exploratorio: el mismo municipio en 2022 y 2023 (Ayudas para jóvenes)
python scripts/validacion_fuera_muestra.py  # exploratorio: el modelo con municipios y un programa que no ha visto
python scripts/simulador.py               # reparto de los 5.300 bonos (31,8 M€) con distintas reglas
python scripts/prediccion_2024.py         # predicción para 2024, escrita antes de tener los datos
python scripts/tendencias_2024.py         # exploratorio: antes del cambio de 2024, placebo 2022-2023 y potencia
python scripts/espacial.py                # exploratorio: vecinos y zonas (I de Moran, errores de Conley, validación por zonas)
python scripts/robustez_indice.py         # exploratorio: el +41 % de la propuesta, midiendo la necesidad de otras 8 formas
python scripts/robustez_pueblos.py        # exploratorio: el 58 % de los pueblos, leyendo el alquiler de otras formas
python scripts/espana_tope500.py          # exploratorio: el tope de 500 € del Plan en toda España (data/ESPANA_TOPE500.md)
python scripts/como_se_aplica.py          # exploratorio: la propuesta en una convocatoria abierta todo el año (data/COMO_SE_APLICA.md)
python scripts/probar_reglas.py           # las reglas de la calculadora, con casos hechos a mano
python scripts/distritos_madrid.py        # los 21 distritos de Madrid: su forma para el mapa y sus nombres
python scripts/distritos_cifra3.py        # exploratorio: la cifra 3 con Madrid capital por distritos (data/DISTRITOS_CIFRA3.md; la primera vez descarga 76 MB)
python scripts/base_datos.py              # la base SQLite (data/bono_alquiler_joven.sqlite) y su diccionario
python scripts/ficha_dcat.py              # ficha DCAT-AP-ES (data/dcat_ap_es.ttl), comprobada con SHACL
python scripts/smart_data_models.py       # los indicadores como Smart Data Models, validados con el esquema oficial
python servidor_mcp/probar_servidor.py    # arranca el servidor MCP y prueba sus herramientas
python scripts/graficos.py                # figuras (resultados/figuras/) y mapa municipal para la app
python scripts/validar_serpavi.py         # el SERPAVI frente a los alquileres del propio portal
python scripts/incidencias_portal.py      # incidencias en los datos oficiales (data/INCIDENCIAS_PORTAL.md)
python scripts/estudio_art135.py          # base del estudio del art. 135 para subir el tope de 500 € (data/ESTUDIO_ART135.md)
streamlit run app/streamlit_app.py        # la app, en http://localhost:8501
python app/probar_app.py                  # prueba todas las páginas de la app sin navegador
```

Dos pasos que no hace falta repetir, porque su resultado ya está en el repositorio:
- `scripts/codigos_municipios.py` y `scripts/topes_convocatorias.py` sacan los códigos INE y los topes de 600 / 900 € de cada convocatoria (29 municipios en 2022, 55 en 2024) de los PDF oficiales, que no se suben: sus enlaces y huellas están en [docs_oficiales/FUENTES.md](docs_oficiales/FUENTES.md). Con los PDF en `docs_oficiales/`, regeneran `data/interim/topes_900_convocatorias.csv` idéntico.
- Las simulaciones de potencia con datos inventados tardan unos 13 minutos. Las del preregistro se hicieron con `python scripts/contraste.py --sintetico --sims 200 --betas 0 -0.5 --sin-ensayo` y `--sims 100 --betas -1.1 --sin-ensayo` (cada una escribe su `resultados/potencia_sintetica_<sims>x199.json`).

Las pruebas del servidor con un modelo no entran en el comando, porque necesitan uno: `python servidor_mcp/probar_con_modelo.py`, con un modelo abierto en local, y `python servidor_mcp/llamar.py`, que llama a cualquier herramienta desde la línea de comandos, para un modelo que ejecuta órdenes ([servidor_mcp/PRUEBA_CON_MODELO.md](servidor_mcp/PRUEBA_CON_MODELO.md)).
</details>

La app está publicada en Streamlit Community Cloud desde el 12-nov-2026: [invisibles-del-bono.streamlit.app](https://invisibles-del-bono.streamlit.app). Para publicarla de nuevo, el fichero principal es `app/streamlit_app.py`, y en «Advanced settings» hay que elegir Python 3.12. Usa `app/requirements.txt`, que solo tiene lo que necesita la app (Streamlit, pandas, NumPy, Altair y PyArrow, en las versiones con las que se ha probado), y el aspecto de `.streamlit/config.toml`. `python app/probar_app.py` prueba todas sus páginas en un entorno instalado solo con ese fichero.

## Para quién es y cuánto cuesta mantenerlo
- **La Consejería de Vivienda:** el Plan 2026-2030 le deja subir el tope si lo justifica con un estudio actualizado de la oferta de alquiler (art. 135). Este proyecto le da la base de ese estudio, repetible con un comando ([data/ESTUDIO_ART135.md](data/ESTUDIO_ART135.md)): de los 63 municipios pequeños donde proponemos subir el tope de 500 €, en 49 hay base en los datos (en 33, por la oferta de alquiler), y el simulador le deja probar topes y cupos antes de la convocatoria, con su coste.
- **Ayuntamientos y oficinas de juventud:** la ficha de cada municipio, «¿Dónde me llega la ayuda?» y la calculadora, para orientar a quien pregunta.
- **Los jóvenes:** saber en dos minutos si pueden pedirla, cuánto cobrarían y dónde les llega.
- **Asistentes de IA:** el servidor MCP responde con nuestras cifras y con la fuente de cada una, también en la consulta SQL libre (las fuentes de las tablas que lee), para que la IA las cite.

Mantenerlo cuesta casi nada: código abierto (MIT), datos públicos, un comando por cada año nuevo de datos y pruebas automáticas que avisan si algo cambia. La app funciona en un servicio gratuito, Streamlit Community Cloud (el aspecto está en `.streamlit/config.toml`), y la base de datos es un solo fichero de medio megabyte.

## Datos
Solo datos agregados por municipio: **ningún dato personal**.

| Fuente | Qué usamos | Licencia |
|---|---|---|
| [Portal de Datos Abiertos de la Comunidad de Madrid](https://datos.comunidad.madrid/catalogo/) | Bono Alquiler Joven 2022 (solicitudes, aceptadas y rechazadas por municipio); Ayudas al alquiler para jóvenes 2022-2023; población por edad; renta disponible; declaraciones del IRPF por tramo de base imponible; paro registrado por edad; Censo 2021 (viviendas en alquiler); alquiler medio; límites de los municipios y de los distritos de Madrid (2020); zona estadística (NUTS 4) de cada municipio | CC BY 4.0 |
| [SERPAVI, Ministerio de Vivienda y Agenda Urbana](https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi) | Alquiler mediano, p25 y p75 por municipio, de 2011 a 2024, y por distrito de Madrid (2024); y los pisos de toda España en 2024, para comparar comunidades | [Aviso legal del MIVAU](https://www.mivau.gob.es/ministerio/aviso-legal): reutilización permitida citando la fuente |
| [Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/bdnstrans/) | Lista oficial de municipios con tope de 900 € en cada convocatoria, 2022-2025: 29 hasta 2023 y 55 desde 2024 (`scripts/topes_convocatorias.py` → `data/interim/topes_900_convocatorias.csv`) | Textos oficiales publicados |
| [INE: IPC de la Comunidad de Madrid](https://www.ine.es/jaxiT3/Tabla.htm?t=50913) | Índice general de 2019 a 2024 (serie IPC256325), para comparar la subida del alquiler en la base del estudio del art. 135 (`data/raw/ine_ipc_madrid/`) | [Condiciones de uso del INE](https://www.ine.es/aviso_legal): reutilización permitida citando la fuente |
| [INE: cifras oficiales de población de los municipios](https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177011&menu=resultados&idp=1254734710990) | Población de cada municipio de España a 1-ene-2024, para saber cuáles tienen 10.000 habitantes o menos (`scripts/espana_tope500.py`; la columna que se usa, en `data/interim/ine_poblacion_municipios_2024.csv`) | [Condiciones de uso del INE](https://www.ine.es/aviso_legal): reutilización permitida citando la fuente |
| [BOE: Real Decreto 326/2026, Plan Estatal de Vivienda 2026-2030](https://www.boe.es/buscar/act.php?id=BOE-A-2026-8872) | Requisitos, topes y cuantía de la ayuda a jóvenes (arts. 8, 133 a 137), para la calculadora y el simulador | Textos oficiales publicados |

**Qué hace cada uno de los 12 conjuntos del portal de la Comunidad que usamos** (son 10 filas porque la del alquiler medio y los índices de precios junta 3). Si se actualiza uno, se vuelven a ejecutar los scripts y cambia lo de la última columna. Hay otros 6 conjuntos del portal en `data/raw/` que descargamos para explorar o como contexto; no entran en los resultados.

| Conjunto del portal | Para qué lo usamos | Qué depende de él |
|---|---|---|
| [Bono Alquiler Joven (2022)](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022) | Solicitudes por municipio: lo que explica el contraste | El hallazgo principal, el simulador (cuánto pide cada municipio) y la ficha |
| [Ayudas al alquiler para jóvenes y sectores de escasos recursos (2022 y 2023)](https://datos.comunidad.madrid/dataset/spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos) | Otro programa con los mismos topes | La prueba de robustez R1, el mismo municipio en dos años y la validación con un programa que el modelo no ha visto |
| [Población censada por edad](https://datos.comunidad.madrid/dataset/poblacion_censada_por_edad_nacionalidad_y_sexo) | Jóvenes de 20 a 34 años | Las tasas por joven, los cupos de la propuesta y el reparto por grupos |
| [Indicador de renta disponible bruta](https://datos.comunidad.madrid/dataset/irpf_indicador_renta) | Renta por habitante | Un control del contraste y el esfuerzo de alquiler del índice de necesidad |
| [Paro registrado por edad](https://datos.comunidad.madrid/dataset/paro_registrado_edad_municipio) | Paro de menores de 25 años | Un control del contraste y el índice de necesidad |
| [Censo 2021: viviendas por régimen de tenencia](https://datos.comunidad.madrid/dataset/censo_2021_viviendas_familiares_por_tenencia) | Hogares de alquiler | Un control del contraste y el índice de necesidad |
| [Declaraciones del IRPF por tramo](https://datos.comunidad.madrid/dataset/irpf_declaraciones_por_tramo) | Cuánta gente queda por debajo del límite de ingresos (3 × IPREM hoy, 5 × IPREM con el Plan) | La robustez con el límite de ingresos, los cupos de la propuesta y el escenario del Plan |
| [Alquiler medio con valor catastral (más de 20.000 hab.)](https://datos.comunidad.madrid/dataset/alquiler_medio_mensual_viviendas_arrendadas_valor_catastral_municipios_mas_20000) e índices de precios del alquiler: [municipios de más de 10.000 hab.](https://datos.comunidad.madrid/dataset/1934445) y [distritos de Madrid](https://datos.comunidad.madrid/dataset/1934430) | Comprobar el SERPAVI con datos del propio portal, también en los 21 distritos de Madrid; y ver si la medida de la subida cambia el supuesto b) del art. 135 | `scripts/validar_serpavi.py` y el aviso de «Límites» en `data/ESTUDIO_ART135.md` |
| [Municipios y distritos de la Comunidad de Madrid (límites)](https://datos.comunidad.madrid/dataset/covid19_tia_muni_y_distritos) | La forma de cada municipio y de los 21 distritos de Madrid, y el nombre de cada distrito | Los mapas de la app, la tabla `alquiler_distritos_madrid` de la base y qué municipios son vecinos (`scripts/espacial.py`) |
| [Municipios de la Comunidad de Madrid](https://datos.comunidad.madrid/dataset/municipio_comunidad_madrid) | La zona estadística (NUTS 4) de cada municipio | La comprobación por zonas de `scripts/espacial.py`: el efecto dentro de cada zona y la validación dejando fuera una zona entera |

**Incidencias en los datos oficiales:** al usarlos encontramos 6: una unidad mal puesta, municipios sin fila que podrían ser ceros, una fila «Otro» sin explicar, dos códigos de municipio distintos en el mismo portal, un cambio de codificación sin aviso y dos juegos de tramos en la misma tabla. Están en [data/INCIDENCIAS_PORTAL.md](data/INCIDENCIAS_PORTAL.md), cada una comprobada con los ficheros y con una propuesta para el portal. Ninguna cambia los resultados: todas tienen su solución en el código.

<details>
<summary>Las descargas: dónde está cada fichero y cómo se comprueba</summary>

- Los CSV del portal que usamos están en `data/raw/`, tal y como se descargaron. Cada uno se llama `datos.csv` dentro de la carpeta de su conjunto, para que las rutas no pasen del límite de Windows al clonar o descomprimir el repositorio; el nombre y la dirección originales están en su `metadata.json`.
- El portal cambia sus ficheros: entre el 21-oct y el 5-nov pasó de Latin-1 a UTF-8 y añadió años. `scripts/verificar_descargas.py` lo comprueba (resultado en [data/VERIFICACION.md](data/VERIFICACION.md)) y `scripts/descargar.py` los vuelve a bajar.
- Lo que se bajó después del contraste está en carpetas con la fecha de descarga, para no tocar los ficheros del contraste: `data/raw_2026-11-06/` (renta, IRPF y paro con años nuevos), `data/raw_2026-11-07/` (los límites municipales), `data/raw_2026-11-12/` (las zonas estadísticas, con `python scripts/descargar.py --destino=data/raw_2026-11-12 municipio_comunidad_madrid`) y `data/raw_2026-11-16/` (la población del INE de toda España: las 52 tablas, 17 MB, no se suben; `python scripts/espana_tope500.py --descargar` las vuelve a bajar, y la columna que se usa está en `data/interim/`).
- El Excel de SERPAVI (71 MB, MD5 `bff6497f571b3323b75a49bcc3707a57`) no está en el repositorio. El recorte de Madrid que usamos está en `data/interim/serpavi_madrid_*.csv`, y la dirección de descarga, en `data/raw/serpavi_mivau/metadata.json`.
- Qué es cada columna: [data/DICCIONARIO.md](data/DICCIONARIO.md) y, para la base SQLite, [data/DICCIONARIO_BASE_DE_DATOS.md](data/DICCIONARIO_BASE_DE_DATOS.md). Calidad de los datos según MELODA 5: [data/MELODA.md](data/MELODA.md). Normativa y documentos oficiales: [docs_oficiales/FUENTES.md](docs_oficiales/FUENTES.md).
</details>

## Uso de IA
Quién hizo qué, tal cual. **La idea la propuso la IA:** Alessandro le pidió a Claude (Anthropic) que trabajara en DataMad, Claude le propuso tres ideas y él eligió la primera, la que Claude recomendaba. **Desde ahí, Claude escribió casi todo el código, los análisis y los textos**, y por eso todos los commits llevan «Co-Authored-By: Claude». **Lo de Alessandro han sido las decisiones** (ir solo, el nombre del proyecto, qué versión del pitch presentar) **y presentarlo y responder de ello.** Para no tener que fiarse ni de él ni de la IA, un comando rehace los resultados desde los datos (salvo los dos pasos que explica «Cómo repetirlo»), y GitHub lo repite en cada subida. Las bases de DataMad permiten usar IA (apartado 7). Lo hecho antes del 7-nov está en [TRABAJO_PREVIO.md](TRABAJO_PREVIO.md).

## Licencia
El código está bajo licencia [MIT](LICENSE). Los datos conservan la licencia de su fuente.

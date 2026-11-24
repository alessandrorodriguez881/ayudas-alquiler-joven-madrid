# Todas las pruebas, una a una

El resumen está en el [README](README.md). Aquí va cada resultado entero, con sus intervalos, su script y su fichero en `resultados/`. «Exploratorio» quiere decir que no estaba en el preregistro: se hizo después del contraste registrado del 7-nov, y en la mayoría lo esperado se escribió antes de ejecutarlo (cada uno lo dice).

## Lo registrado antes de hacer el contraste

### El trabajo previo, declarado
Datos descargados y verificados, una tabla de 159 municipios, y la hipótesis y las reglas para darla por buena escritas antes de ver el resultado ([PREREGISTRO.md](PREREGISTRO.md)). El contraste se probó antes solo con datos inventados.

### El contraste real (7-nov)
*`resultados/contraste_real.json`*

La hipótesis principal cumple las tres condiciones fijadas antes de hacerlo. **Donde más alquileres superan el tope, menos jóvenes piden el Bono:** por cada 10 puntos más de mercado por encima del tope, un **7,6 % menos de solicitudes** por joven (intervalo del 3,9 % al 11,1 %). El mismo patrón sale en las Ayudas al alquiler, que tienen los mismos topes (no es una prueba independiente).

### Lo que no salió
Un umbral de 900 € igual para todos explica las solicitudes mejor que el tope real, así que una parte es el tope y otra el alquiler caro en sí; y la comparación entre municipios parecidos con tope de 600 y de 900 € va en la misma dirección, pero no es precisa. Separando las dos cosas (análisis exploratorio, hecho después), la parte del tope es un **−5,3 % por cada 10 puntos** (intervalo del −8,5 % al −2,0 %): es la que usa el simulador. Todo, en la última sección de [PREREGISTRO.md](PREREGISTRO.md) y en `resultados/figuras/contraste_todas_las_pruebas.png`.

### Una predicción para 2024, escrita antes de tener los datos
*`scripts/prediccion_2024.py` → `resultados/prediccion_2024.json`, 15-nov*

En 2024 la Comunidad subió el tope de 600 a 900 € en 26 municipios. Cuando se publiquen sus solicitudes por municipio, se verá si el tope frena: el modelo predice que en esos 26 crecerán de 2022 a 2024 un 30 % más que en los que siguieron con 600 € (del 10 % al 53 %). Cómo se comprobará y cuándo se da por buena está al final del [preregistro](PREREGISTRO.md).

## Exploratorio: ¿aguanta el resultado?

### La franja de 600 a 900 €, como placebo
*exploratorio, `scripts/placebo_franja.py` → `resultados/placebo_franja.json`; lo esperado, escrito antes en el commit `5a970aa`*

La parte del tope sale de los alquileres de 600 a 900 € de los municipios con tope de 600 €, que quedan fuera del tope. Si lo que frenara fuera el alquiler en sí, esa misma franja frenaría igual en los municipios con tope de 900 €, donde sí entra. La primera versión estaba mal planteada: le faltaba un efecto propio de los municipios con tope de 600 €, y no separaba nada. **Corregida, después de ver la primera:** la diferencia entre donde la franja queda fuera del tope y donde entra va a favor del tope: −22,8 % de solicitudes por cada 10 puntos (del −33,7 % al −10,1 %), y en el tramo de alquiler común a los dos grupos (el de H2, 42 municipios), −31,9 % (del −49,2 % al −8,6 %). Pero ninguna pendiente por separado es precisa: donde la franja queda fuera, −11,3 % (del −22,7 % al +1,7 %); donde entra, +14,9 % en toda la muestra, que no esperábamos, y cerca de 0 en el tramo de H2, con un intervalo muy ancho. Apunta al tope en la dirección; el tamaño no es fiable. Ojo: es posterior, y depende de la curva supuesta, porque la franja, la parte por encima de 900 € y el alquiler mediano salen de los mismos percentiles del SERPAVI. Con ese efecto de grupo, la parte del tope del modelo conjunto sale mayor, −20,7 % (del −32,8 % al −6,4 %): el simulador se queda con el −5,3 %, la cifra prudente.

### ¿Iban igual antes del cambio?
*exploratorio, `scripts/tendencias_2024.py` → `resultados/tendencias_2024.json`, 17-nov, con lo esperado escrito antes en el commit que añade el script*

La Comunidad eligió los 26 municipios, así que no son al azar. Con el mismo diseño que la prueba de 2024, pero con las Ayudas para jóvenes de 2022 y 2023 (mismos topes los dos años), los 26 crecieron un 16 % menos que los 73 que siguieron en 600 € (de −37 % a +13 %: no se distingue de cero). Esperábamos casi lo mismo, entre −15 % y +15 %, y salió justo por debajo. Si en 2024 crecen más, no será porque ya vinieran creciendo más. Con el ruido de ese programa (665 solicitudes en 2022 en esos municipios), la prueba vería el +30 % previsto 4 de cada 10 veces; esperábamos al menos 5. El Bono tiene unas 5 veces más solicitudes en los mismos municipios (3.534 en 2022), así que será más precisa, pero cuánto no se sabrá hasta tener los datos.

### El límite de ingresos no lo explica
*exploratorio, `resultados/requisito_ingresos.json`*

El Bono pide ingresos de hasta 3 veces el IPREM. Si se añade como control la parte de las declaraciones del IRPF por debajo de ese límite en cada municipio, el efecto queda en **−7,4 %** por cada 10 puntos, y la parte del tope sigue en −5,3 %. Esa parte va casi a la par que la renta por habitante, que ya era un control.

### Las habitaciones
*exploratorio, `resultados/habitaciones.json`*

El tope de una habitación es la mitad del de un piso (300 o 450 €). No hay datos abiertos del alquiler de habitaciones por municipio, así que tomamos el alquiler del piso dividido entre los jóvenes que lo comparten (el caso optimista). Con dos que comparten, las habitaciones no amplían nada; con tres, el límite sube a 900 € (1.350 € en los municipios con tope de 900 €). Medida así la parte del mercado que queda fuera, el efecto sigue siendo negativo y el modelo ajusta mejor que con el tope del piso o con un umbral único de 900 o 1.350 €. Puede ser la razón de que el umbral de 900 € igual para todos ajustara mejor: fuera del Anexo II, 900 € es el límite real para tres jóvenes con contratos de habitación. Se miró después de ver los datos, así que es exploratorio; pero aguanta con municipios y con un programa que el modelo no ha visto (dos puntos más abajo).

### El mismo municipio en 2022 y en 2023
*exploratorio, `resultados/panel_ayudas.json`*

Las Ayudas al alquiler para jóvenes tienen los mismos topes los dos años, así que se puede comparar cada municipio consigo mismo. Con esos datos no se puede saber: el efecto sale en 0, con un intervalo del −25 % al +34 % por cada 10 puntos, en el que también cabe el −7,6 %. En un año, la parte del alquiler por encima del tope solo se movió unos 5 puntos.

### Con municipios que el modelo no ha visto
*exploratorio, `resultados/validacion_fuera_muestra.json`, con lo esperado escrito antes*

Dejando fuera un municipio cada vez, saber qué parte del alquiler pasa del tope baja el error típico de las solicitudes del 21 % al 18 %. Y el modelo del simulador (el tope y el umbral de 900 € juntos), entrenado con el Bono 2022, predice las Ayudas para jóvenes de 2023, otro programa y otro año, con un 27 % menos de desviación que sin esas dos partes (correlación de rangos de 0,32 a 0,46). El umbral de 900 € igual para todos también predice bien: el alquiler caro frena por sí solo. **La medida de las habitaciones es la que mejor predice** (añadida el 12-nov, con lo esperado escrito antes): frente al tope del piso, la desviación de los municipios que el modelo no ha visto baja un 24 % (de 1.359 a 1.036, sin contar Madrid capital) y la de las Ayudas de 2023, un 21 % (de 452 a 357). También gana a un umbral de 1.350 € igual para todos (1.079 y 365). Lo que no esperábamos: Madrid capital, dejada fuera, la predice peor que el tope del piso.

### Los vecinos y las zonas
*exploratorio, `scripts/espacial.py` → `resultados/espacial.json`, 12-nov, con lo esperado escrito antes*

Los municipios vecinos se parecen en cuánto piden (I de Moran de 0,15; p = 0,005), pero lo que el modelo no explica ya no se parece entre vecinos (0,03; p = 0,24), así que el filtro espacial no tuvo que quitar nada. Con errores que dejan que se parezcan los municipios a menos de 30 km (errores de Conley), el intervalo del −7,6 % va del −10,9 % al −4,1 %, casi el mismo que el registrado. Comparando solo municipios de la misma zona estadística (las 11 zonas NUTS 4 del portal), el efecto es algo mayor: −8,2 % (del −12,5 % al −3,8 %), y la parte del tope, −6,2 %. Y dejando fuera una zona entera cada vez, o cada municipio con sus vecinos, la parte del alquiler por encima del tope sigue prediciendo mejor que sin ella, y la medida de las habitaciones sigue siendo la mejor (sin Madrid capital, de 2.006 a 1.776 con el tope del piso y a 1.022 con las habitaciones). Esperábamos más parecido entre vecinos y errores más anchos: no salió así.

### ¿El simulador reparte como el Bono de verdad?
*exploratorio, `scripts/reparto_real_2022.py` → `resultados/reparto_real_2022.json`, 19-nov, con lo esperado escrito antes; un primer cálculo rápido ya se había visto*

El simulador da las ayudas por orden de llegada, en proporción a las solicitudes de cada municipio. El conjunto del Bono 2022 del portal trae también las aceptadas (11.472 en los 132 municipios, el 23,8 % de las solicitudes), así que esa regla se puede comprobar. Sale como esperábamos: Madrid capital se llevó el 63,8 % de las aceptadas y el simulador, con los topes de 2022, le da el 65,3 %; los 36 municipios con más necesidad, el 16,8 % frente al 15,4 %. En todos los grupos se aceptó entre el 22,6 % y el 24,9 % de lo pedido, y por municipio la correlación de rangos es de 0,95. Con tantas solicitudes, esas diferencias pequeñas se notan (los municipios con más necesidad, un punto por encima de la media), pero van a favor de la propuesta: el simulador les da algo menos de lo que recibieron. Los totales no se comparan: el simulador usa el presupuesto de 2024 (31,8 M€, 5.300 ayudas).

## Exploratorio: el Plan 2026-2030 y la propuesta

### Las reglas del Plan 2026-2030, leídas en el BOE
*RD 326/2026*

Además del tope, cambian el límite de ingresos (5 × IPREM **de la persona**, no 3 × IPREM del hogar; art. 133.1.d) y la ayuda (hasta 300 € al mes, o 200 € por una habitación, sin pasar del 60 % del alquiler; art. 137). Con esa cuantía, los 31,8 M€ dan unas 4.420 ayudas, no 5.300. Para que pedirla tenga la misma probabilidad que hoy harían falta 40,1 M€ con el Plan tal cual y 40,3 M€ con nuestra propuesta (`resultados/simulador_reparto.json`, bloque `plan_amount`). **El límite de ingresos más alto, simulado** (exploratorio, bloque `plan_income_limit`): en las declaraciones del IRPF deja entrar a 1,44 veces más gente, y más donde la renta es alta. Con el mismo dinero y por orden de llegada, de cada 100 que la piden la conseguirían unos 8 (hoy, con el presupuesto de 2024, 10), y 6 o 7 si también la piden los que entran nuevos; los municipios con más necesidad fuera de Madrid capital (36 municipios con 225.245 jóvenes: los tercios se cortan por jóvenes, no por municipios) bajarían de 3,0 a 2,9 ayudas por cada 1.000 jóvenes. Con los cupos de la propuesta, que usan el límite del Plan, ese tercio recibe 4,3 pida quien pida: **un 41 % más que con el Plan tal cual** (del 34 % al 48 %, según cómo se reparta el tramo del IRPF que contiene los 42.000 €).

### ¿Y si la necesidad se mide de otra forma?
*exploratorio, `scripts/robustez_indice.py` → `resultados/robustez_indice.json`, 12-nov, con lo esperado escrito antes*

Los cupos de la propuesta usan nuestro índice, y el +41 % se mide con ese mismo índice. Dejando la propuesta igual y eligiendo el tercio con más necesidad de otras 8 formas (cada parte del índice por separado, el índice sin una de sus partes, con puntuaciones z o con media geométrica), ese tercio recibe siempre más que con el Plan: entre un 31 % y un 52 % más. El tercio con menos necesidad se queda casi igual (del −5 % al +7 %; midiendo solo los hogares de alquiler, +23 %), y Madrid capital baja un 11 %. Esperábamos menos ganancia con las partes sueltas: salió más. Lo que sí cambia es la lista: con otra fórmula del índice, cambian de bolsa entre 18 y 54 de los 131 municipios de fuera de Madrid capital (con una sola parte, de 57 a 70; añadido el 15-nov). Por eso la fórmula tiene que fijarse en la convocatoria.

### ¿Y el 58 %, con pueblos de pocos contratos?
*exploratorio, `scripts/robustez_pueblos.py` → `resultados/robustez_pueblos.json`, 12-nov, con lo esperado escrito antes*

El SERPAVI tiene de 10 a 575 contratos en cada municipio pequeño. Leyendo su alquiler de otras dos formas (con la mediana también, o a tramos entre los cuartiles) sale el mismo 58 %. Quitando los pueblos con menos de 30 contratos, el 59 %; con menos de 100, el 65 %: los pueblos mejor medidos son algo más caros, así que el 58 % es la cifra prudente. En todos los casos, el Plan deja fuera al menos el doble que hoy (26 %).

### ¿Y en el resto de España?
*exploratorio, `scripts/espana_tope500.py` → [data/ESPANA_TOPE500.md](data/ESPANA_TOPE500.md), 16-nov, con lo esperado escrito antes en el commit que añade el script*

El tope de 500 € del Plan es el mismo en todas las comunidades donde se aplica, que son todas menos el País Vasco y Navarra (RD 326/2026, art. 1.5). Con el mismo método, el SERPAVI de 2024 (pisos) y la población oficial del INE a 1-ene-2024, en los 1.590 municipios de 10.000 habitantes o menos con datos quedaría por encima de 500 € el 32 % del alquiler. En 209 (con 30 contratos o más), donde viven 1.132.424 personas, quedaría fuera más de la mitad. Madrid es la 2.ª de las 14 comunidades con datos suficientes, después de Baleares: un 63 %, ponderando por pisos alquilados (el 58 % de arriba pondera por jóvenes, que solo tenemos en Madrid). Con la misma regla, Madrid da los mismos 33 pueblos que la base del estudio del art. 135: el código sirve para cualquier comunidad. Al principio contamos también el País Vasco y Navarra (291 municipios y 1.483.774 personas; Madrid, la 3.ª): lo corregimos la misma noche, después de ver los resultados, cuando un jurado ciego avisó de que el Plan no se aplica allí.

### ¿Publican el Bono por municipio otras comunidades?
*búsqueda del 16 y 17-nov, ampliada el 23-nov, [data/BONO_POR_COMUNIDADES.md](data/BONO_POR_COMUNIDADES.md)*

En datos abiertos, que sepamos, Madrid es la única de las 17 que lo publica por municipio, y solo de 2022. En datos.gob.es y en el portal europeo, el único conjunto del Bono es el de Madrid. Cataluña lo da por comarca y solo las concedidas. De la convocatoria de 2024, el Gobierno dio en la Asamblea las ayudas concedidas por municipio hasta agosto de 2025, en PDF y sin las solicitudes. Y los datos existen: el art. 134 del RD 42/2022 obliga a enviarlos al Ministerio cada semestre, por municipio. Por eso pedimos que el portal lo publique cada año: así se comprueba la predicción de 2024 y se rehace la base del estudio del art. 135.

### ¿Cómo se aplica en una convocatoria?
*exploratorio, `scripts/como_se_aplica.py` → [data/COMO_SE_APLICA.md](data/COMO_SE_APLICA.md), 12-nov, con lo esperado escrito antes*

El Plan pide convocatorias «abiertas de esta ayuda de forma continuada y permanente» (RD 326/2026, art. 138), así que no se pueden comparar todas las solicitudes a final de año. La propuesta reparte el dinero en 4 bolsas (Madrid capital y los tres tercios del resto, por necesidad), da las ayudas por orden de llegada dentro de cada una, como hoy, y pasa a las demás lo que sobre en una. Andalucía ya lo hizo con las provincias de su Bono Alquiler Joven: en 2024 pasó a Sevilla 1,5 M€ que sobraban en otras siete. Con el mismo dinero, el tercio con más necesidad recibe un 40,8 % más que con el Plan tal cual (con un cupo por municipio, un 41,0 %). Pierden Madrid capital (309 ayudas, un 10,7 % menos: de cada 100 que la piden, la conseguirían 7,3 en vez de 8,2) y el tercio con menos necesidad (12 ayudas, un 3,6 % menos); en total, 29 de los 132 municipios. Dentro de cada bolsa manda el orden de llegada, así que se pierde algo de puntería: las bolsas consiguen el 68 % de la mejora de los cupos en la mitad más necesitada del tercio con más necesidad. No es un informe jurídico.

### Madrid capital, por distritos

Dentro de Madrid capital, si su bolsa se reparte por la necesidad de sus distritos, los que más la necesitan (Puente de Vallecas, Usera, Villaverde…) reciben un 2,2 % más que con el Plan, en vez de perder, y los de menos necesidad, un 23,9 % menos; lo calculamos después de ver el resultado preregistrado ([data/DISTRITOS_CIFRA3.md](data/DISTRITOS_CIFRA3.md)).

### Cuántas solicitudes más habría con todo el alquiler bajo el tope (una extrapolación)

Si en 2022 el tope hubiera cubierto todo el alquiler, el modelo da unas 9.300 solicitudes más, sobre 48.300 (de 3.200 a 16.300; `resultados/simulador_reparto.json`). Es una extrapolación de una asociación entre municipios, no un efecto causal probado (ver «Lo que no salió», arriba).

### La base del estudio del art. 135
*`scripts/estudio_art135.py`, [data/ESTUDIO_ART135.md](data/ESTUDIO_ART135.md)*

El Plan deja que la Comunidad suba el tope de 500 € si lo justifica con «estudios actualizados de oferta de vivienda» en alquiler, que pueden apoyarse en los dos supuestos del art. 18.3 de la Ley 12/2023: que el alquiler pase del 30 % de la renta del hogar, o que en cinco años haya subido al menos 3 puntos más que el IPC. Lo medimos en cada municipio con datos del portal, del SERPAVI y del INE (el IPC de la Comunidad subió un 16,5 % de 2019 a 2024). La propuesta sube el tope en 63 municipios pequeños (46.458 jóvenes), y hay base en los datos en 49 (42.485 jóvenes). En 33, con el tope de 500 € del Plan queda fuera más de la mitad del alquiler: es el estudio de la oferta, lo que pide el artículo (en Hoyo de Manzanares, el 93 %). En otros 16, el alquiler subió más que el IPC + 3 puntos (en total, el supuesto b) se cumple en 46). La subida se mide con la mediana del SERPAVI: con el índice de precios del alquiler del portal, en los 51 municipios grandes que lo tienen, el supuesto b) no se cumple en ninguno (con la mediana, en 33). Qué medida vale tendría que justificarlo la Comunidad ante el Ministerio. El primer supuesto no se cumple en ningún municipio con la renta media del hogar. Si el tope solo sube donde hay base, las cifras de la propuesta no cambian. No es el estudio oficial: decidir y acordarlo con el Ministerio le toca a la Comunidad.

## Lo que entregamos, en detalle

### La app
*`app/`, publicada en [invisibles-del-bono.streamlit.app](https://invisibles-del-bono.streamlit.app)*

Portada con las tres cifras del proyecto y accesos para el joven y para la Consejería; **«¿Dónde me llega la ayuda?»**, que con tus ingresos y si vives solo o compartes enseña en qué municipios, y en cuáles de los 21 distritos de Madrid, entra más alquiler en el tope, cuánto te darían y cuánto pagarías tú (en Madrid, con el tope de hoy de 900 €, entra al menos la mitad de los alquileres en 11 de los 21 distritos, del 26 % de Chamberí al 88 % de Puente de Vallecas); mapa de necesidad, cobertura y alquiler por encima del tope; **calculadora «¿Puedo pedirla?»**, que dice si un joven cumple los requisitos hoy, con el Plan y con la propuesta, y cuánto cobraría, artículo por artículo (`scripts/reglas_bono.py`, probada con 28 casos hechos a mano en `scripts/probar_reglas.py`); ficha de cada municipio, con su alquiler de 2011 a 2024 frente a los topes y, en los pueblos donde la propuesta sube el tope, si la base del estudio del art. 135 lo justifica; simulador «¿y si el tope fuera otro?» con el presupuesto fijo y la cuantía de hoy o la del Plan; **«¿Cómo se aplica?»**, con las 4 bolsas y quién pierde; y el método con todas las pruebas. Lee la base de datos y usa las mismas funciones que el informe, así que sus cifras son las mismas.

### La base de datos
*`data/bono_alquiler_joven.sqlite`, 0,6 MB*

Todo lo que usa el proyecto en un solo fichero, con 10 tablas unidas por el código INE (municipios, reglas, topes, solicitudes, alquiler del SERPAVI de 2011 a 2024 por municipio y en los 21 distritos de Madrid capital, simulación, fuentes, diccionario y metadatos) y un diccionario de cada columna ([data/DICCIONARIO_BASE_DE_DATOS.md](data/DICCIONARIO_BASE_DE_DATOS.md)). La crea `scripts/base_datos.py`, que comprueba que dice lo mismo que los ficheros de origen.

### El servidor MCP
*`servidor_mcp/`*

Para que un asistente de IA consulte nuestros indicadores ya calculados y cite la fuente de cada cifra. Parte de la plantilla de la formación de DataMad y lee la base SQLite, solo para leer. Herramientas: `buscar_municipio`, `ficha_municipio` (jóvenes, necesidad, alquiler, topes de cada regla y la parte del alquiler por encima, solicitudes y bonos simulados), `puedo_pedirla` (las reglas de la calculadora), `reglas`, `diccionario` y `consulta_sql`. Para Claude Desktop, `servidor_mcp/claude_desktop_config.json`.

### La ficha DCAT-AP-ES
*`data/dcat_ap_es.ttl`*

El catálogo con la base de datos, los indicadores por municipio y el reparto simulado, con tamaño y SHA-1 de cada fichero, licencia, tema (vivienda) y ámbito. Comprobada con las plantillas SHACL oficiales de datos.gob.es (`resultados/validacion_dcat.json`): cumple todo salvo el publicador, que tiene que ser un organismo con código DIR3. Si la Comunidad publica estos datos, basta con poner el suyo.

### Smart Data Models
*`scripts/smart_data_models.py` → `data/smart_data_models/KeyPerformanceIndicator_municipios.json`, 16-nov*

Los indicadores de cada municipio como entidades KeyPerformanceIndicator, el modelo de datos abierto de FIWARE y la OASC: la parte del alquiler de 2024 por encima del tope de hoy, del Plan y de la propuesta, el índice de necesidad y las solicitudes y los bonos del Bono 2022 por cada 1.000 jóvenes. Son 739 entidades, validadas con el esquema oficial, que se guarda con su dirección y su huella en `data/raw_2026-11-16/smart_data_models/`. Un context broker NGSI puede cargarlas tal cual. Salen de la base de datos, así que dicen lo mismo que la app.

# DataMad 2026: preregistro de la cifra 3 con Madrid capital por distritos

**Escrito el vie 13-nov-2026, antes de calcular nada con los distritos** (empezado a las 15:33 y guardado a las 15:34, reloj del equipo; queda fijado con el commit que lo añade). Es **exploratorio**: no forma parte del contraste preregistrado del 2-nov (`PREREGISTRO.md`). Lo pidió Alessandro el 13-nov, en local y sin publicar.

**Lo que ya he visto de los datos por distrito** (solo para saber si existen y qué cubren; ningún índice ni ningún reparto calculado):
- el padrón del Ayuntamiento a 1-1-2024 suma 704.628 jóvenes de 20 a 34 años en Madrid capital; la tabla del proyecto (portal de la Comunidad), 684.390
- el censo 2021 del INE da para Madrid un 24,02 % de viviendas principales en alquiler, lo mismo que el portal de la Comunidad
- las primeras filas del panel de indicadores del Ayuntamiento: renta media disponible por persona de 2023 en Centro (22.073 €), Arganzuela (22.728 €), Retiro (26.905 €) y la ciudad (19.632 €); tasa de desempleo de 16 a 24 años de la ciudad en 2026 (2,77 % los hombres y 2,46 % las mujeres)

## Pregunta
Si Madrid capital entra por distritos en vez de como una sola bolsa, ¿la propuesta sigue dando más ayudas al tercio con más necesidad que el Plan tal cual, con el mismo dinero? ¿Cuántas más?

## Unidades
Los 131 municipios del simulador sin Madrid capital y los 21 distritos de Madrid: **152 unidades**. Los 131 municipios llevan exactamente los datos de hoy (`data/interim/municipios_2024.csv`).

## Datos de cada distrito, anclados a las cifras de Madrid del proyecto
Cada dato del distrito es la cifra de Madrid de la tabla del proyecto por la proporción del distrito en su fuente, de modo que los distritos suman (o promedian) lo mismo que Madrid hoy:
1. **Jóvenes de 20 a 34 y de 15 a 24 años (2024):** padrón municipal del Ayuntamiento a 1-1-2024 (datos.madrid.es, conjunto 209163, enero de 2024; CC BY 4.0), por edad y sección, sumado por distrito y escalado para sumar los 684.390 y 350.985 de Madrid en la tabla
2. **Renta por habitante (2024):** los 27.188 € de Madrid en la tabla × (renta media disponible por persona del distrito / la de la ciudad), del panel de indicadores de distritos y barrios del Ayuntamiento (conjunto 300087, edición 2026, dato de 2023; CC BY 4.0)
3. **Paro de menores de 25 años por 1.000 jóvenes de 15 a 24 (2024):** los 25,83 de Madrid en la tabla × (tasa de desempleo de 16 a 24 años del distrito / la de la ciudad), del mismo panel, año 2024, media de hombres y mujeres
4. **% de hogares de alquiler (2021):** censo 2021 del INE por secciones (`C2021_Indicadores.csv`, tabla T20: viviendas principales en alquiler / viviendas principales), sumado por distrito. Se usa tal cual, porque para Madrid da lo mismo que el portal
5. **Alquiler:** SERPAVI por distrito (mediana, p25 y p75 de 2022 y 2024), ya en `data/interim/serpavi_madrid_distritos.csv`
6. **Parte de las declaraciones del IRPF por debajo de 5 × IPREM:** no existe por distrito, así que cada distrito lleva la de Madrid (supuesto)
7. **Solicitudes del Bono 2022:** no existen por distrito. Las 30.961 de Madrid se reparten con el modelo del proyecto: proporcionales a jóvenes × exp(β × parte del alquiler del distrito por encima del tope de 2022, 900 €), con la β central del simulador (−0,54), de modo que suman las de Madrid. Para 2022 se usan las mismas proporciones de jóvenes que en 2024 (supuesto)

## Índice de necesidad de cada distrito
La misma fórmula que en `scripts/necesidad_2024.py`: media de tres rangos percentiles × 100 (esfuerzo del alquiler, paro juvenil y hogares de alquiler). El rango de cada distrito es su posición en la distribución de los 132 municipios del proyecto, como se puntuaría una unidad nueva, así que los municipios conservan su índice publicado. Topes de los distritos: los de Madrid (hoy 900 €; con el Plan y con la propuesta, 1.000 €).

## Escenarios (el mismo dinero, 31,8 M€, y la cuantía del Plan, art. 137)
- **A. El Plan tal cual:** una sola bolsa, por orden de llegada (las ayudas van en proporción a las solicitudes)
- **B. La propuesta con un cupo por unidad:** jóvenes × índice × parte bajo 5 × IPREM, como `cupos_por_municipio` hoy, pero con 152 unidades
- **C. La propuesta con 3 bolsas:** los tercios de jóvenes por necesidad de las 152 unidades; por orden de llegada dentro de cada bolsa y el sobrante a las demás, como en `scripts/como_se_aplica.py` (ya no hay bolsa aparte para Madrid capital: cada distrito va a la de su necesidad)
- **Comprobación:** con Madrid entero, el mismo código tiene que dar el +40,8 % de `resultados/como_se_aplica.json`

## Qué se mide
- **Principal:** las ayudas por 1.000 jóvenes en el tercio con más necesidad (tercios de jóvenes sobre las 152 unidades), C frente a A, en %
- **También:** B frente a A; los otros dos tercios; Madrid capital entera; cada distrito; cuántos distritos y qué parte de los jóvenes del tercio alto son de Madrid
- **Con las 8 reglas de medir la necesidad** de `scripts/robustez_indice.py` (cada componente solo, el índice sin cada uno, con puntuaciones z y con media geométrica), sobre las 152 unidades. La propuesta sigue usando nuestro índice; solo cambia con qué se elige el tercio que se mide

## Lo que espero
- Índice alto en los distritos del sur (Puente de Vallecas, Villaverde, Usera, Carabanchel, Latina y Villa de Vallecas) y bajo en Salamanca, Chamberí, Chamartín, Retiro y Moncloa-Aravaca. Entre 6 y 10 distritos en el tercio alto, que tendría en Madrid entre un tercio y la mitad de sus jóvenes
- La ganancia del tercio alto con Madrid dentro, **menor que el +41 %: entre +10 % y +30 %** (C frente a A). Motivo: con el Plan, los distritos del sur ya reciben muchas ayudas, porque sus alquileres caben bajo los 1.000 €
- Madrid capital entera, entre −15 % y +5 %; dentro de Madrid, ganan los distritos con más necesidad y pierden los de menos
- Con las 8 reglas, positiva en todas, aunque más dispersa que fuera de Madrid

## Cómo se usará (decidido antes de calcular)
- **+15 % o más y positiva con las 8 reglas:** se puede decir en la respuesta a la pregunta 29 («¿Y Madrid capital?»), en «Método y datos» y, si Alessandro quiere, en el titular («contando Madrid por distritos, +X %»)
- **Entre 0 y +15 %:** solo en la respuesta a la pregunta 29 y en «Método y datos», tal cual
- **Negativa:** se dice igual en la respuesta a la pregunta 29, y el titular sigue siendo el +41 % fuera de Madrid capital, con Madrid −11 % al lado
- Nada de esto cambia lo enviado ni se publica sin su «Súbelo»

## Limitaciones que ya sé
- **Las solicitudes por distrito son un supuesto:** si dentro de Madrid el tope no frena igual que entre municipios, el reparto del Plan por distritos cambia, y con él la comparación
- **Años mezclados:** renta de 2023, paro de 2024, censo de 2021 y padrón de 2024
- **Fuentes de apoyo:** el Ayuntamiento de Madrid y el INE, como ya lo es el SERPAVI. La base municipal sigue siendo la del portal de la Comunidad

Script: `scripts/distritos_cifra3.py` → `resultados/distritos_cifra3.json` y `data/DISTRITOS_CIFRA3.md`.

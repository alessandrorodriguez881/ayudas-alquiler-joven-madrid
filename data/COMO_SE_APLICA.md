# Cómo se aplicaría la propuesta en una convocatoria

Lo genera `scripts/como_se_aplica.py` con los datos del repositorio. **Es una propuesta de diseño, no un informe jurídico:** decidir y comprobar que encaja en la norma les toca a la Comunidad de Madrid y a sus servicios jurídicos.

## Lo que pide la norma
- **La convocatoria no se cierra** ([RD 326/2026](https://www.boe.es/buscar/act.php?id=BOE-A-2026-8872), art. 138): las comunidades «realizarán convocatorias abiertas de esta ayuda de forma continuada y permanente», y la ayuda se paga de forma periódica. Por eso la propuesta no compara solicitudes entre sí: reparte el dinero en bolsas que se gastan por orden de llegada
- **La Comunidad puede poner sus preferencias** (art. 8.4): reconoce las ayudas con las preferencias del Plan y con las «preferencias adicionales» que ella establezca, si respetan las del Plan
- **Subir el tope necesita al Ministerio** (art. 135): un estudio actualizado del alquiler y, antes de convocar, un acuerdo en la comisión de seguimiento que acredite que el Ministerio está conforme con el tope nuevo. La base de ese estudio está en [ESTUDIO_ART135.md](ESTUDIO_ART135.md)
- **Ya se ha hecho algo parecido:** Andalucía repartió por provincias el dinero de su Bono Alquiler Joven. Como en Sevilla había solicitudes sin dinero, le pasó 1.503.067,85 € que sobraban en otras siete provincias ([Resolución de 29 de noviembre de 2024](https://www.juntadeandalucia.es/boja/2024/245/2), BOJA núm. 245, de 19-dic-2024). En la resolución se lee: «Se podrán realizar cuantas redistribuciones de crédito sean necesarias hasta agotar el crédito disponible»

## La propuesta, paso a paso
1. **Antes de convocar,** la Comunidad acuerda los topes nuevos con el Ministerio en la comisión de seguimiento (art. 135): el del Plan o, en los municipios de 10.000 habitantes o menos, el alquiler por debajo del cual quedan 3 de cada 4 contratos, sin pasar de 1.000 €
2. **La convocatoria se abre y no se cierra** (art. 138)
3. **El dinero se reparte en 4 bolsas,** que se publican con la convocatoria, con la lista de municipios de cada una: Madrid capital y tres grupos con el resto de municipios, cada uno con un tercio de sus jóvenes, de más a menos necesidad. Cada bolsa recibe según sus jóvenes de 20 a 34 años, su índice de necesidad, la parte de las declaraciones del IRPF por debajo del límite de ingresos del Plan y lo que cuesta allí cada ayuda
4. **Dentro de cada bolsa, por orden de llegada,** como hoy. No hay que comparar solicitudes, así que la convocatoria puede seguir abierta
5. **Lo que sobra no se pierde:** cada trimestre, el dinero que una bolsa no va a usar, porque no le quedan solicitudes esperando, pasa a las bolsas que sí tienen, en proporción a su reserva
6. **Cada año, las bolsas se recalculan** con los datos nuevos, con un comando: `python scripts/rehacer_todo.py`

## Lo que sale, con el mismo dinero (31,8 M€)
Simulación con la cuantía del Plan (art. 137) y las solicitudes de 2022, como en `scripts/simulador.py`.

| Bolsa | Jóvenes de 20 a 34 | Reserva | Ayudas | De cada 100 que la piden, la consiguen: con el Plan | Con las bolsas | Ayudas por 1.000 jóvenes: con el Plan | Con las bolsas | Cambio |
|---|---|---|---|---|---|---|---|---|
| Tercio con más necesidad | 225.245 | 6,9 M€ (22 %) | 966 | 8,2 | 11,5 | 3,05 | 4,29 | +41 % |
| Tercio de necesidad media | 174.043 | 4,0 M€ (13 %) | 560 | 8,2 | 8,8 | 2,98 | 3,22 | +8 % |
| Tercio con menos necesidad | 181.759 | 2,3 M€ (7 %) | 326 | 8,2 | 7,6 | 1,86 | 1,79 | −4 % |
| Madrid capital | 684.390 | 18,5 M€ (58 %) | 2.569 | 8,2 | 7,3 | 4,21 | 3,75 | −11 % |

- **Las 4 bolsas dan casi lo mismo que los cupos por municipio,** que es lo que simula el resto del proyecto: el tercio con más necesidad recibe un 40,8 % más que con el Plan tal cual (con cupos por municipio, un 41,0 %)
- Con los datos de 2022, **ninguna bolsa tiene dinero de sobra**: en todas hay muchas más solicitudes que ayudas, así que el dinero se acaba en todas y no se mueve nada entre bolsas. La regla del sobrante es para cuando una bolsa reciba menos solicitudes de las esperadas

## Quién pierde
- **Madrid capital:** 309 ayudas menos que con el Plan tal cual (−10,7 %). De cada 100 jóvenes de Madrid capital que la piden, la conseguirían 8,2 con el Plan y 7,3 con las bolsas
- **El tercio con menos necesidad:** 12 ayudas menos (−3,6 %)
- **Por municipios:** 29 de los 132 reciben menos ayudas que con el Plan tal cual: Madrid capital, donde viven el 54 % de los jóvenes, y otros 28, con el 12 %. Los que más pierden: Madrid capital (−309); Alcobendas (−4); Rivas-Vaciamadrid (−3); Las Rozas de Madrid (−2); Tres Cantos (−2). Los que más ganan: Alcalá de Henares (+49); Móstoles (+43); Torrejón de Ardoz (+31); Fuenlabrada (+29); Parla (+21)
- **Dentro de cada bolsa manda el orden de llegada,** así que se pierde algo de puntería. En los municipios del tercio con más necesidad que más la necesitan (la mitad de sus jóvenes), las bolsas dan 4,23 ayudas por cada 1.000 jóvenes; los cupos por municipio, 4,81, y el Plan tal cual, 3,01. Las bolsas consiguen el 68 % de la mejora de los cupos. Con más bolsas se afinaría más (no lo hemos simulado)

## Lo que esto no resuelve
- **Madrid capital va en una sola bolsa,** porque las solicitudes son por municipio: dentro de Madrid, todos los distritos perderían lo mismo, también los de menos renta. Para una bolsa por distrito harían falta las solicitudes por distrito, que no tenemos
- **Suponemos que el orden de llegada no depende del municipio,** como en el simulador. Si en un municipio se pide antes, se lleva más de su bolsa
- **Los núcleos de 10.000 habitantes o menos** dentro de municipios más grandes también tienen el tope de 500 € del Plan, y con datos por municipio no se ven
- **Las cifras son una simulación** con las solicitudes de 2022 y la parte del efecto que se debe al tope (−5,3 % de solicitudes por cada 10 puntos de alquiler por encima)

Todas las cifras, en `resultados/como_se_aplica.json`.

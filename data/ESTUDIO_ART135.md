# Base para el estudio del art. 135: subir el tope de 500 € en los municipios pequeños

Lo genera `scripts/estudio_art135.py`. **No es el estudio oficial:** es la base con datos abiertos para que la Comunidad de Madrid lo haga. Decidir, hacer el estudio y firmar el acuerdo con el Ministerio le toca a ella.

## Qué dice la norma
- **Plan Estatal de Vivienda 2026-2030** ([RD 326/2026](https://www.boe.es/buscar/act.php?id=BOE-A-2026-8872)), art. 133.1.e: la ayuda a jóvenes es para alquileres de hasta 1.000 € al mes, o de 500 € en los municipios de 10.000 habitantes o menos
- **Art. 135:** las comunidades autónomas pueden subir ese máximo si lo justifican con estudios actualizados del alquiler, que pueden basarse en los dos supuestos del art. 18.3 de la [Ley 12/2023](https://www.boe.es/buscar/act.php?id=BOE-A-2023-12203). Antes de convocar, hace falta un acuerdo con el Ministerio de Vivienda en la comisión de seguimiento
- **Ley 12/2023, art. 18.3:**
  - a) que el coste del alquiler, más los gastos y suministros básicos, pase del 30 % de la renta media de los hogares
  - b) que el alquiler haya subido en los cinco años anteriores al menos 3 puntos más que el IPC de la comunidad autónoma

## Cómo lo medimos
- **Supuesto a):** el alquiler mediano de 2024 (SERPAVI, Ministerio de Vivienda) por 12, entre la renta del hogar. La renta del hogar es la renta disponible bruta por habitante de 2024 (portal de la Comunidad) por las personas por hogar de 2021 (población del censo anual entre viviendas principales del Censo de 2021, los dos del portal). **Solo el alquiler, sin gastos ni suministros:** donde ya pasa del 30 %, el supuesto se cumple seguro; con los gastos se cumpliría en más municipios
- **Supuesto b):** la subida del alquiler mediano del SERPAVI de 2019 a 2024, frente a la del IPC de la Comunidad de Madrid (INE, serie IPC256325, media de cada año): **16,5 %**. Se cumple con una subida de al menos el **19,5 %**
- Solo usamos el alquiler mediano de un año si el SERPAVI tiene al menos 30 viviendas en ese municipio. Si falta un dato y el otro supuesto no se cumple, «sin datos suficientes»
- **La propuesta sube el tope** donde el percentil 75 del alquiler de 2024, redondeado a 50 € hacia arriba, pasa de 500 €, y nunca por encima de 1.000 €. Así, 3 de cada 4 alquileres del municipio caben en el tope

## Resultado
- La propuesta sube el tope en **63 municipios pequeños**, donde viven **46.458 jóvenes** de 20 a 34 años
- Con el tope de 500 € del Plan, en la mitad de ellos queda fuera **más del 58 %** del alquiler
- **Se puede justificar con datos en 46 de ellos** (40.681 jóvenes):
  - solo con el supuesto a): 0
  - solo con el b): 46
  - con los dos: 0
  - con ninguno de los dos (medidos los dos): 4
  - sin datos suficientes para decirlo: 13
- En toda la Comunidad, con datos en 112 municipios, el supuesto a) se cumple en 0 y el b) en 87. Con la renta media de los hogares, el alquiler solo no llega al 30 % en ningún municipio: con estos datos, la vía es el supuesto b)
- **La propuesta no depende de los municipios que no se pueden justificar.** Si el tope solo sube donde se puede (y en los demás se queda en 500 €), el tercio de municipios con más necesidad recibe 4,3 ayudas por cada 1.000 jóvenes (con la propuesta entera, 4,3), y que pedirla dé la misma probabilidad que hoy costaría 40,3 M€ (40,3 M€). Es la simulación de `scripts/simulador.py`, con la cuantía del Plan

| Municipio | Habitantes (2024) | Jóvenes de 20 a 34 | Alquiler mediano (2024) | Tope: Plan → propuesta | Alquiler fuera del tope del Plan | Alquiler / renta del hogar | Subida 2019-2024 | Supuesto |
|---|---|---|---|---|---|---|---|---|
| Colmenarejo | 9.741 | 1.724 | 650 € | 500 → 750 € | 84 % | 12 % | 24 % | b |
| Hoyo de Manzanares | 9.186 | 1.671 | 757 € | 500 → 900 € | 93 % | 12 % | 25 % | b |
| Soto del Real | 9.436 | 1.577 | 639 € | 500 → 750 € | 82 % | 10 % | 28 % | b |
| Loeches | 9.253 | 1.468 | 600 € | 500 → 700 € | 72 % | 13 % | 20 % | b |
| San Martín de Valdeiglesias | 9.120 | 1.444 | 402 € | 500 → 550 € | 25 % | 11 % | 24 % | b |
| Sevilla la Nueva | 9.694 | 1.391 | 652 € | 500 → 750 € | 88 % | 13 % | 25 % | b |
| Villa del Prado | 7.424 | 1.356 | 462 € | 500 → 550 € | 32 % | 13 % | 37 % | b |
| Morata de Tajuña | 8.294 | 1.334 | 500 € | 500 → 600 € | 47 % | 13 % | 23 % | b |
| Camarma de Esteruelas | 8.107 | 1.312 | 600 € | 500 → 700 € | 75 % | 12 % | 23 % | b |
| Fuente el Saz de Jarama | 7.384 | 1.310 | 600 € | 500 → 700 € | 75 % | 13 % | 20 % | b |
| Cercedilla | 7.646 | 1.297 | 550 € | 500 → 700 € | 65 % | 12 % | 22 % | b |
| Torres de la Alameda | 7.742 | 1.252 | 540 € | 500 → 650 € | 60 % | 12 % | 20 % | b |
| Manzanares el Real | 9.539 | 1.241 | 600 € | 500 → 700 € | 75 % | 12 % | 23 % | b |
| Cobeña | 7.742 | 1.192 | 700 € | 500 → 850 € | 93 % | 10 % | 27 % | b |
| Collado Mediano | 7.564 | 1.179 | 617 € | 500 → 750 € | 75 % | 11 % | 32 % | b |
| Boalo (El) | 8.548 | 1.121 | 625 € | 500 → 750 € | 82 % | 11 % | 29 % | b |
| Miraflores de la Sierra | 7.209 | 1.121 | 529 € | 500 → 650 € | 57 % | 12 % | 28 % | b |
| Guadalix de la Sierra | 6.912 | 1.104 | 526 € | 500 → 650 € | 61 % | 11 % | 20 % | b |
| Campo Real | 6.766 | 1.058 | 520 € | 500 → 650 € | 59 % | 13 % | 22 % | b |
| Becerril de la Sierra | 6.553 | 1.000 | 570 € | 500 → 700 € | 66 % | 11 % | 23 % | b |
| Pedrezuela | 6.475 | 941 | 507 € | 500 → 600 € | 57 % | 11 % | 27 % | b |
| Moraleja de Enmedio | 5.630 | 933 | 560 € | 500 → 700 € | 61 % | 11 % | 15 % | ninguno |
| Ajalvir | 4.946 | 909 | 647 € | 500 → 750 € | 87 % | 12 % | 20 % | b |
| Cubas de la Sagra | 6.984 | 908 | — | 500 → 800 € | — | — | — | sin datos suficientes |
| Chinchón | 5.820 | 907 | 452 € | 500 → 550 € | 39 % | 12 % | 29 % | b |
| Valdetorres de Jarama | 5.050 | 807 | 550 € | 500 → 650 € | 71 % | 12 % | 22 % | b |
| Molinos (Los) | 4.812 | 804 | 600 € | 500 → 750 € | 78 % | 12 % | 31 % | b |
| Torrejón de Velasco | 4.887 | 763 | 582 € | 500 → 700 € | 75 % | 13 % | 21 % | b |
| Torrelaguna | 4.992 | 739 | 450 € | 500 → 550 € | 39 % | 11 % | 22 % | b |
| Serranillos del Valle | 4.632 | 717 | 650 € | 500 → 750 € | 88 % | 12 % | 28 % | b |
| Valdeolmos-Alalpardo | 4.579 | 691 | 609 € | 500 → 700 € | 89 % | 10 % | 22 % | b |
| Talamanca de Jarama | 4.526 | 688 | 568 € | 500 → 700 € | 67 % | 13 % | 32 % | b |
| Robledo de Chavela | 4.763 | 659 | 450 € | 500 → 550 € | 36 % | 11 % | 29 % | b |
| Casarrubuelos | 4.225 | 658 | 553 € | 500 → 650 € | 75 % | 13 % | 23 % | b |
| Quijorna | 3.987 | 651 | 621 € | 500 → 750 € | 82 % | 14 % | 24 % | b |
| Valdilecha | 3.228 | 546 | 450 € | 500 → 550 € | 39 % | 13 % | 18 % | ninguno |
| Navalagamella | 3.119 | 529 | 451 € | 500 → 600 € | 40 % | 13 % | 25 % | b |
| Aldea del Fresno | 3.422 | 477 | 492 € | 500 → 550 € | 38 % | 14 % | 38 % | b |
| Navacerrada | 3.307 | 467 | 600 € | 500 → 700 € | 75 % | 12 % | 20 % | b |
| Tielmes | 2.807 | 458 | 464 € | 500 → 550 € | 35 % | 14 % | 37 % | b |
| Villamanta | 2.855 | 452 | 465 € | 500 → 650 € | 51 % | 12 % | — | sin datos suficientes |
| Cabrera (La) | 2.952 | 436 | 500 € | 500 → 600 € | 56 % | 11 % | 25 % | b |
| Santos de la Humosa (Los) | 2.797 | 419 | 529 € | 500 → 650 € | 52 % | 12 % | — | sin datos suficientes |
| Bustarviejo | 2.833 | 366 | 483 € | 500 → 550 € | 42 % | 12 % | 29 % | b |
| Chapinería | 2.634 | 359 | 522 € | 500 → 600 € | 47 % | 12 % | — | sin datos suficientes |
| Fresno de Torote | 2.547 | 349 | — | 500 → 750 € | — | — | — | sin datos suficientes |
| Vellón (El) | 2.160 | 318 | 478 € | 500 → 600 € | 44 % | 13 % | 23 % | b |
| Buitrago del Lozoya | 1.970 | 302 | 456 € | 500 → 650 € | 46 % | 11 % | 15 % | ninguno |
| Fresnedillas de la Oliva | 1.833 | 295 | 400 € | 500 → 550 € | 26 % | 11 % | 33 % | b |
| Valdeavero | 1.817 | 285 | 525 € | 500 → 600 € | 51 % | 13 % | 34 % | b |
| Colmenar del Arroyo | 2.013 | 265 | 446 € | 500 → 550 € | 28 % | 10 % | 29 % | b |
| Villanueva de Perales | 1.718 | 257 | — | 500 → 650 € | — | — | — | sin datos suficientes |
| Navalafuente | 1.703 | 255 | 450 € | 500 → 550 € | 36 % | 11 % | 20 % | b |
| Rascafría | 1.712 | 253 | 400 € | 500 → 550 € | 31 % | 10 % | 14 % | ninguno |
| Villamantilla | 1.620 | 233 | 500 € | 500 → 600 € | 47 % | 12 % | 30 % | b |
| Anchuelo | 1.393 | 211 | 500 € | 500 → 550 € | 39 % | 13 % | 25 % | b |
| Lozoyuela-Navas-Sieteiglesias | 1.479 | 209 | — | 500 → 550 € | — | — | — | sin datos suficientes |
| Pozuelo del Rey | 1.302 | 204 | — | 500 → 700 € | — | — | — | sin datos suficientes |
| Santorcaz | 998 | 157 | — | 500 → 600 € | — | — | — | sin datos suficientes |
| Ribatejada | 911 | 135 | — | 500 → 600 € | — | — | — | sin datos suficientes |
| Villamanrique de Tajo | 820 | 129 | — | 500 → 550 € | — | — | — | sin datos suficientes |
| Corpa | 795 | 96 | 450 € | 500 → 550 € | 39 % | 12 % | — | sin datos suficientes |
| Garganta de los Montes | 415 | 69 | — | 500 → 1.000 € | — | — | — | sin datos suficientes |

## Límites
- El SERPAVI recoge los contratos declarados en el IRPF, no los anuncios: mide el alquiler que se paga, no la oferta. Es el índice oficial del Ministerio, pero el art. 135 habla de «oferta»
- La renta del hogar es una estimación: renta por habitante de 2024 por las personas por hogar de 2021
- En los municipios pequeños hay pocos contratos, así que la mediana de un año a otro se mueve mucho. Por eso pedimos al menos 30 viviendas
- Sin los gastos y suministros, el supuesto a) se queda corto: la cifra real de municipios que lo cumplen es igual o mayor

Todos los datos, por municipio, en `resultados/estudio_art135.csv`.

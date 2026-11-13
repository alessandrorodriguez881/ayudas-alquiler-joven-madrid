# La cifra 3 con Madrid capital por distritos

Lo genera `scripts/distritos_cifra3.py`. **Es exploratorio**, preregistrado en [PREREGISTRO_DISTRITOS.md](../PREREGISTRO_DISTRITOS.md) antes de calcular (commit `a74873e`, 13-nov-2026 a las 15:34). Lo marcado como «añadido después» no estaba preregistrado.

## Qué se ha hecho
Hoy Madrid capital, con el 54 % de los jóvenes, va como una sola unidad y una sola bolsa. Por eso el +41 % se mide fuera de ella. Aquí sus 21 distritos ocupan su lugar: 131 municipios y 21 distritos, 152 unidades. Cada distrito lleva la cifra de Madrid de la tabla del proyecto, repartida según el padrón municipal de 2024, el panel de indicadores de distritos del Ayuntamiento y el censo 2021 del INE. Sus solicitudes de 2022 no existen, así que son un supuesto: las de Madrid, repartidas con el modelo del proyecto. Detalles y fuentes, en el docstring del script y en `data/raw_2026-11-13/metadata.json`.

**Comprobación:** con Madrid entero, el mismo código da el +40,8 % de `resultados/como_se_aplica.json`.

**Una precisión sobre el preregistro:** la posición de cada distrito en cada componente se mide frente a los 136 municipios con los tres datos, que son con los que se calculó el índice publicado (el preregistro decía «los 132 del simulador»). Así ningún municipio cambia de índice.

## El índice de necesidad de los distritos
- **Más necesidad (en el tercio alto):** Puente de Vallecas, Usera, Villa de Vallecas, Villaverde, Carabanchel, Vicálvaro, Tetuán, Latina. Esperaba ahí Puente de Vallecas, Villaverde, Usera, Carabanchel, Latina y Villa de Vallecas: ✅ están todos
- **Menos necesidad (en el tercio bajo):** Fuencarral-El Pardo, Salamanca, Barajas, Retiro, Moncloa-Aravaca, Chamartín. Esperaba ahí Salamanca, Chamberí, Chamartín, Retiro y Moncloa-Aravaca: todos menos Chamberí, que queda en el tercio medio
- **Distritos en el tercio alto:** 8 (esperaba entre 6 y 10: ✅ se cumple), con el 71 % de sus jóvenes (esperaba entre un tercio y la mitad: ❌ no se cumple)

## Resultado preregistrado: 3 bolsas por necesidad con los distritos dentro
Con el mismo dinero (31,8 M€) y la cuantía del Plan.

| Tercio | Jóvenes | Unidades | De ellos en Madrid | Ayudas por 1.000 jóvenes con el Plan | Con las 3 bolsas | Cambio | Con un cupo por unidad |
|---|---|---|---|---|---|---|---|
| Necesidad alta | 425.404 | 27 (8 distritos) | 71 % | 4,21 | 4,58 | +8,7 % | +8,8 % |
| Necesidad media | 447.758 | 49 (7 distritos) | 51 % | 3,47 | 3,48 | +0,4 % | +0,5 % |
| Necesidad baja | 392.276 | 76 (6 distritos) | 39 % | 2,74 | 2,33 | −15,1 % | −14,9 % |

- **El tercio con más necesidad gana un +8,7 %**, no un +41 %. Esperaba entre +10 % y +30 %: ❌ no se cumple. Motivo: el 71 % de sus jóvenes vive en 8 distritos de Madrid, que con el Plan ya reciben muchas ayudas: en Madrid se piden más ayudas por joven que fuera, y el supuesto reparte más solicitudes donde el alquiler cabe bajo el tope
- **Con las otras 8 formas de medir la necesidad,** el tercio con más necesidad gana entre un +1,6 % y un +8,5 %: positivo en todas (✅ se cumple)
- **Madrid capital entera:** +1,1 % con las 3 bolsas (−12,5 % con un cupo por unidad). Esperaba entre −15 % y +5 %: ✅ se cumple
- **El coste de mezclar:** los municipios con más necesidad de fuera de Madrid ganan solo un +9,0 % (hoy, un +41 %), porque comparten bolsa y orden de llegada con distritos que piden mucho más. Con un cupo para cada municipio y cada distrito ganarían un +48,4 %, y Madrid entera perdería un 12,5 %
- **Según lo decidido antes de calcular** (entre 0 y +15 %): va a la respuesta de la pregunta 29 y a «Método y datos», tal cual. **El titular no cambia:** +41 % fuera de Madrid capital, con Madrid −11 % al lado

## Añadido después de ver el resultado (no preregistrado): las 4 bolsas de hoy y Madrid repartida por distritos
Las 4 bolsas de hoy, con su dinero, pero la de Madrid se reparte en 3 subbolsas según la necesidad de sus distritos, por orden de llegada dentro de cada una:
- **Fuera de Madrid, todo sigue igual:** el tercio con más necesidad, +41,0 %
- **Madrid capital entera:** −10,8 %, como hoy
- **Dentro de Madrid,** los distritos con más necesidad (Tetuán, Carabanchel, Usera, Puente de Vallecas, Villaverde, Villa de Vallecas, Vicálvaro) pasan de perder como todos a +2,2 %; los de necesidad media, −16,1 %, y los de menos (Retiro, Salamanca, Chamartín, Chamberí, Fuencarral-El Pardo, Moncloa-Aravaca, Hortaleza, Barajas), −23,9 %
- Es la respuesta más directa a «¿Y Madrid capital?»: con la misma propuesta, **los barrios de Madrid con más necesidad no pierden**; pierden los de menos

## Límites
- **Las solicitudes por distrito son un supuesto:** las de Madrid, repartidas con el freno del tope que medimos entre municipios. Si dentro de Madrid frena distinto, cambia el reparto del Plan por distritos
- **Años mezclados:** renta de 2023, paro de 2024, censo de 2021 y padrón de 2024
- **Fuentes de apoyo:** el Ayuntamiento de Madrid y el INE, como ya el SERPAVI. La base municipal sigue siendo la del portal de la Comunidad
- **La parte de las declaraciones bajo 5 × IPREM** es la de Madrid en todos los distritos (no la hay por distrito)

Todas las cifras, en `resultados/distritos_cifra3.json`; la tabla de los distritos, en `data/interim/distritos_madrid_2024.csv`.

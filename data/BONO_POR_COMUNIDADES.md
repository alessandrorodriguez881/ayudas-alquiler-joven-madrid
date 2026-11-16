# ¿Quién publica el Bono Alquiler Joven por municipio?

> Búsqueda del 16 y el 17-nov-2026, solo en fuentes públicas: los portales de datos abiertos de las 17 comunidades, más Ceuta y Melilla, el catálogo nacional (datos.gob.es) y la Base de Datos Nacional de Subvenciones (BDNS). Lo clave lo comprobé yo el 17-nov a las 00:08: la búsqueda en datos.gob.es y el registro de Cataluña.
>
> ✅ comprobado, con enlace · ❓ no encontrado («no lo encontramos» no es lo mismo que «no existe»).

## En pocas palabras
- **Que sepamos, Madrid es la única de las 17 comunidades que publica el Bono por municipio en un formato reutilizable,** y solo de 2022: [Bono Alquiler Joven (2022)](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022). Tiene solicitudes, aceptadas y rechazadas de 159 municipios, más una fila «Otro», en CSV y JSON, con licencia CC BY 4.0 ✅
  - En datos.gob.es, buscando «bono alquiler joven» o «alquiler joven» en el título, sale un solo conjunto: ese ✅ ([API](https://datos.gob.es/apidata/catalog/dataset/title/bono%20alquiler%20joven))
- **Nadie publica 2023, 2024 ni 2025 por municipio, tampoco Madrid.** Las convocatorias siguientes existen, pero sus listas salen en PDF en los boletines o en la BDNS, donde cada concesión es una persona y no hay municipio ✅
- **Lo más parecido fuera de Madrid es Cataluña:** su registro de subvenciones da una fila por concesión del Bono (convocatorias de 2022 y de 2025), con la comarca y no el municipio, y solo las concedidas ✅ ([Concessions del RAISC](https://analisi.transparenciacatalunya.cat/d/s9xt-n979))
- **En el País Vasco y en Navarra el Bono no se aplica** (RD 42/2022), y tampoco el Plan 2026-2030 (RD 326/2026, art. 1.5) ✅

Por eso pedimos que el portal de la Comunidad publique el Bono cada año, por municipio. Así se puede comprobar la predicción de 2024 ([PREREGISTRO.md](../PREREGISTRO.md)) y rehacer cada año la base del estudio del art. 135. El contraste de este proyecto necesita las solicitudes por municipio: hoy, que sepamos, solo se puede hacer en Madrid.

## Comunidad a comunidad
| Comunidad | Qué publica del Bono | Dónde se buscó |
|---|---|---|
| **Madrid** | ✅ Por municipio, solo 2022 (CSV y JSON, CC BY 4.0). La convocatoria de 2024 está en la BDNS, sin municipio | [Portal de datos abiertos](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022) |
| **Cataluña** | ✅ Por comarca, solo las concedidas (2022 y 2025) | [RAISC](https://analisi.transparenciacatalunya.cat/d/s9xt-n979) |
| Andalucía, Aragón, Illes Balears, Canarias, Comunitat Valenciana, Murcia | ❓ Nada del Bono en sus portales (búsqueda en su catálogo CKAN) | Sus portales y datos.gob.es |
| Castilla y León | ❓ Nada en su portal (OpenDataSoft). Las resoluciones, en PDF | Su portal y datos.gob.es |
| Galicia | ❓ Nada con «aluguer», «bono», «xove» ni «mocidade» | abertos.xunta.gal y datos.gob.es |
| Asturias, Cantabria, Castilla-La Mancha, Extremadura, La Rioja, Ceuta y Melilla | ❓ Nada en datos.gob.es. Sus portales no se pudieron buscar por conjunto, o no tienen | datos.gob.es |
| País Vasco y Navarra | No se aplica el Bono | RD 42/2022 |

## Límites
- En datos.gob.es se busca por el título: un conjunto del Bono con otro título se pudo escapar
- No abrimos los PDF de los boletines, así que no sabemos si traen el municipio
- Los registros generales de subvenciones concedidas solo se miraron en Cataluña, en la Comunitat Valenciana (un mes) y en Andalucía
- No se copió ningún dato personal: solo recuentos y nombres de campos

# ¿Llegan las ayudas al alquiler a quien más las necesita?

Proyecto para **DataMad 2026** (URJC, UCM y Comunidad de Madrid), sobre el **Bono Alquiler Joven** en la Comunidad de Madrid.
**En desarrollo:** el periodo de desarrollo va del 7 al 26 de noviembre de 2026.

## La pregunta
El Bono Alquiler Joven (RD 42/2022) da 250 € al mes, pero solo si el alquiler no pasa de **600 €**, o de **900 €** en los 29 municipios del Anexo II del Acuerdo del Consejo de Gobierno de 14-sep-2022.

Donde casi todos los pisos cuestan más que el tope, ¿piden la ayuda menos jóvenes? Si es así, el tope no rechaza: **disuade**. Y eso no se ve en el número de solicitudes rechazadas, porque quien no llega al tope ni siquiera la pide.

El nuevo Plan Estatal de Vivienda 2026-2030 (RD 326/2026) sube el tope general a 1.000 € y deja que cada comunidad lo cambie si lo justifica con estudios actualizados de oferta (art. 135). Este proyecto quiere aportar ese estudio para la Comunidad de Madrid, con datos abiertos.

## Estado (6-nov-2026)
- **Trabajo previo, declarado en [TRABAJO_PREVIO.md](TRABAJO_PREVIO.md):** datos descargados y verificados, una tabla de 159 municipios, y la hipótesis y las reglas para darla por buena escritas antes de ver el resultado ([PREREGISTRO.md](PREREGISTRO.md)). El contraste se ha probado solo con datos inventados.
- **El contraste con los datos reales aún no se ha hecho.** `scripts/contraste.py` no lo deja ejecutar antes del 7-nov-2026.
- Las notas internas de planificación (`PLAN.md`, `IDEAS.md`) no están en el repositorio.

## Cómo repetirlo
Python 3.11 o posterior.

```bash
pip install -r requirements.txt
python scripts/preparar_datos.py          # data/interim/municipios.csv (159 municipios)
python scripts/contraste.py --sintetico   # potencia y falsos positivos con datos inventados
python scripts/contraste.py               # contraste real (a partir del 7-nov-2026)
```

Los CSV del portal que usamos están en `data/raw/`, tal y como se descargaron. El portal cambia sus ficheros: entre el 21-oct y el 5-nov pasó de Latin-1 a UTF-8 y añadió años. `scripts/verificar_descargas.py` lo comprueba (resultado en [data/VERIFICACION.md](data/VERIFICACION.md)) y `scripts/descargar.py` los vuelve a bajar.

## Datos
Solo datos agregados por municipio: **ningún dato personal**.

| Fuente | Qué usamos | Licencia |
|---|---|---|
| [Portal de Datos Abiertos de la Comunidad de Madrid](https://datos.comunidad.madrid/catalogo/) | Bono Alquiler Joven 2022 (solicitudes, aceptadas y rechazadas por municipio); Ayudas al alquiler para jóvenes 2022-2023; población por edad; renta disponible; paro registrado por edad; Censo 2021 (viviendas en alquiler); alquiler medio | CC BY 4.0 |
| [SERPAVI, Ministerio de Vivienda y Agenda Urbana](https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi) | Alquiler mediano, p25 y p75 por municipio, 2022 y 2023 | [Aviso legal del MIVAU](https://www.mivau.gob.es/ministerio/aviso-legal): reutilización permitida citando la fuente |
| [Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/bdnstrans/) | Lista oficial de municipios con tope de 900 € en cada convocatoria, 2022-2025: 29 hasta 2023 y 55 desde 2024 (`scripts/topes_convocatorias.py` → `data/interim/topes_900_convocatorias.csv`) | Textos oficiales publicados |

- El Excel de SERPAVI (71 MB, MD5 `bff6497f571b3323b75a49bcc3707a57`) no está en el repositorio. El recorte de Madrid que usamos está en `data/interim/serpavi_madrid_*.csv`, y la dirección de descarga, en `data/raw/serpavi_mivau/metadata.json`.
- Qué es cada columna: [data/DICCIONARIO.md](data/DICCIONARIO.md). Calidad de los datos según MELODA 5: [data/MELODA.md](data/MELODA.md). Normativa y documentos oficiales: [docs_oficiales/FUENTES.md](docs_oficiales/FUENTES.md).

## Uso de IA
Preparado con ayuda de Claude (Anthropic), como se explica en [TRABAJO_PREVIO.md](TRABAJO_PREVIO.md). Las bases de DataMad permiten usar IA (apartado 7).

## Licencia
El código está bajo licencia [MIT](LICENSE). Los datos conservan la licencia de su fuente.

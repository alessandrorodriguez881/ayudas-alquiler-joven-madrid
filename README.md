# ¿Llegan las ayudas al alquiler a quien más las necesita?

Proyecto para **DataMad 2026** (URJC, UCM y Comunidad de Madrid), sobre el **Bono Alquiler Joven** en la Comunidad de Madrid.
**En desarrollo:** el periodo de desarrollo va del 7 al 26 de noviembre de 2026.

## La pregunta
El Bono Alquiler Joven (RD 42/2022) da 250 € al mes, pero solo si el alquiler no pasa de **600 €**, o de **900 €** en los 29 municipios del Anexo II del Acuerdo del Consejo de Gobierno de 14-sep-2022.

Donde casi todos los pisos cuestan más que el tope, ¿piden la ayuda menos jóvenes? Si es así, el tope no solo rechaza: también **frena las solicitudes**. Y eso no se ve en el número de solicitudes rechazadas, porque quien no llega al tope ni siquiera la pide.

El nuevo Plan Estatal de Vivienda 2026-2030 (RD 326/2026, art. 133.1.e) pone el tope en 1.000 €, o en **500 € en los municipios de 10.000 habitantes o menos**, y deja que cada comunidad lo suba si lo justifica con estudios actualizados de la oferta de alquiler (art. 135). Este proyecto quiere ser una base abierta y repetible para ese estudio en la Comunidad de Madrid.

## Estado (7-nov-2026)
- **Trabajo previo, declarado en [TRABAJO_PREVIO.md](TRABAJO_PREVIO.md):** datos descargados y verificados, una tabla de 159 municipios, y la hipótesis y las reglas para darla por buena escritas antes de ver el resultado ([PREREGISTRO.md](PREREGISTRO.md)). El contraste se probó antes solo con datos inventados.
- **Contraste real hecho el 7-nov** (`resultados/contraste_real.json`): la hipótesis principal cumple las tres condiciones fijadas antes de mirar. **Donde más alquileres superan el tope, menos jóvenes piden el Bono:** por cada 10 puntos más de mercado por encima del tope, un **7,6 % menos de solicitudes** por joven (intervalo del 3,9 % al 11,1 %). El mismo patrón sale en las Ayudas al alquiler, que tienen los mismos topes (no es una prueba independiente).
- **Lo que no salió:** un umbral de 900 € igual para todos explica las solicitudes mejor que el tope real, así que una parte es el tope y otra el alquiler caro en sí; y la comparación entre municipios parecidos con tope de 600 y de 900 € va en la misma dirección, pero no es precisa. Separando las dos cosas (análisis exploratorio, hecho después), la parte del tope es un **−5,3 % por cada 10 puntos** (intervalo del −8,5 % al −2,0 %): es la que usa el simulador. Todo, en la última sección de [PREREGISTRO.md](PREREGISTRO.md) y en `resultados/figuras/contraste_todas_las_pruebas.png`.
- **El límite de ingresos no lo explica** (exploratorio, `resultados/requisito_ingresos.json`): el Bono pide ingresos de hasta 3 veces el IPREM. Si se añade como control la parte de las declaraciones del IRPF por debajo de ese límite en cada municipio, el efecto queda en **−7,4 %** por cada 10 puntos, y la parte del tope sigue en −5,3 %. Esa parte va casi a la par que la renta por habitante, que ya era un control.
- **Las habitaciones** (exploratorio, `resultados/habitaciones.json`): el tope de una habitación es la mitad del de un piso (300 o 450 €). No hay datos abiertos del alquiler de habitaciones por municipio, así que tomamos el alquiler del piso dividido entre los jóvenes que lo comparten (el caso optimista). Con dos que comparten, las habitaciones no amplían nada; con tres, el límite sube a 900 € (1.350 € en los municipios con tope de 900 €). Medida así la parte del mercado que queda fuera, el efecto sigue siendo negativo y el modelo ajusta mejor que con el tope del piso o con un umbral único de 900 o 1.350 €. Puede ser la razón de que el umbral de 900 € igual para todos ajustara mejor: fuera del Anexo II, 900 € es el límite real para tres jóvenes con contratos de habitación. Es una pista, no una prueba: se miró después de ver los datos.
- **El mismo municipio en 2022 y en 2023** (exploratorio, `resultados/panel_ayudas.json`): las Ayudas al alquiler para jóvenes tienen los mismos topes los dos años, así que se puede comparar cada municipio consigo mismo. Con esos datos no se puede saber: el efecto sale en 0, con un intervalo del −25 % al +34 % por cada 10 puntos, en el que también cabe el −7,6 %. En un año, la parte del alquiler por encima del tope solo se movió unos 5 puntos.
- **App** (`app/`, en local): mapa de necesidad, cobertura y alquiler por encima del tope; ficha de cada municipio; simulador «¿y si el tope fuera otro?» con el presupuesto fijo; y el método con todas las pruebas. Usa las mismas funciones que el informe (`scripts/simulador.py`), así que sus cifras son las mismas.
- Las notas internas de planificación (`PLAN.md`, `IDEAS.md`) no están en el repositorio.

## Cómo repetirlo
Python 3.11 o posterior.

```bash
pip install -r requirements.txt
python scripts/preparar_datos.py          # data/interim/municipios.csv (159 municipios)
python scripts/potencia_umbral.py         # tabla de potencia del preregistro, con las simulaciones guardadas
python scripts/contraste.py               # contraste real (a partir del 7-nov-2026)
python scripts/exploratorio_topes_falsos.py  # exploratorio, no preregistrado: los topes falsos, más de cerca
python scripts/necesidad_2024.py          # tabla de 2024 e índice de necesidad (desarrollo)
python scripts/requisito_ingresos.py      # exploratorio: el límite de ingresos (3 × IPREM) con el IRPF por tramos
python scripts/habitaciones.py            # exploratorio: los topes de las habitaciones (300 / 450 €; Plan, 600 / 250 €)
python scripts/panel_ayudas.py            # exploratorio: el mismo municipio en 2022 y 2023 (Ayudas para jóvenes)
python scripts/simulador.py               # reparto de los 5.300 bonos (31,8 M€) con distintas reglas
python scripts/graficos.py                # figuras (resultados/figuras/) y mapa municipal para la app
python scripts/validar_serpavi.py         # el SERPAVI frente a los alquileres del propio portal
streamlit run app/streamlit_app.py        # la app, en http://localhost:8501
python app/probar_app.py                  # prueba todas las páginas de la app sin navegador
```

Dos pasos que no hace falta repetir, porque su resultado ya está en el repositorio:
- `scripts/codigos_municipios.py` y `scripts/topes_convocatorias.py` sacan los códigos INE y los topes de 600 / 900 € de cada convocatoria (29 municipios en 2022, 55 en 2024) de los PDF oficiales, que no se suben: sus enlaces y huellas están en [docs_oficiales/FUENTES.md](docs_oficiales/FUENTES.md). Con los PDF en `docs_oficiales/`, regeneran `data/interim/topes_900_convocatorias.csv` idéntico.
- Las simulaciones de potencia con datos inventados tardan unos 13 minutos. Las del preregistro se hicieron con `python scripts/contraste.py --sintetico --sims 200 --betas 0 -0.5 --sin-ensayo` y `--sims 100 --betas -1.1 --sin-ensayo` (cada una escribe su `resultados/potencia_sintetica_<sims>x199.json`).

Los CSV del portal que usamos están en `data/raw/`, tal y como se descargaron. El portal cambia sus ficheros: entre el 21-oct y el 5-nov pasó de Latin-1 a UTF-8 y añadió años. `scripts/verificar_descargas.py` lo comprueba (resultado en [data/VERIFICACION.md](data/VERIFICACION.md)) y `scripts/descargar.py` los vuelve a bajar.

## Datos
Solo datos agregados por municipio: **ningún dato personal**.

| Fuente | Qué usamos | Licencia |
|---|---|---|
| [Portal de Datos Abiertos de la Comunidad de Madrid](https://datos.comunidad.madrid/catalogo/) | Bono Alquiler Joven 2022 (solicitudes, aceptadas y rechazadas por municipio); Ayudas al alquiler para jóvenes 2022-2023; población por edad; renta disponible; declaraciones del IRPF por tramo de base imponible; paro registrado por edad; Censo 2021 (viviendas en alquiler); alquiler medio; límites municipales (2020) | CC BY 4.0 |
| [SERPAVI, Ministerio de Vivienda y Agenda Urbana](https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi) | Alquiler mediano, p25 y p75 por municipio, de 2022 a 2024 | [Aviso legal del MIVAU](https://www.mivau.gob.es/ministerio/aviso-legal): reutilización permitida citando la fuente |
| [Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/bdnstrans/) | Lista oficial de municipios con tope de 900 € en cada convocatoria, 2022-2025: 29 hasta 2023 y 55 desde 2024 (`scripts/topes_convocatorias.py` → `data/interim/topes_900_convocatorias.csv`) | Textos oficiales publicados |

- El Excel de SERPAVI (71 MB, MD5 `bff6497f571b3323b75a49bcc3707a57`) no está en el repositorio. El recorte de Madrid que usamos está en `data/interim/serpavi_madrid_*.csv`, y la dirección de descarga, en `data/raw/serpavi_mivau/metadata.json`.
- Qué es cada columna: [data/DICCIONARIO.md](data/DICCIONARIO.md). Calidad de los datos según MELODA 5: [data/MELODA.md](data/MELODA.md). Normativa y documentos oficiales: [docs_oficiales/FUENTES.md](docs_oficiales/FUENTES.md).

## Uso de IA
Preparado con ayuda de Claude (Anthropic), como se explica en [TRABAJO_PREVIO.md](TRABAJO_PREVIO.md). Las bases de DataMad permiten usar IA (apartado 7).

## Licencia
El código está bajo licencia [MIT](LICENSE). Los datos conservan la licencia de su fuente.

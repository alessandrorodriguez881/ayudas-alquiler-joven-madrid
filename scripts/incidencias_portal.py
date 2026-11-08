"""Problems we met in the official open data, each one checked against the files, to send back to the Comunidad de
Madrid (an idea from the winner of the MAD Open Data Challenge, which reported errors in the official data; and the
tie-break of the DataMad rules is the use of the Comunidad's data). Nothing here changes our results: every problem
already has its workaround in scripts/ (named in each entry).
Checks the copies in data/raw/ (21-Oct) and data/raw_2026-11-06/, offline. (On 5-Nov verificar_descargas.py saw the
DataStore API of IRPF by bracket with 2,000 rows against 21,619 in the CSV; on 8-Nov that resource had no DataStore,
so it is not listed: it can no longer be checked.)
Usage:  python -P scripts/incidencias_portal.py   -> resultados/incidencias_portal.json and data/INCIDENCIAS_PORTAL.md
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import RAW, ROOT, leer_csv  # noqa: E402
import requisito_ingresos as ri  # noqa: E402

NEW = ROOT / "data" / "raw_2026-11-06"
BONO, AYUDAS = "spacm_bono_alquiler_joven_2022", "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos"


def csv(base, name):
    return next((base / name).glob("*.csv"))


def portal(name):
    return json.loads((RAW / name / "metadata.json").read_text(encoding="utf-8"))["portal_url"]


def unit_label():
    """IRPF returns by bracket: one bracket is labelled «Miles euros» but holds a count of returns."""
    t = leer_csv(csv(NEW, "irpf_declaraciones_por_tramo"))
    units = t.groupby("Tramo")["Unidad"].unique()
    odd = {k: list(v) for k, v in units.items() if list(v) != ["Número"]}
    t["Valor"] = pd.to_numeric(t["Valor"], errors="coerce")
    m = t[(t["Tipo territorio"] == "Municipios") & (t["Año"] == 2024)].pivot_table(
        index="Código territorio", columns="Tramo", values="Valor")
    brackets = [b for b, _ in ri.BRACKETS]  # the 2015-2024 scheme
    full = m.dropna(subset=brackets + ["Total"])
    adds_up = int(((full[brackets].sum(axis=1) - full["Total"]).abs() <= 1).sum())
    return {"id": "irpf_unidad", "dataset": "irpf_declaraciones_por_tramo", "url": portal("irpf_declaraciones_por_tramo"),
            "tipo": "error", "comprobado": bool(odd),
            "que": "El tramo «Entre 12.020,01 y 18.030,00 euros» dice «Miles euros» en la columna Unidad, pero es un número "
                   "de declaraciones, como los demás tramos",
            "prueba": {"unidades_que_no_son_numero": odd,
                       "filas_con_ese_tramo": int((t["Tramo"] == "Entre 12.020,01 y 18.030,00 euros").sum()),
                       "municipios_2024_donde_los_tramos_suman_el_total": f"{adds_up} de {len(full)}"},
            "propuesta": "Cambiar la unidad de ese tramo a «Número»",
            "como_lo_resolvemos": "scripts/requisito_ingresos.py lo trata como número y comprueba que los tramos suman el total"}


def bracket_schemes():
    """IRPF returns by bracket: two different sets of brackets in the same table, depending on the year."""
    t = leer_csv(csv(NEW, "irpf_declaraciones_por_tramo"))
    years = t.groupby("Tramo")["Año"].agg(lambda y: sorted(int(v) for v in y.unique()))
    old = years.get("Más de 21.035,00 euros", [])
    return {"id": "irpf_tramos", "dataset": "irpf_declaraciones_por_tramo", "url": portal("irpf_declaraciones_por_tramo"),
            "tipo": "aviso", "comprobado": bool(old),
            "que": "La tabla mezcla dos juegos de tramos: en unos años el último es «Más de 21.035,00 euros» y en otros "
                   "hay tres tramos por encima de 21.035 €. La descripción del conjunto no lo dice",
            "prueba": {"anios_con_mas_de_21035": old,
                       "anios_con_tramos_hasta_60101": years.get("Más de 60.101,21 euros", [])},
            "propuesta": "Decirlo en la descripción, o publicar los años antiguos en un recurso aparte",
            "como_lo_resolvemos": "Solo usamos 2021 y 2024, que tienen los tramos completos"}


def other_row():
    """Bono 2022 and Ayudas: a row «Otro» with «-» as municipality code, not explained in the metadata."""
    out = {}
    for name in (BONO, AYUDAS):
        t = leer_csv(csv(RAW, name))
        notes = json.loads((RAW / name / "metadata.json").read_text(encoding="utf-8")).get("notes") or ""
        o = t[t["municipio_nombre"] == "Otro"]
        out[name] = {"filas": len(o), "codigos": sorted(o["municipio"].astype(str).unique()),
                     "solicitudes": int(o["solicitudes"].sum()), "aceptadas": int(o["aceptadas"].sum()),
                     "la_descripcion_lo_explica": "otro" in notes.lower()}
    b = out[BONO]
    n = f"{b['solicitudes']:,}".replace(",", ".")
    return {"id": "fila_otro", "dataset": f"{BONO} y {AYUDAS}", "url": portal(BONO), "tipo": "aviso",
            "comprobado": b["filas"] == 1 and not b["la_descripcion_lo_explica"],
            "que": f"Hay una fila «Otro» con «-» como código de municipio: en el Bono 2022, {n} solicitudes, todas "
                   "rechazadas. La descripción no dice qué son",
            "prueba": out,
            "propuesta": "Explicar en la descripción qué recoge «Otro» (por ejemplo, solicitudes sin vivienda en la Comunidad) "
                         "y dejar vacío el código en vez de «-»",
            "como_lo_resolvemos": "scripts/base_datos.py guarda solo los códigos de 3 cifras y lleva la cifra de «Otro» a "
                                  "la tabla metadatos"}


def zero_or_missing():
    """Bono 2022 and Ayudas: municipalities with no row, and no row with 0 requests: zero and «no data» look the same."""
    codes = pd.read_csv(ROOT / "data" / "interim" / "codigos_municipios.csv", dtype={"ine": str})["ine"]
    out = {}
    for name in (BONO, AYUDAS):
        t = leer_csv(csv(RAW, name), dtype={"municipio": str})
        t = t[t["municipio"].astype(str).str.fullmatch(r"\d{3}")]
        keys = ["programa", "año_convocatoria"] if "programa" in t else []
        groups = t.groupby(keys) if keys else [((), t)]
        out[name] = [{"grupo": " ".join(str(v) for v in (k if isinstance(k, tuple) else (k,))) or "todo",
                      "municipios_con_fila": int(g["municipio"].nunique()),
                      "municipios_sin_fila": int((~codes.isin(g["municipio"])).sum()),
                      "filas_con_0_solicitudes": int((g["solicitudes"] == 0).sum())} for k, g in groups]
    b = out[BONO][0]
    return {"id": "cero_o_sin_dato", "dataset": f"{BONO} y {AYUDAS}", "url": portal(BONO), "tipo": "aviso",
            "comprobado": b["municipios_sin_fila"] > 0 and b["filas_con_0_solicitudes"] == 0,
            "que": f"{b['municipios_sin_fila']} de los 179 municipios no tienen fila en el Bono 2022, y ninguna fila tiene 0 "
                   "solicitudes: no se sabe si en esos municipios nadie la pidió o si falta el dato",
            "prueba": out,
            "propuesta": "Publicar los 179 municipios, con 0 donde no hubo solicitudes (o decir en la descripción que las "
                         "filas que faltan son ceros)",
            "como_lo_resolvemos": "El contraste solo usa los 159 municipios con fila y no los trata como ceros "
                                  "(PREREGISTRO.md)"}


def two_codes():
    """The same portal uses two municipality codes: 3-digit INE (Bono, Ayudas) and its own statistics code (IRPF...)."""
    bono = leer_csv(csv(RAW, BONO), dtype={"municipio": str})
    irpf = leer_csv(csv(NEW, "irpf_declaraciones_por_tramo"))
    irpf = irpf[irpf["Tipo territorio"] == "Municipios"]
    parla = {"bono_2022": str(bono.loc[bono["municipio_nombre"] == "Parla", "municipio"].iloc[0]),
             "irpf_por_tramo": str(int(irpf.loc[irpf["Territorio"] == "Parla", "Código territorio"].iloc[0]))}
    return {"id": "dos_codigos", "dataset": f"{BONO} e irpf_declaraciones_por_tramo (y otros del Instituto de Estadística)",
            "url": portal(BONO), "tipo": "aviso", "comprobado": parla["bono_2022"] != parla["irpf_por_tramo"],
            "que": "Dentro del mismo portal, el municipio va con dos códigos distintos: el INE de 3 cifras en los datos del "
                   "Bono y de las Ayudas, y el código estadístico de la Comunidad (INE × 10 + dígito de control) en el IRPF, "
                   "la población o el paro. Para cruzarlos hace falta una tabla de equivalencias",
            "prueba": {"parla": parla},
            "propuesta": "Añadir en todos los conjuntos una columna con el código INE de 5 cifras (28106 para Parla)",
            "como_lo_resolvemos": "scripts/codigos_municipios.py hace la tabla de equivalencias de los 179 municipios"}


def encoding():
    """The same dataset, downloaded on 21-Oct and on 6-Nov: Latin-1 first, then UTF-8, with no notice on the portal."""
    out = {}
    for name in ("irpf_declaraciones_por_tramo", "irpf_indicador_renta", "paro_registrado_edad_municipio"):
        enc = {}
        for label, base in (("21-oct", RAW), ("6-nov", NEW)):
            data = csv(base, name).read_bytes()
            try:
                data.decode("utf-8")
                enc[label] = "UTF-8"
            except UnicodeDecodeError:
                enc[label] = "Latin-1"
        out[name] = enc
    changed = [k for k, v in out.items() if v["21-oct"] != v["6-nov"]]
    return {"id": "codificacion", "dataset": ", ".join(changed), "url": portal(changed[0]) if changed else "",
            "tipo": "aviso", "comprobado": bool(changed),
            "que": "Entre el 21-oct y el 6-nov estos ficheros pasaron de Latin-1 a UTF-8 (además de añadir el último año). "
                   "Un programa que lea la codificación fija deja de funcionar o lee mal las tildes",
            "prueba": out,
            "propuesta": "Mantener una codificación (UTF-8) en todos los ficheros y anotar los cambios de formato en el "
                         "historial del conjunto",
            "como_lo_resolvemos": "scripts/comun.py (leer_csv) prueba las dos codificaciones"}


def markdown(items):
    head = ["# Incidencias en los datos abiertos que usamos", "",
            "Para devolverlas al Portal de Datos Abiertos de la Comunidad de Madrid. Generado por "
            "`scripts/incidencias_portal.py`: cada una se comprueba con los ficheros, así que no depende de lo que digamos "
            "nosotros. Ninguna cambia nuestros resultados: todas tienen su solución en el código.", "",
            "| # | Tipo | Conjunto | Qué pasa | Propuesta | Comprobado |", "|---|---|---|---|---|---|"]
    mark = {True: "✅", False: "❌ ya no pasa"}
    rows = [f"| {i} | {x['tipo']} | [{x['dataset'].replace(',', ' ').split()[0]}]({x['url']}) | {x['que']} | {x['propuesta']} | "
            f"{mark[x['comprobado']]} |" for i, x in enumerate(items, 1)]
    detail = ["", "## Pruebas y cómo lo resolvemos", ""]
    for i, x in enumerate(items, 1):
        detail += [f"**{i}. {x['id']}** — {x['como_lo_resolvemos']}.", "",
                   "```json", json.dumps(x["prueba"], ensure_ascii=False, indent=1), "```", ""]
    return "\n".join(head + rows + detail)


def main():
    items = [unit_label(), zero_or_missing(), other_row(), two_codes(), encoding(), bracket_schemes()]
    out = {"note": "Incidencias comprobadas con los ficheros del repositorio; ver el docstring del script",
           "incidencias": items}
    (ROOT / "resultados" / "incidencias_portal.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                                encoding="utf-8")
    (ROOT / "data" / "INCIDENCIAS_PORTAL.md").write_text(markdown(items), encoding="utf-8")
    for x in items:
        print(x["id"], x["tipo"], "comprobado:", x["comprobado"])


if __name__ == "__main__":
    main()

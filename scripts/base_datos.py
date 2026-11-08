"""One documented SQLite database with everything the project uses, by municipality (written 8-Nov-2026):
data/bono_alquiler_joven.sqlite, read by the app and meant for the MCP server. Tables:
  municipios        179 municipalities: population, income, unemployment, renting, need index, income-limit share
  reglas            each call or rule (Bono 2022 and 2024, Ayudas para jóvenes 2022-2025, Plan 2026-2030, proposal):
                    norm, income limit, aid and months, as written in the norm (NULL where we have not read it)
  topes             cap of the flat and of the room per municipality and rule (EUR/month)
  solicitudes       requests, accepted and rejected per municipality, programme and call year (open data portal)
  alquiler_serpavi  SERPAVI 2011-2024: rented dwellings and monthly rent (median, p25, p75) per municipality and year
  alquiler_distritos_madrid  the same for Madrid city's 21 districts (SERPAVI's 'Distritos' sheet), named as on the
                    portal's boundaries (scripts/distritos_madrid.py)
  simulacion        each scenario of the simulator (central beta): cap, expected requests, bonos and share above the cap
  fuentes           every dataset used, with its licence and address
  diccionario       every column of every table: type, unit, meaning and source (the script fails if one is missing)
  metadatos         when and from which commit the file was built
and the view ficha_municipio (today's, the Plan's and the proposal's caps next to the 2024 rent).
Nothing is computed here that the scripts do not already compute: values come from data/interim/ (preparar_datos.py,
necesidad_2024.py, requisito_ingresos.py, topes_convocatorias.py, distritos_madrid.py), the raw portal files,
scripts/reglas_bono.py and scripts/simulador.py, and verify() checks them against those files after building.
data/DICCIONARIO_BASE_DE_DATOS.md is written from the same dictionary.
Usage:  python -P scripts/base_datos.py   (after the scripts above)"""
import datetime
import json
import pathlib
import sqlite3
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
import reglas_bono as rb  # noqa: E402
import simulador  # noqa: E402
from comun import INTERIM, RAW, ROOT, leer_csv  # noqa: E402

DB = ROOT / "data" / "bono_alquiler_joven.sqlite"
DOC = ROOT / "data" / "DICCIONARIO_BASE_DE_DATOS.md"
NEW = ROOT / "data" / "raw_2026-11-06"
CM = "Portal de Datos Abiertos de la Comunidad de Madrid"

# table -> (description, primary key, {column: (SQL type, unit, meaning, source)})
SCHEMA = {
    "municipios": ("Una fila por municipio de la Comunidad de Madrid", ["ine"], {
        "ine": ("TEXT", "", "Código INE del municipio, 3 cifras (provincia 28)", "codigos_municipios.csv"),
        "ine5": ("TEXT", "", "Código INE de 5 cifras", "codigos_municipios.csv"),
        "municipio": ("TEXT", "", "Nombre oficial", "Instituto de Estadística de la Comunidad de Madrid"),
        "pob_total_2024": ("INTEGER", "personas", "Población total, 2024", "poblacion_censada_por_edad_nacionalidad_y_sexo"),
        "jovenes_20_34_2022": ("INTEGER", "personas", "Población de 20 a 34 años, 2022 (no hay tramo de 18 a 35)",
                               "poblacion_censada_por_edad_nacionalidad_y_sexo"),
        "jovenes_20_34_2024": ("INTEGER", "personas", "Población de 20 a 34 años, 2024",
                               "poblacion_censada_por_edad_nacionalidad_y_sexo"),
        "jovenes_15_24_2024": ("INTEGER", "personas", "Población de 15 a 24 años, 2024",
                               "poblacion_censada_por_edad_nacionalidad_y_sexo"),
        "renta_pc_2024": ("REAL", "€ por persona y año", "Renta disponible bruta per cápita, 2024", "irpf_indicador_renta"),
        "paro_menor25_2024": ("REAL", "personas", "Parados registrados menores de 25 años, media de los 12 meses de 2024",
                              "paro_registrado_edad_municipio"),
        "paro25_por_1000_15_24_2024": ("REAL", "por 1.000", "Parados menores de 25 por cada 1.000 jóvenes de 15 a 24, 2024",
                                       "calculado"),
        "pct_alquiler_2021": ("REAL", "%", "Hogares (viviendas principales) de alquiler, Censo 2021",
                              "censo_2021_viviendas_familiares_por_tenencia"),
        "esfuerzo_alquiler_2024": ("REAL", "proporción", "12 × alquiler mediano 2024 / renta per cápita 2024",
                                   "calculado (SERPAVI y renta)"),
        "indice_necesidad": ("REAL", "0-100", "Índice de necesidad: media de los rangos de esfuerzo de alquiler, paro "
                             "juvenil y hogares de alquiler (136 municipios con los tres)", "calculado (necesidad_2024.py)"),
        "tercil_necesidad": ("TEXT", "", "baja, media o alta (tercios de municipios)", "calculado (necesidad_2024.py)"),
        "grupo_necesidad": ("TEXT", "", "Grupo del simulador: Madrid capital aparte y el resto en tercios de jóvenes por "
                            "necesidad (132 municipios)", "calculado (simulador.py)"),
        "parte_irpf_bajo_3iprem_2024": ("REAL", "proporción", "Declaraciones del IRPF con base imponible de hasta 3 × IPREM "
                                        "(25.200 €), de todas las edades: compara municipios, no cuenta jóvenes",
                                        "irpf_declaraciones_por_tramo (requisito_ingresos.py)"),
        "parte_irpf_bajo_5iprem_2024": ("REAL", "proporción", "Ídem con 5 × IPREM (42.000 €), el límite de la persona en el "
                                        "Plan 2026-2030; el tramo que lo contiene es ancho (30.051-60.101 €)",
                                        "irpf_declaraciones_por_tramo (requisito_ingresos.py)"),
        "anexo_ii_2022": ("INTEGER", "0/1", "1 si tenía tope de 900 € en el Bono 2022 (29 municipios)", "Acuerdo de 14-sep-2022"),
        "anexo_ii_2024": ("INTEGER", "0/1", "1 si tiene tope de 900 € en el Bono 2024 (55 municipios)",
                          "Acuerdo de 26-dic-2024 (BDNS 805618)"),
        "hasta_10000_hab": ("INTEGER", "0/1", "1 si tiene 10.000 habitantes o menos en 2024 (tope de 500 € en el Plan)",
                            "calculado"),
    }),
    "reglas": ("Cada convocatoria o regla, con lo que dice su norma", ["regla"], {
        "regla": ("TEXT", "", "Clave de la regla", ""),
        "nombre": ("TEXT", "", "Nombre", ""),
        "norma": ("TEXT", "", "Norma que la fija", ""),
        "estado": ("TEXT", "", "Situación a 8-nov-2026", ""),
        "topes": ("TEXT", "", "Cómo se fija el tope del alquiler", ""),
        "limite_ingresos_iprem": ("REAL", "veces el IPREM", "Límite de ingresos anuales (NULL si no lo hemos leído en la norma)", ""),
        "ingresos_que_cuentan": ("TEXT", "", "De quién son los ingresos que cuentan", ""),
        "ayuda_max_piso": ("REAL", "€/mes", "Ayuda máxima por persona, vivienda", ""),
        "ayuda_max_habitacion": ("REAL", "€/mes", "Ayuda máxima por persona, habitación", ""),
        "ayuda_max_pct_alquiler": ("REAL", "%", "La ayuda no pasa de este porcentaje del alquiler", ""),
        "meses": ("INTEGER", "meses", "Duración de la ayuda", ""),
        "nota": ("TEXT", "", "Lo demás que conviene saber", ""),
    }),
    "topes": ("Tope del alquiler por municipio y regla", ["ine", "regla"], {
        "ine": ("TEXT", "", "Código INE del municipio", ""),
        "regla": ("TEXT", "", "Clave de la regla (tabla reglas)", ""),
        "tope_piso": ("REAL", "€/mes", "Alquiler máximo de la vivienda entera", "norma de la regla; propuesta: reglas_bono.caps"),
        "tope_habitacion": ("REAL", "€/mes", "Alquiler máximo de una habitación (NULL si no lo hemos leído en la norma)",
                            "norma de la regla; propuesta: reglas_bono.caps"),
    }),
    "solicitudes": ("Solicitudes por municipio, programa y año de convocatoria", ["ine", "programa", "anio_convocatoria"], {
        "ine": ("TEXT", "", "Código INE del municipio", ""),
        "programa": ("TEXT", "", "bono_alquiler_joven, ayudas_alquiler_jovenes (programa 5.1) o "
                     "ayudas_alquiler_escasos_recursos (programa 2)", ""),
        "anio_convocatoria": ("INTEGER", "año", "Año de la convocatoria", ""),
        "solicitudes": ("INTEGER", "solicitudes", "Solicitudes presentadas", "spacm_bono_alquiler_joven_2022, "
                        "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos"),
        "aceptadas": ("INTEGER", "solicitudes", "Solicitudes aceptadas", "idem"),
        "rechazadas": ("INTEGER", "solicitudes", "Solicitudes rechazadas (por requisitos o por crédito agotado)", "idem"),
    }),
    "alquiler_serpavi": ("Alquiler de vivienda colectiva por municipio y año, 2011-2024", ["ine", "anio"], {
        "ine": ("TEXT", "", "Código INE del municipio", ""),
        "anio": ("INTEGER", "año", "Año", ""),
        "viviendas": ("INTEGER", "viviendas", "Viviendas colectivas en alquiler con declaración del IRPF", "SERPAVI (MIVAU)"),
        "mediana": ("REAL", "€/mes", "Alquiler mensual mediano", "SERPAVI (MIVAU)"),
        "p25": ("REAL", "€/mes", "Percentil 25 del alquiler mensual", "SERPAVI (MIVAU)"),
        "p75": ("REAL", "€/mes", "Percentil 75 del alquiler mensual", "SERPAVI (MIVAU)"),
    }),
    "alquiler_distritos_madrid": ("Alquiler de vivienda colectiva en los 21 distritos de Madrid capital, por año, 2011-2024",
                                  ["distrito", "anio"], {
        "distrito": ("TEXT", "", "Código del distrito: municipio y distrito, de 07901 (Centro) a 07921 (Barajas); es el "
                     "CUDIS del SERPAVI sin la provincia", "SERPAVI (MIVAU), hoja Distritos"),
        "ine": ("TEXT", "", "Código INE del municipio (079, Madrid)", ""),
        "nombre": ("TEXT", "", "Nombre del distrito", "covid19_tia_muni_y_distritos (límites de municipios y distritos de "
                   "Madrid, 2020; scripts/distritos_madrid.py)"),
        "anio": ("INTEGER", "año", "Año", ""),
        "viviendas": ("INTEGER", "viviendas", "Viviendas colectivas en alquiler con declaración del IRPF",
                      "SERPAVI (MIVAU), hoja Distritos"),
        "mediana": ("REAL", "€/mes", "Alquiler mensual mediano", "SERPAVI (MIVAU), hoja Distritos"),
        "p25": ("REAL", "€/mes", "Percentil 25 del alquiler mensual", "SERPAVI (MIVAU), hoja Distritos"),
        "p75": ("REAL", "€/mes", "Percentil 75 del alquiler mensual", "SERPAVI (MIVAU), hoja Distritos"),
    }),
    "simulacion": ("Escenarios del simulador de reparto con el β central (−0,54) y 31,8 M€", ["ine", "escenario"], {
        "ine": ("TEXT", "", "Código INE del municipio", ""),
        "escenario": ("TEXT", "", "Regla del simulador (scripts/simulador.py, rules)", ""),
        "reparto": ("TEXT", "", "llegada (orden de llegada) o cupos (jóvenes × necesidad, a veces × límite de ingresos: "
                    "aquí, el de hoy, 3 × IPREM, porque son bonos de 250 €)", ""),
        "tope_piso": ("REAL", "€/mes", "Tope del piso en el escenario", "simulador.py"),
        "solicitudes": ("REAL", "solicitudes", "Solicitudes esperadas con ese tope", "simulador.py"),
        "bonos": ("REAL", "bonos", "Bonos que recibiría (5.300 en total)", "simulador.py"),
        "parte_por_encima": ("REAL", "proporción", "Parte de los alquileres de 2024 por encima del tope", "simulador.py"),
    }),
    "fuentes": ("Datos usados, con su licencia", ["fuente"], {
        "fuente": ("TEXT", "", "Nombre del conjunto de datos", ""),
        "titulo": ("TEXT", "", "Título", ""),
        "publica": ("TEXT", "", "Quién lo publica", ""),
        "licencia": ("TEXT", "", "Licencia", ""),
        "url": ("TEXT", "", "Dirección", ""),
        "actualizado": ("TEXT", "", "Fecha de la última actualización según la fuente", ""),
        "carpeta": ("TEXT", "", "Carpeta del repositorio con la copia y su metadata.json", ""),
    }),
    "diccionario": ("Cada columna de cada tabla", ["tabla", "columna"], {
        "tabla": ("TEXT", "", "Tabla", ""), "columna": ("TEXT", "", "Columna", ""), "tipo": ("TEXT", "", "Tipo SQL", ""),
        "unidad": ("TEXT", "", "Unidad", ""), "descripcion": ("TEXT", "", "Qué es", ""), "fuente": ("TEXT", "", "De dónde sale", ""),
    }),
    "metadatos": ("Cómo y cuándo se hizo el fichero", ["clave"], {
        "clave": ("TEXT", "", "Clave", ""), "valor": ("TEXT", "", "Valor", ""),
    }),
}
FOREIGN = {"topes": [("ine", "municipios"), ("regla", "reglas")], "solicitudes": [("ine", "municipios")],
           "alquiler_serpavi": [("ine", "municipios")], "alquiler_distritos_madrid": [("ine", "municipios")],
           "simulacion": [("ine", "municipios")]}
SOURCES = [("spacm_bono_alquiler_joven_2022", RAW), ("spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos", RAW),
           ("poblacion_censada_por_edad_nacionalidad_y_sexo", RAW), ("censo_2021_viviendas_familiares_por_tenencia", RAW),
           ("irpf_indicador_renta", NEW), ("paro_registrado_edad_municipio", NEW), ("irpf_declaraciones_por_tramo", NEW),
           ("serpavi_mivau", RAW), ("covid19_tia_muni_y_distritos", ROOT / "data" / "raw_2026-11-07")]
CALLS = {2022: "BDNS 654786", 2023: "BDNS 721190", 2024: "BDNS 793423", 2025: "BDNS 864406"}


def municipalities():
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    codes = pd.read_csv(INTERIM / "codigos_municipios.csv", dtype={"ine": str, "ine5": str})
    inc = pd.read_csv(INTERIM / "requisito_ingresos.csv", dtype={"ine": str})
    s, _ = simulador.load()
    t = (t.merge(codes[["ine", "ine5"]], on="ine", how="left")
         .merge(inc[["ine", simulador.BONO_INCOME, simulador.PLAN_INCOME]], on="ine", how="left")
         .merge(s[["ine"]].assign(grupo_necesidad=simulador.need_groups(s)), on="ine", how="left"))
    return t.assign(parte_irpf_bajo_3iprem_2024=t[simulador.BONO_INCOME],
                    parte_irpf_bajo_5iprem_2024=t[simulador.PLAN_INCOME],
                    anexo_ii_2022=(t["tope_2022"] == 900).astype(int), anexo_ii_2024=(t["tope_2024"] == 900).astype(int),
                    hasta_10000_hab=(t["pob_total_2024"] <= 10000).astype(int))


def rules():
    who_bono = "hogar; solo la persona si alquila una habitación o si comparten jóvenes que firman (art. 4.1.d)"
    rows = [
        ("bono_2022", "Bono Alquiler Joven 2022", "Acuerdo del Consejo de Gobierno de 14-sep-2022 (RD 42/2022)",
         "cerrada: crédito agotado el 6-nov-2023", "art. 5: 600 / 300 €; 900 / 450 € en los 29 del anexo II",
         3, who_bono, 250, 250, 100, 24, "Por orden de llegada mientras hay crédito (art. 9)"),
        ("bono_2024", "Bono Alquiler Joven 2024", "Acuerdo del Consejo de Gobierno de 26-dic-2024 (BDNS 805618)",
         "abierta desde el 3-feb-2025", "art. 5: 600 / 300 €; 900 / 450 € en los 55 del anexo II",
         3, who_bono, 250, 250, 100, 24, "Mismos artículos 4, 5, 7 y 8 que el Acuerdo de 2022"),
        *[(f"ayudas_jovenes_{y}", f"Ayudas al alquiler para jóvenes {y} (programa 5.1)", f"Convocatoria de {y} ({c})",
           "pasada" if y < 2025 else "convocatoria de 2025", "anexo I: 600 € y 900 € en la lista de municipios",
           None, None, None, None, None, None, "Solo el tope general de la vivienda; las familias numerosas tienen 900 € "
           "en todos los municipios. El resto de condiciones no está en esta tabla")
          for y, c in CALLS.items()],
        ("plan_2026_2030", "Plan Estatal de Vivienda 2026-2030: ayuda a jóvenes", "RD 326/2026 (BOE-A-2026-8872)",
         "en vigor desde el 24-abr-2026; la Comunidad aún no la ha convocado",
         "art. 133.1.e: 1.000 / 600 €; 500 / 250 € en municipios o núcleos de 10.000 habitantes o menos",
         5, "solo la persona (art. 133.1.d)", 300, 200, 60, 24,
         "5,5 o 6 × IPREM con discapacidad (art. 133.1.d); prorrogable 2 años más (art. 134); la Comunidad puede añadir "
         "requisitos (art. 8.1) y subir el tope con un estudio (art. 135)"),
        ("propuesta", "Propuesta del proyecto", "RD 326/2026, art. 135", "propuesta",
         "p75 del alquiler local (SERPAVI 2024) redondeado a 50 €, entre el tope del Plan y 1.000 €; habitación, el 60 %",
         5, "solo la persona (art. 133.1.d)", 300, 200, 60, 24,
         "Con cupos por jóvenes × necesidad × parte por debajo del límite de ingresos (simulador.py)"),
    ]
    return pd.DataFrame(rows, columns=list(SCHEMA["reglas"][2]))


def caps(m):
    conv = pd.read_csv(INTERIM / "topes_900_convocatorias.csv", dtype={"ine": str}).set_index("ine")
    rows = []
    for _, r in m.iterrows():
        p75 = r["serpavi_p75_2024"]
        rows.append((r["ine"], "bono_2022", float(r["tope_2022"]), r["tope_2022"] / 2))  # Acuerdo 2022, art. 5
        for rule, key in [("bono_2024", "hoy"), ("plan_2026_2030", "plan"), ("propuesta", "propuesta")]:
            rows.append((r["ine"], rule, *rb.caps(key, r["tope_2024"], r["pob_total_2024"], p75)))
        for y in CALLS:
            rows.append((r["ine"], f"ayudas_jovenes_{y}", float(conv.loc[r["ine"], f"tope_ayudas_{y}"]), None))
    return pd.DataFrame(rows, columns=list(SCHEMA["topes"][2]))


def requests(names):
    """Rows with a 3-digit municipality code only: the Bono file ends with requests that never named a dwelling."""
    def one(folder):
        t = leer_csv(next((RAW / folder).glob("*.csv")))
        keep = t["municipio"].astype(str).str.fullmatch(r"\d{3}")
        return t[keep], t.loc[~keep, "solicitudes"].sum()
    bono, bono_out = one("spacm_bono_alquiler_joven_2022")
    ay, ay_out = one("spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos")
    bono = bono.assign(programa="bono_alquiler_joven", anio_convocatoria=2022)
    ay = ay.assign(programa=ay["programa"].map({5.1: "ayudas_alquiler_jovenes", 2.0: "ayudas_alquiler_escasos_recursos"}),
                   anio_convocatoria=ay["año_convocatoria"])
    t = (pd.concat([bono, ay]).rename(columns={"municipio": "ine"})
         .groupby(["ine", "programa", "anio_convocatoria"], as_index=False)[["solicitudes", "aceptadas", "rechazadas"]].sum())
    assert t["ine"].isin(names).all(), sorted(set(t["ine"]) - set(names))
    return t, {"solicitudes_bono_2022_sin_municipio": int(bono_out), "solicitudes_ayudas_sin_municipio": int(ay_out)}


def serpavi():
    t = pd.read_csv(INTERIM / "serpavi_madrid_municipios.csv", dtype={"ine": str})
    return pd.DataFrame({"ine": t["ine"], "anio": t["year"], "viviendas": t["n"].round().astype("Int64"),
                         "mediana": t["med"], "p25": t["p25"], "p75": t["p75"]})


def districts():
    """Madrid city's districts in SERPAVI's 'Distritos' sheet, with the names of the portal's boundaries."""
    t = pd.read_csv(INTERIM / "serpavi_madrid_distritos.csv", dtype={"ine": str})
    t = t[t["ine"] == "079"]
    code = "079" + t["cudis"].astype("int64").astype(str).str[-2:]  # 2807901 -> '07901', as in the app's map
    g = json.loads((INTERIM / "distritos_madrid_wgs84.geojson").read_text(encoding="utf-8"))
    names = {f["properties"]["ine"]: f["properties"]["nombre"] for f in g["features"]}
    return pd.DataFrame({"distrito": code, "ine": t["ine"], "nombre": code.map(names), "anio": t["year"],
                         "viviendas": t["n"].round().astype("Int64"), "mediana": t["med"], "p25": t["p25"],
                         "p75": t["p75"]})


def simulation():
    """The simulator's scenarios with the central beta, recomputed from its functions (its CSV keeps 1 decimal)."""
    s, _ = simulador.load()
    beta = json.loads((ROOT / "resultados" / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
        "real_cap_and_uniform_900"]["real_cap"]["beta"]
    n_bonos = simulador.BUDGET_EUR / simulador.BONO_EUR
    out = []
    for name, (cap, how) in simulador.rules(s).items():
        req, sh = simulador.requests(s, cap, beta)
        bonos = simulador.allocate(req, req if how == "llegada" else simulador.need_weights(s, how), n_bonos)
        out.append(pd.DataFrame({"ine": s["ine"], "escenario": name, "reparto": "llegada" if how == "llegada" else
                                 "cupos: " + " × ".join(["jóvenes", "necesidad" + ("²" if how[1] == 2 else ""),
                                                          *(["límite de ingresos"] if "requisito" in how else [])]),
                                 "tope_piso": cap, "solicitudes": req, "bonos": bonos, "parte_por_encima": sh}))
    return pd.concat(out, ignore_index=True)


def sources():
    rows = []
    for name, base in SOURCES:
        m = json.loads((base / name / "metadata.json").read_text(encoding="utf-8"))
        if name == "serpavi_mivau":
            rows.append((name, m["title"], m["publisher"], m["license"], m["source_page"], m["file_last_modified"],
                         str((base / name).relative_to(ROOT)).replace("\\", "/")))
        else:
            rows.append((name, m["title"], CM, m["license_title"] + " 4.0", m["portal_url"], m["metadata_modified"][:10],
                         str((base / name).relative_to(ROOT)).replace("\\", "/")))
    return pd.DataFrame(rows, columns=list(SCHEMA["fuentes"][2]))


def dictionary():
    return pd.DataFrame([(t, c, *spec) for t, (_, _, cols) in SCHEMA.items() for c, spec in cols.items()],
                        columns=list(SCHEMA["diccionario"][2]))


def commit():
    """HEAD, and whether the code differs from it (the database and its dictionary are written here, so they do not count)."""
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    try:
        dirty = git("status", "--porcelain", "--", ".", f":!{DB.relative_to(ROOT).as_posix()}",
                    f":!{DOC.relative_to(ROOT).as_posix()}")
        return git("rev-parse", "--short", "HEAD") + (" (con cambios sin commit)" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "sin git"


def create(con):
    for table, (_, pk, cols) in SCHEMA.items():
        defs = [f'"{c}" {spec[0]}' for c, spec in cols.items()]
        defs.append(f"PRIMARY KEY ({', '.join(pk)})")
        defs += [f"FOREIGN KEY ({c}) REFERENCES {ref}({SCHEMA[ref][1][0]})" for c, ref in FOREIGN.get(table, [])]
        con.execute(f"CREATE TABLE {table} ({', '.join(defs)})")
    con.execute("""CREATE VIEW ficha_municipio AS
        SELECT m.ine, m.municipio, m.pob_total_2024, m.jovenes_20_34_2024, m.indice_necesidad,
               h.tope_piso AS tope_hoy, p.tope_piso AS tope_plan, x.tope_piso AS tope_propuesta,
               a.mediana AS alquiler_mediano_2024, a.p75 AS alquiler_p75_2024
        FROM municipios m
        JOIN topes h ON h.ine = m.ine AND h.regla = 'bono_2024'
        JOIN topes p ON p.ine = m.ine AND p.regla = 'plan_2026_2030'
        JOIN topes x ON x.ine = m.ine AND x.regla = 'propuesta'
        LEFT JOIN alquiler_serpavi a ON a.ine = m.ine AND a.anio = 2024""")


def insert(con, table, df):
    cols = list(SCHEMA[table][2])
    df = df[cols].astype(object).where(df[cols].notna(), None)
    con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})",
                    [tuple(v.item() if isinstance(v, np.generic) else v for v in row) for row in df.itertuples(index=False)])


def verify(con, m):
    """The database says the same as the files it comes from, and every key and reference holds."""
    q = lambda sql: con.execute(sql).fetchall()  # noqa: E731
    assert not q("PRAGMA foreign_key_check"), q("PRAGMA foreign_key_check")
    assert q("SELECT COUNT(*) FROM municipios") == [(179,)]
    assert q("SELECT COUNT(*) FROM ficha_municipio") == [(179,)]
    assert q("SELECT COUNT(*) FROM topes") == [(179 * 8,)]
    bono = q("SELECT SUM(solicitudes), SUM(aceptadas) FROM solicitudes WHERE programa = 'bono_alquiler_joven'")[0]
    assert bono == (int(m["bono_solicitudes"].sum()), int(m["bono_aceptadas"].sum())), bono
    old = pd.read_csv(INTERIM / "municipios.csv", dtype={"ine": str}).set_index("ine")["ayudas51_solicitudes"]
    ay = pd.read_sql("SELECT ine, SUM(solicitudes) AS n FROM solicitudes WHERE programa = 'ayudas_alquiler_jovenes' "
                     "GROUP BY ine", con).set_index("ine")["n"]
    # municipios.csv only has the Bono's 159 municipalities; the base also keeps the Ayudas of the other 20
    assert np.array_equal(ay.reindex(old.index, fill_value=0).to_numpy(int), old.to_numpy(int)), "Ayudas distintas"
    assert q("SELECT COUNT(*) FROM topes WHERE regla = 'bono_2024' AND tope_piso = 900") == [(55,)]
    assert q("SELECT COUNT(*) FROM topes WHERE regla = 'bono_2022' AND tope_piso = 900") == [(29,)]
    sim = pd.read_csv(INTERIM / "simulador_municipios.csv", dtype={"ine": str}).set_index("ine")
    got = pd.read_sql("SELECT ine, bonos FROM simulacion WHERE escenario = 'actual_2024_55'", con).set_index("ine")["bonos"]
    assert np.allclose(got.round(1), sim.loc[got.index, "bonos_actual_2024_55"]), "simulación distinta del simulador"
    total = q("SELECT escenario, SUM(bonos) FROM simulacion GROUP BY escenario")
    assert all(abs(v - simulador.BUDGET_EUR / simulador.BONO_EUR) < 1e-6 for _, v in total), total
    p75 = pd.read_sql("SELECT ine, p75 FROM alquiler_serpavi WHERE anio = 2024", con).set_index("ine")["p75"]
    assert np.allclose(p75, m.set_index("ine").loc[p75.index, "serpavi_p75_2024"], equal_nan=True)
    assert q("SELECT COUNT(DISTINCT distrito), COUNT(DISTINCT nombre) FROM alquiler_distritos_madrid") == [(21, 21)]
    # the two sheets of the SERPAVI count the same rentals: the 21 districts add up to the city
    city = q("SELECT d.anio, SUM(d.viviendas), a.viviendas FROM alquiler_distritos_madrid d JOIN alquiler_serpavi a "
             "ON a.ine = d.ine AND a.anio = d.anio GROUP BY d.anio")
    assert len(city) == 14 and all(s == v for _, s, v in city), city
    documented = {(t, c) for t, c in q("SELECT tabla, columna FROM diccionario")}
    real = {(t, c[1]) for t in SCHEMA for c in q(f"PRAGMA table_info({t})")}
    assert documented == real, documented ^ real
    return {t: q(f"SELECT COUNT(*) FROM {t}")[0][0] for t in SCHEMA}


def markdown(counts, meta):
    lines = ["# Diccionario de `data/bono_alquiler_joven.sqlite`", "",
             "Una sola base SQLite con todo lo que usa el proyecto, por municipio (y el alquiler de Madrid capital también "
             "por distrito). La genera `scripts/base_datos.py` (este "
             "fichero también, con el mismo diccionario que va dentro de la base, en la tabla `diccionario`). La leen la app "
             "y, más adelante, el servidor MCP.", "",
             f"Hecha el {meta['creada']} desde el commit `{meta['commit']}`. Clave de municipio: `ine` (3 cifras). "
             "Vista `ficha_municipio`: los topes de hoy, del Plan y de la propuesta junto al alquiler de 2024.", "",
             "```sql", "SELECT municipio, tope_hoy, tope_plan, tope_propuesta, alquiler_p75_2024",
             "FROM ficha_municipio WHERE alquiler_p75_2024 > tope_hoy ORDER BY jovenes_20_34_2024 DESC;", "```", ""]
    for table, (desc, pk, cols) in SCHEMA.items():
        lines += [f"## `{table}` ({counts[table]} filas)", "", f"{desc}. Clave: `{', '.join(pk)}`.", "",
                  "| Columna | Tipo | Unidad | Qué es | Fuente |", "|---|---|---|---|---|"]
        lines += [f"| `{c}` | {t} | {u} | {d} | {f} |" for c, (t, u, d, f) in cols.items()]
        lines.append("")
    return "\n".join(lines)


def main():
    m = municipalities()
    req, outside = requests(set(m["ine"]))
    meta = {"creada": datetime.date.today().isoformat(), "commit": commit(), "script": "scripts/base_datos.py",
            "licencia_datos": "Cada dato conserva la licencia de su fuente (tabla fuentes)", **outside}
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    create(con)
    for table, df in [("municipios", m), ("reglas", rules()), ("topes", caps(m)), ("solicitudes", req),
                      ("alquiler_serpavi", serpavi()), ("alquiler_distritos_madrid", districts()),
                      ("simulacion", simulation()), ("fuentes", sources()),
                      ("diccionario", dictionary()),
                      ("metadatos", pd.DataFrame({"clave": list(meta), "valor": [str(v) for v in meta.values()]}))]:
        insert(con, table, df)
    con.commit()
    counts = verify(con, m)
    con.execute("VACUUM")
    con.close()
    DOC.write_text(markdown(counts, meta), encoding="utf-8")
    print("ok", DB.relative_to(ROOT), f"{DB.stat().st_size / 1e6:.2f} MB", counts)


if __name__ == "__main__":
    main()

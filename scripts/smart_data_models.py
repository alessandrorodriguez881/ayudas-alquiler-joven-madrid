"""The project's indicators per municipality as Smart Data Models (16-Nov-2026): one KeyPerformanceIndicator entity per
municipality and indicator, in the keyValues format of the official examples, validated against the official schema.

Smart Data Models (smartdatamodels.org) are the open data models of FIWARE, TM Forum, IUDX and OASC; an NGSI context
broker (or any program) can load these entities as they are. The indicators come from the project's SQLite database
(scripts/base_datos.py), so they are the same numbers as the app and the report:
  - share of the 2024 rents (SERPAVI, flats) above the cap of today's Bono, of the Plan 2026-2030 and of the proposal
  - need index 0-100 (scripts/necesidad_2024.py)
  - Bono Alquiler Joven 2022 requests and granted aids per 1,000 young people aged 20-34
The schema (dataModel.KeyPerformanceIndicator) and the common schema it uses are kept in
data/raw_2026-11-16/smart_data_models/ with their address and SHA-1, so the validation works offline.
Usage:  python -P scripts/smart_data_models.py   -> data/smart_data_models/KeyPerformanceIndicator_municipios.json
"""
import hashlib
import json
import math
import sqlite3
import sys
import urllib.request

import pandas as pd
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT, share_above  # noqa: E402

DB = ROOT / "data" / "bono_alquiler_joven.sqlite"
SCHEMAS = ROOT / "data" / "raw_2026-11-16" / "smart_data_models"
SCHEMA_URLS = {
    "schema.json": "https://raw.githubusercontent.com/smart-data-models/dataModel.KeyPerformanceIndicator/master/"
                   "KeyPerformanceIndicator/schema.json",
    "common-schema.json": "https://smart-data-models.github.io/data-models/common-schema.json",
}
OUT_DIR = ROOT / "data" / "smart_data_models"
OUT = OUT_DIR / "KeyPerformanceIndicator_municipios.json"
REPO = "https://github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid"
PROVIDER = "Los invisibles del Bono (DataMad 2026)"
PORTAL = "https://datos.comunidad.madrid/dataset/"
SERPAVI = "https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi"
RULE_NAMES = {"bono_2024": "del Bono Alquiler Joven de hoy (convocatoria de 2024)",
              "plan_2026_2030": "del Plan Estatal de Vivienda 2026-2030 (RD 326/2026, art. 133.1.e)",
              "propuesta": "de la propuesta del proyecto (el tope del Plan o el alquiler local, hasta 1.000 €)"}


def schemas():
    SCHEMAS.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, url in SCHEMA_URLS.items():
        path = SCHEMAS / name
        if not path.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "datamad-2026-script"})
            with urllib.request.urlopen(req, timeout=60) as r:
                path.write_bytes(r.read())
        meta[name] = {"url": url, "sha1": hashlib.sha1(path.read_bytes()).hexdigest()}
    meta_path = SCHEMAS / "metadata.json"
    if not meta_path.exists():
        meta_path.write_text(json.dumps({"name": "smart_data_models", "downloaded": "2026-11-16",
                                         "license": "Smart Data Models: CC-BY-4.0 (modelos de datos)", "files": meta},
                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    kpi = json.loads((SCHEMAS / "schema.json").read_text(encoding="utf-8"))
    common = json.loads((SCHEMAS / "common-schema.json").read_text(encoding="utf-8"))
    registry = Registry().with_resource(SCHEMA_URLS["common-schema.json"], Resource.from_contents(common))
    return Draft202012Validator(kpi, registry=registry), kpi.get("$id")


def indicators():
    with sqlite3.connect(DB) as con:
        m = pd.read_sql("SELECT ine, ine5, municipio, indice_necesidad, jovenes_20_34_2022 FROM municipios", con)
        caps = pd.read_sql("SELECT ine, regla, tope_piso FROM topes WHERE regla IN ('bono_2024', 'plan_2026_2030', "
                           "'propuesta')", con).pivot(index="ine", columns="regla", values="tope_piso")
        rent = pd.read_sql("SELECT ine, p25, p75 FROM alquiler_serpavi WHERE anio = 2024", con).set_index("ine")
        req = pd.read_sql("SELECT ine, solicitudes, aceptadas FROM solicitudes WHERE programa = 'bono_alquiler_joven' "
                          "AND anio_convocatoria = 2022", con).set_index("ine")
    m = m.set_index("ine").join(caps).join(rent).join(req)
    rows = []
    for ine, r in m.iterrows():
        def add(slug, name, desc, value, period, formula, see_also, unit):
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return
            rows.append((ine, r, slug, name, desc, round(float(value), 4), period, formula, see_also, unit))
        for rule in ("bono_2024", "plan_2026_2030", "propuesta"):
            cap = r[rule]
            share = share_above(cap, r["p25"], r["p75"]) if not math.isnan(cap) else float("nan")
            add(f"alquiler-sobre-tope-{rule.replace('_', '-')}",
                f"Alquiler por encima del tope {('de hoy', 'del Plan 2026-2030', 'de la propuesta')[('bono_2024', 'plan_2026_2030', 'propuesta').index(rule)]}",
                f"Parte de los alquileres de pisos de 2024 (SERPAVI) que pasa del tope {RULE_NAMES[rule]}: "
                f"{cap:.0f} € al mes",
                share, ("2024-01-01", "2024-12-31"),
                f"Reparto log-normal entre los percentiles 25 y 75 del alquiler de pisos de 2024; tope {cap:.0f} €",
                [SERPAVI, f"{REPO}/blob/main/scripts/comun.py"], "proporción (0-1)")
        add("indice-de-necesidad", "Índice de necesidad",
            "Índice de necesidad de 0 a 100: media de los rangos del esfuerzo de alquiler, el paro juvenil y los hogares "
            "de alquiler", r["indice_necesidad"], ("2024-01-01", "2024-12-31"),
            "Media de tres rangos percentiles entre los municipios con los tres datos",
            [f"{REPO}/blob/main/scripts/necesidad_2024.py"], "0-100")
        young = r["jovenes_20_34_2022"]
        for slug, col, name in (("solicitudes-bono-2022-por-1000-jovenes", "solicitudes", "Solicitudes"),
                                ("bonos-2022-por-1000-jovenes", "aceptadas", "Bonos concedidos")):
            value = 1000 * r[col] / young if young and young >= 500 and not math.isnan(r[col]) else float("nan")
            add(slug, f"{name} del Bono Alquiler Joven 2022 por cada 1.000 jóvenes",
                f"{name} del Bono Alquiler Joven 2022 por cada 1.000 jóvenes de 20 a 34 años (solo con 500 jóvenes o más)",
                value, ("2022-01-01", "2022-12-31"), f"1.000 × {col} / jóvenes de 20 a 34 años (2022)",
                [f"{PORTAL}spacm_bono_alquiler_joven_2022", f"{PORTAL}poblacion_censada_por_edad_nacionalidad_y_sexo"],
                "por cada 1.000 jóvenes")
    return rows


def entity(ine, r, slug, name, desc, value, period, formula, see_also, unit):
    return {
        "id": f"urn:ngsi-ld:KeyPerformanceIndicator:invisibles-del-bono:{r['ine5']}:{slug}",
        "type": "KeyPerformanceIndicator",
        "name": f"{name}: {r['municipio']}",
        "description": f"{desc}. Unidad: {unit}.",
        "category": ["quantitative"],
        "organization": "Comunidad de Madrid: Bono Alquiler Joven",
        "process": "Bono Alquiler Joven",
        "provider": PROVIDER,
        "dataProvider": PROVIDER,
        "source": REPO,
        "seeAlso": see_also,
        "kpiValue": value,
        "calculationPeriod": {"from": period[0], "to": period[1]},
        "calculationMethod": "automatic",
        "calculationFrequency": "yearly",
        "calculationFormula": formula,
        "area": r["municipio"],
        "address": {"addressLocality": r["municipio"], "addressRegion": "Comunidad de Madrid", "addressCountry": "ES"},
    }


def main():
    validator, schema_id = schemas()
    ents = [entity(*row) for row in indicators()]
    errors = [(e["id"], err.message) for e in ents for err in validator.iter_errors(e)]
    if errors:
        sys.exit(f"{len(errors)} errors against the schema, first: {errors[0]}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False) for e in ents) + "\n]\n", encoding="utf-8")
    kinds = pd.Series([e["id"].rsplit(":", 1)[1] for e in ents]).value_counts().sort_index()
    print(f"{len(ents)} entities, valid against {schema_id}")
    print(kinds.to_string())


if __name__ == "__main__":
    main()

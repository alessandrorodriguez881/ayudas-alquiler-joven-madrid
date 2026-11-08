"""What the MCP server answers, read from data/bono_alquiler_joven.sqlite (scripts/base_datos.py), opened read-only.
Every answer carries the sources of its figures (table fuentes), so an AI that uses it can cite them. No MCP code here:
servidor.py registers these functions as tools, and they can be tested or reused without the SDK."""
import json
import math
import pathlib
import re
import sqlite3
import sys
from contextlib import closing

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bono_alquiler_joven.sqlite"
sys.path.insert(0, str(ROOT / "scripts"))
import reglas_bono as rb  # noqa: E402
from comun import norm, share_above  # noqa: E402

MAX_ROWS = 500
RULE_IN_DB = {"hoy": "bono_2024", "plan": "plan_2026_2030", "propuesta": "propuesta"}
CAP_RULES = ("bono_2022", "bono_2024", "plan_2026_2030", "propuesta")
SIM = {"hoy": "actual_2024_55", "plan": "plan_estatal", "propuesta": "necesidad_requisito_plan_p75_hasta_1000"}
# the simulator's central beta: the part of the deterrence due to the cap (exploratorio_topes_falsos.py)
BETA = json.loads((ROOT / "resultados" / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
    "real_cap_and_uniform_900"]["real_cap"]["beta"]
REPO = "github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid"
BETA_ES = f"{BETA:.2f}".replace(".", ",").replace("-", "−")
NOTE = (f"Datos agregados por municipio. Simulación con β = {BETA_ES} (la parte del efecto que se debe al tope; análisis "
        f"exploratorio) y el presupuesto del Bono 2024 (31,8 M€, 5.300 bonos de 250 €). Método: {REPO}")


def rows(sql, params=()):
    with closing(sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(sql, params).fetchmany(MAX_ROWS)]


def sources(*names):
    marks = ", ".join("?" * len(names))
    return rows(f"SELECT fuente, titulo, publica, licencia, url FROM fuentes WHERE fuente IN ({marks})", names)


def resolve(municipio):
    """One municipality from a name (accents, articles and order do not matter) or a 3-digit INE code."""
    every = rows("SELECT ine, municipio FROM municipios")
    key = norm(municipio)
    exact = [m for m in every if m["ine"] == str(municipio).strip() or norm(m["municipio"]) == key]
    found = exact or [m for m in every if key and key in norm(m["municipio"])]
    if len(found) != 1:
        hint = ", ".join(m["municipio"] for m in found[:10]) or "ninguno"
        raise ValueError(f"«{municipio}» no identifica un solo municipio de la Comunidad de Madrid (coincidencias: {hint})")
    return found[0]


def buscar_municipio(texto):
    key = norm(texto)
    return [m for m in rows("SELECT ine, municipio, pob_total_2024 FROM municipios ORDER BY municipio")
            if key in norm(m["municipio"])]


def ficha_municipio(municipio):
    m = resolve(municipio)
    ine = m["ine"]
    r = rows("SELECT * FROM municipios WHERE ine = ?", (ine,))[0]
    rent = {x["anio"]: x for x in rows("SELECT anio, viviendas, mediana, p25, p75 FROM alquiler_serpavi WHERE ine = ? "
                                       "AND anio IN (2022, 2024)", (ine,))}
    r24, r22 = rent.get(2024, {}), rent.get(2022, {})
    caps = rows(f"SELECT t.regla, r.nombre, t.tope_piso, t.tope_habitacion FROM topes t JOIN reglas r USING (regla) "
                f"WHERE t.ine = ? AND t.regla IN ({', '.join('?' * len(CAP_RULES))})", (ine, *CAP_RULES))
    for c in caps:
        share = share_above(c["tope_piso"], r24.get("p25"), r24.get("p75"))
        c["parte_alquiler_2024_por_encima"] = None if math.isnan(share) else round(share, 3)
    req = rows("SELECT programa, anio_convocatoria, solicitudes, aceptadas, rechazadas FROM solicitudes WHERE ine = ? "
               "ORDER BY programa, anio_convocatoria", (ine,))
    sim = {k: rows("SELECT tope_piso, solicitudes, bonos, parte_por_encima FROM simulacion WHERE ine = ? AND escenario = ?",
                   (ine, v)) for k, v in SIM.items()}
    bono22 = next((x for x in req if x["programa"] == "bono_alquiler_joven"), None)
    cap22 = next(c["tope_piso"] for c in caps if c["regla"] == "bono_2022")
    share22 = share_above(cap22, r22.get("p25"), r22.get("p75"))
    not_made = None  # requests not made in 2022 because of the cap: requests with the share at 0, minus actual ones
    if bono22 and not math.isnan(share22):
        not_made = round(bono22["solicitudes"] * (math.exp(-BETA * share22) - 1))  # as simulador.not_made
    return {
        "municipio": r["municipio"], "ine": ine, "poblacion_2024": r["pob_total_2024"],
        "jovenes_20_34_2024": r["jovenes_20_34_2024"],
        "indice_necesidad_0_100": None if r["indice_necesidad"] is None else round(r["indice_necesidad"], 1),
        "grupo_necesidad": r["grupo_necesidad"],
        "alquiler_mensual_2024": {"mediana": r24.get("mediana"), "p25": r24.get("p25"), "p75": r24.get("p75"),
                                  "viviendas": r24.get("viviendas")} if r24 else None,
        "topes": caps,
        "solicitudes": req,
        "solicitudes_bono_2022_no_hechas_por_el_tope": not_made,
        "bonos_simulados": {k: round(v[0]["bonos"], 1) if v else None for k, v in sim.items()},
        "parte_irpf_bajo_3iprem_2024": r["parte_irpf_bajo_3iprem_2024"],
        "nota": NOTE + ". «solicitudes_bono_2022_no_hechas_por_el_tope» es una estimación del modelo: las que habría "
                "con todo el alquiler de 2022 por debajo del tope, menos las que hubo.",
        "fuentes": sources("spacm_bono_alquiler_joven_2022", "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos",
                           "poblacion_censada_por_edad_nacionalidad_y_sexo", "serpavi_mivau"),
    }


def puedo_pedirla(municipio, edad, precio, ingresos, tipo="piso", con_quien="solo", jovenes_que_firman=1,
                  ingresos_otros=0.0, incluye="vivienda", gastos_sin_separar=False, fuente_regular_de_ingresos=True,
                  nacionalidad_o_residencia=True, discapacidad="no", exclusiones=(), otra_ayuda_al_alquiler=False,
                  iprem_anual=rb.IPREM_YEAR_2024):
    m = resolve(municipio)
    case = rb.Case(age=int(edad), kind=tipo, price=float(precio), includes=incluye, expenses_included=bool(gastos_sin_separar),
                   living=con_quien, sharers=int(jovenes_que_firman), income=float(ingresos),
                   others_income=float(ingresos_otros), regular_income=bool(fuente_regular_de_ingresos),
                   nationality=bool(nacionalidad_o_residencia), disability=str(discapacidad),
                   exclusions=frozenset(exclusiones), other_rent_aid=bool(otra_ayuda_al_alquiler))
    caps = {c["regla"]: c for c in rows("SELECT regla, tope_piso, tope_habitacion FROM topes WHERE ine = ?", (m["ine"],))}
    out = {"municipio": m["municipio"], "ine": m["ine"]}
    for rule, key in RULE_IN_DB.items():
        res = rb.evaluate(case, rule, caps[key]["tope_piso"], caps[key]["tope_habitacion"], iprem=float(iprem_anual))
        out[rule] = {"regla": rb.RULES[rule], "cumple": res.eligible, "ayuda_al_mes": res.monthly, "meses": res.months,
                     "total": round(res.monthly * res.months, 2),
                     "tope": res.room_cap if tipo == "habitacion" else res.flat_cap,
                     "requisitos": [{"requisito": c.key, "articulo": c.article, "cumple": c.ok, "explicacion": c.text}
                                    for c in res.checks]}
    out["aviso"] = ("Orientativo: decide la Comunidad de Madrid. Cumplir no asegura la ayuda: hoy se da por orden de "
                    "llegada mientras hay dinero. El Plan 2026-2030 aún no está convocado en la Comunidad y puede añadir "
                    "requisitos. Normas: Acuerdo del Bono Alquiler Joven 2024 (BDNS 805618) y RD 326/2026 (BOE-A-2026-8872).")
    return out


def reglas():
    return rows("SELECT * FROM reglas")


def diccionario(tabla=None):
    if tabla:
        return rows("SELECT tabla, columna, tipo, unidad, descripcion, fuente FROM diccionario WHERE tabla = ?", (tabla,))
    return rows("SELECT tabla, columna, tipo, unidad, descripcion, fuente FROM diccionario")


def consulta_sql(sql):
    """One SELECT (or WITH ... SELECT) on the read-only database; at most MAX_ROWS rows."""
    text = sql.strip().rstrip(";").strip()
    if not re.match(r"(?is)^(select|with)\b", text) or ";" in text:
        raise ValueError("Solo se admite una consulta SELECT (o WITH … SELECT), sin «;» en medio")
    with closing(sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)) as con:
        con.execute("PRAGMA query_only = ON")
        cur = con.execute(text)
        cols = [d[0] for d in cur.description]
        got = cur.fetchmany(MAX_ROWS + 1)
    return {"columnas": cols, "filas": [list(x) for x in got[:MAX_ROWS]], "recortado": len(got) > MAX_ROWS}

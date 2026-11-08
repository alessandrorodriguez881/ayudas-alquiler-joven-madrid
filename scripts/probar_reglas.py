"""Checks of scripts/reglas_bono.py against cases worked out by hand from the norm, and against the caps the simulator uses.
Run:  python -P scripts/probar_reglas.py   (after preparar_datos.py, simulador.py needs its tables)"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
import habitaciones  # noqa: E402
import reglas_bono as rb  # noqa: E402
import simulador  # noqa: E402

BIG_900 = {"hoy": (900.0, 450.0), "plan": (1000.0, 600.0)}  # an Annex II municipality of more than 10,000 people
SMALL_600 = {"hoy": (600.0, 300.0), "plan": (500.0, 250.0)}  # a municipality of 10,000 people or fewer


def run(case, caps):
    return {r: rb.evaluate(case, r, *caps[r]) for r in caps}


def expect(name, res, **want):
    """want: rule -> (eligible, monthly)."""
    for rule, (ok, monthly) in want.items():
        got = res[rule]
        failed = [ch.key for ch in got.checks if not ch.ok]
        assert (got.eligible, got.monthly) == (ok, monthly), (name, rule, got.eligible, got.monthly, failed)
    print("ok", name)


# One person, whole flat
expect("piso de 850 € en un municipio del anexo II, 20.000 € al año",
       run(rb.Case(age=28, price=850, income=20000), BIG_900), hoy=(True, 250.0), plan=(True, 300.0))
expect("piso de 950 €: por encima de los 900 € de hoy, dentro de los 1.000 € del Plan",
       run(rb.Case(age=28, price=950, income=20000), BIG_900), hoy=(False, 0.0), plan=(True, 300.0))
expect("piso de 400 €: el Plan da el 60 % (240 €); hoy, 250 €",
       run(rb.Case(age=25, price=400, income=15000), BIG_900), hoy=(True, 250.0), plan=(True, 240.0))
expect("piso de 200 €: hoy la ayuda no pasa del alquiler",
       run(rb.Case(age=25, price=200, income=15000), BIG_900), hoy=(True, 200.0), plan=(True, 120.0))
expect("municipio pequeño, piso de 550 €: cabe hoy (600 €) y no en el Plan (500 €)",
       run(rb.Case(age=30, price=550, income=18000), SMALL_600), hoy=(True, 250.0), plan=(False, 0.0))

# Age and income limits, with their edges
for a, ok in [(17, False), (18, True), (35, True), (36, False)]:
    expect(f"edad {a}", run(rb.Case(age=a, price=500, income=10000), BIG_900),
           hoy=(ok, 250.0 if ok else 0.0), plan=(ok, 300.0 if ok else 0.0))
expect("ingresos de 25.200 €, justo 3 × IPREM", run(rb.Case(age=30, price=700, income=25200), BIG_900),
       hoy=(True, 250.0), plan=(True, 300.0))
expect("ingresos de 25.201 €: fuera hoy, dentro del Plan (5 × IPREM = 42.000 €)",
       run(rb.Case(age=30, price=700, income=25201), BIG_900), hoy=(False, 0.0), plan=(True, 300.0))
expect("45.000 € sin discapacidad: fuera del Plan", run(rb.Case(age=30, price=700, income=45000), BIG_900),
       plan=(False, 0.0))
expect("45.000 € con discapacidad del 33 %: dentro (5,5 × IPREM = 46.200 €)",
       run(rb.Case(age=30, price=700, income=45000, disability="33"), BIG_900), plan=(True, 300.0))
expect("49.000 € con discapacidad del 65 %: dentro (6 × IPREM = 50.400 €)",
       run(rb.Case(age=30, price=700, income=49000, disability="65"), BIG_900), plan=(True, 300.0))

# Who lives in the flat
expect("con sus padres: hoy cuentan 10.000 + 20.000 €; en el Plan, solo sus 10.000 €",
       run(rb.Case(age=24, price=800, living="otros", income=10000, others_income=20000), BIG_900),
       hoy=(False, 0.0), plan=(True, 300.0))
expect("tres jóvenes que firman un piso de 900 €: hoy 250 € cada uno; Plan, 60 % de 300 € = 180 €",
       run(rb.Case(age=26, price=900, living="jovenes", sharers=3, income=15000), BIG_900),
       hoy=(True, 250.0), plan=(True, 180.0))
expect("cuatro jóvenes en un piso de 900 €: hoy la ayuda se reparte (225 € cada uno)",
       run(rb.Case(age=26, price=900, living="jovenes", sharers=4, income=15000), BIG_900),
       hoy=(True, 225.0), plan=(True, 135.0))
expect("tres jóvenes en un piso de 1.200 € con contrato conjunto: no cabe en ningún tope de piso",
       run(rb.Case(age=26, price=1200, living="jovenes", sharers=3, income=15000), BIG_900),
       hoy=(False, 0.0), plan=(False, 0.0))

# Rooms
expect("habitación de 320 € en un municipio pequeño: no cabe hoy (300 €) ni en el Plan (250 €)",
       run(rb.Case(age=22, kind="habitacion", price=320, income=9000), SMALL_600), hoy=(False, 0.0), plan=(False, 0.0))
expect("habitación de 320 € en el anexo II: hoy 250 €; Plan, 60 % = 192 €",
       run(rb.Case(age=22, kind="habitacion", price=320, income=9000), BIG_900), hoy=(True, 250.0), plan=(True, 192.0))
expect("habitación de 500 €: no cabe hoy (450 €); Plan, tope de 200 €",
       run(rb.Case(age=22, kind="habitacion", price=500, income=9000), BIG_900), hoy=(False, 0.0), plan=(True, 200.0))

# Price with a garage, storage room or bills inside (art. 5)
expect("700 € con garaje sin desglosar: cuentan 560 €, cabe en 600 €",
       run(rb.Case(age=29, price=700, includes="garaje", income=12000), SMALL_600), hoy=(True, 250.0))
expect("640 € con trastero: cuentan 608 €, no cabe en 600 €",
       run(rb.Case(age=29, price=640, includes="trastero", income=12000), SMALL_600), hoy=(False, 0.0))
expect("630 € con gastos sin desglosar: cuentan 598,50 €, cabe en 600 €",
       run(rb.Case(age=29, price=630, expenses_included=True, income=12000), SMALL_600), hoy=(True, 250.0))

# Exclusions and other aid
expect("alguien del piso tiene una vivienda en propiedad: fuera hoy; en el Plan solo cuenta el solicitante",
       run(rb.Case(age=27, price=700, income=15000, exclusions=frozenset({"vivienda_conviviente"})), BIG_900),
       hoy=(False, 0.0), plan=(True, 300.0))
expect("familiar del casero: fuera en las dos",
       run(rb.Case(age=27, price=700, income=15000, exclusions=frozenset({"familiar_casero"})), BIG_900),
       hoy=(False, 0.0), plan=(False, 0.0))
expect("cobra otra ayuda al alquiler: fuera en las dos",
       run(rb.Case(age=27, price=700, income=15000, other_rent_aid=True), BIG_900), hoy=(False, 0.0), plan=(False, 0.0))
expect("sin fuente regular de ingresos: fuera hoy; el Plan no lo pide (la Comunidad puede añadirlo)",
       run(rb.Case(age=27, price=700, income=15000, regular_income=False), BIG_900), hoy=(False, 0.0), plan=(True, 300.0))

# Caps by municipality: the same as the simulator and habitaciones.py for every municipality they use
s, _ = simulador.load()
flat_rules = simulador.rules(s)
room_rules = habitaciones.caps_by_rule(s)
for rule, sim_flat, sim_room in [("hoy", s["tope_2024"].to_numpy(float), room_rules["actual_2024_55"][1]),
                                 ("plan", simulador.plan_cap(s), room_rules["plan_estatal"][1]),
                                 ("propuesta", flat_rules["necesidad_requisito_plan_p75_hasta_1000"][0],
                                  room_rules["propuesta_p75_hasta_1000"][1])]:
    mine = np.array([rb.caps(rule, c, p, q) for c, p, q in
                     zip(s["tope_2024"], s["pob_total_2024"], s["serpavi_p75_2024"])])
    assert np.array_equal(mine[:, 0], sim_flat) and np.array_equal(mine[:, 1], sim_room), rule
    print("ok", f"topes «{rule}» iguales que en el simulador ({len(s)} municipios)")
assert rb.caps("propuesta", 600, 5000, float("nan")) == (500.0, 300.0)  # no SERPAVI rents: the Plan's cap
print("ok", "sin alquileres del SERPAVI, la propuesta usa el tope del Plan")

# The list article -> line of code points at each function's def
lines = pathlib.Path(rb.__file__).read_text(encoding="utf-8").splitlines()
for row in rb.article_table():
    assert lines[row["linea"] - 1].startswith(f"def {row['funcion']}("), row
print("ok", f"lista artículo -> línea de código ({len(rb.article_table())} filas)")  # no "→": cp1252 consoles

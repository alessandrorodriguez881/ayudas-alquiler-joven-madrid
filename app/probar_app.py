"""Headless check of every page of the app (Streamlit AppTest, no browser): each page and each control runs without errors,
and the simulator with today's rule gives zero change.  Run:  python app/probar_app.py"""
import pathlib

from streamlit.testing.v1 import AppTest

APP = pathlib.Path(__file__).resolve().parent / "streamlit_app.py"


def ok(at, where):
    assert not at.exception, f"{where}: {at.exception[0].message}"
    print("ok", where)


at = AppTest.from_file(str(APP), default_timeout=120).run()
ok(at, "mapa")
for option in ["Cobertura del Bono", "Alquiler por encima del tope", "Con el Plan 2026-2030"]:
    at.segmented_control(key="medida").set_value(option).run()
    ok(at, f"mapa: {option}")

at.switch_page("app_pages/ficha.py").run()
ok(at, "ficha: Parla")
for name in ["Madrid", "Majadahonda", "Acebeda (La)"]:  # Acebeda: 7 young people and no SERPAVI rents
    at.selectbox(key="municipio").select(name).run()
    ok(at, f"ficha: {name}")

at.switch_page("app_pages/simular.py").run()
ok(at, "simulador: propuesta")
at.segmented_control(key="tope").set_value("Hoy (600 / 900 €)").run()
at.segmented_control(key="reparto").set_value("Orden de llegada (hoy)").run()
assert {m.delta for m in at.metric} <= {"0", "0,0", "0,0 puntos", "0,0 M€"}, [m.delta for m in at.metric]
ok(at, "simulador: la regla de hoy no cambia nada")
at.segmented_control(key="tope").set_value("Un tope único").run()
at.slider(key="tope_unico").set_value(1200).run()
at.segmented_control(key="beta").set_value("Sin efecto (0)").run()
at.slider(key="presupuesto").set_value(10.0).run()
ok(at, "simulador: tope único de 1.200 €, sin efecto, 10 M€")

at.switch_page("app_pages/metodo.py").run()
ok(at, "método y datos")

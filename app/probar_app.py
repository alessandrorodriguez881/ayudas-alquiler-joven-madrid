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

at.switch_page("app_pages/calculadora.py").run()
money = lambda: [m.value for m in at.metric]  # noqa: E731  (per rule: aid a month, aid in 24 months)
assert money() == ["250 €", "6.000 €", "300 €", "7.200 €", "300 €", "7.200 €"], money()
ok(at, "calculadora: piso de 750 € en Parla, 18.000 € al año")
at.number_input(key="calc_precio").set_value(950).run()
assert money()[:4] == ["0 €", "0 €", "300 €", "7.200 €"], money()  # above today's 900 EUR, inside the Plan's 1,000 EUR
ok(at, "calculadora: piso de 950 €")
at.radio(key="calc_convivencia").set_value("jovenes").run()
at.number_input(key="calc_n").set_value(3).run()
at.number_input(key="calc_precio").set_value(900).run()
assert money()[:4] == ["250 €", "6.000 €", "180 €", "4.320 €"], money()  # Plan: 60 % of 300 EUR each
ok(at, "calculadora: tres jóvenes en un piso de 900 €")
at.segmented_control(key="calc_tipo").set_value("Habitación").run()
at.selectbox(key="calc_municipio").select("Acebeda (La)").run()  # small, no SERPAVI rents: the proposal keeps the Plan
at.multiselect(key="calc_exclusiones").select("vivienda_conviviente").run()
ok(at, "calculadora: habitación en Acebeda, con una exclusión")

at.switch_page("app_pages/ficha.py").run()
ok(at, "ficha: Parla")
for name in ["Madrid", "Majadahonda", "Acebeda (La)"]:  # Acebeda: 7 young people and no SERPAVI rents
    at.selectbox(key="municipio").select(name).run()
    ok(at, f"ficha: {name}")

at.switch_page("app_pages/simular.py").run()
ok(at, "simulador: propuesta")
at.segmented_control(key="cuantia").set_value("La del Plan: hasta 300 €, sin pasar del 60 % del alquiler").run()
assert at.metric[4].value == "40,3 M€", at.metric[4].value  # simulador_reparto.json, plan_amount
ok(at, "simulador: propuesta con la cuantía del Plan")
at.segmented_control(key="mas_gente").set_value("Y todos los que entran nuevos").run()
assert at.metric[4].value == "58,1 M€", at.metric[4].value  # plan_income_limit, p_1
ok(at, "simulador: propuesta con el Plan y todos los que entran nuevos por su límite de ingresos")
at.segmented_control(key="mas_gente").set_value("Los mismos que en 2022").run()
at.segmented_control(key="cuantia").set_value("250 € (hoy)").run()
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

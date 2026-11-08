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
assert "Hoy cumples" in at.success[0].value, at.success[0].value
ok(at, "calculadora: piso de 750 € en Parla, 18.000 € al año")
at.number_input(key="calc_precio").set_value(950).run()
assert money()[:4] == ["0 €", "0 €", "300 €", "7.200 €"], money()  # above today's 900 EUR, inside the Plan's 1,000 EUR
assert "Hoy no cumples" in at.error[0].value and "Plan 2026-2030 y con nuestra propuesta, sí" in at.error[0].value
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

at.switch_page("app_pages/donde.py").run()
assert not at.error, [e.value for e in at.error]
card = lambda: [m.value for m in at.metric][3:]  # noqa: E731  (the three tiles, then the card, column by column)
# Parla (SERPAVI 2024 median 650 EUR): inside the cap, median, you pay | cap, aid, share of your income
assert card() == ["93 %", "650 €", "400 €", "900 €", "250 €", "27 %"], card()
ok(at, "dónde me llega: Parla, sola, 18.000 €")
at.segmented_control(key="donde_como").set_value("Compartiendo piso").run()
at.number_input(key="donde_n").set_value(3).run()
at.segmented_control(key="donde_regla").set_value("plan").run()
assert (card()[4], card()[2]) == ("130 €", "87 €"), card()  # Plan: 60 % of 650 / 3 each; each pays 217 - 130
ok(at, "dónde me llega: con el Plan, compartiendo entre 3")
at.number_input(key="donde_ingresos").set_value(30000).run()
at.segmented_control(key="donde_regla").set_value("hoy").run()
assert at.error and "límite de ingresos" in at.error[0].value, [e.value for e in at.error]
ok(at, "dónde me llega: 30.000 € no cumple el límite de hoy (25.200 €)")
at.segmented_control(key="donde_como").set_value("Solo o sola").run()
at.number_input(key="donde_ingresos").set_value(18000).run()
districts = lambda: next(m.value for m in at.markdown if "distritos**" in m.value)  # noqa: E731
assert "**11 de los 21 distritos**, desde el 26 % de Chamberí hasta el 88 % de Puente de Vallecas" in districts(), \
    districts()
at.selectbox(key="donde_municipio").select("Madrid · Puente de Vallecas").run()
# SERPAVI 2024 median 700 EUR, Madrid's cap of 900 EUR: you pay 700 - 250, 30 % of 1,500 EUR a month
assert card() == ["88 %", "700 €", "450 €", "900 €", "250 €", "30 %"], card()
ok(at, "dónde me llega: Madrid, distrito de Puente de Vallecas")
at.segmented_control(key="donde_regla").set_value("plan").run()
assert "**14 de los 21 distritos**, desde el 35 % de Chamberí hasta el 95 % de Puente de Vallecas" in districts(), \
    districts()
ok(at, "dónde me llega: los distritos de Madrid con el tope del Plan (1.000 €)")
at.segmented_control(key="donde_regla").set_value("hoy").run()
at.button(key="donde_ir").click().run()
assert (at.selectbox(key="calc_municipio").value, at.number_input(key="calc_precio").value) == ("Madrid", 700)
assert [m.value for m in at.metric][:2] == ["250 €", "6.000 €"], [m.value for m in at.metric]
ok(at, "dónde me llega -> calculadora con Madrid y 700 €")

at.switch_page("app_pages/ficha.py").run()
ok(at, "ficha: Parla")
for name in ["Madrid", "Majadahonda", "Acebeda (La)"]:  # Acebeda: 7 young people and no SERPAVI rents
    at.selectbox(key="municipio").select(name).run()
    ok(at, f"ficha: {name}")
# the base of the art. 135 study, in each of its three cases (resultados/estudio_art135.csv)
for name, says in [("Hoyo de Manzanares", "lo justifica: el alquiler mediano del SERPAVI subió un 24,7 %"),
                   ("Rascafría", "no lo justifica: el alquiler mediano del SERPAVI subió un 14,3 %"),
                   ("Garganta de los Montes", "faltan datos")]:
    at.selectbox(key="municipio").select(name).run()
    boxes = [b.value for b in [*at.success, *at.info]]
    assert any(says in b for b in boxes), boxes
    ok(at, f"ficha: {name}, art. 135")

at.switch_page("app_pages/simular.py").run()  # opens with the proposal and the Plan's aid, as on the cover
assert "recibe 4,3 ayudas por cada 1.000 jóvenes** (hoy, 3,7)" in at.info[0].value, at.info[0].value  # plan_amount
assert at.metric[4].value == "40,3 M€", at.metric[4].value  # simulador_reparto.json, plan_amount
ok(at, "simulador: propuesta con la cuantía del Plan")
assert [m.value for m in at.metric][5:] == ["63 pueblos", "46 de 63", "40.681"], [m.value for m in at.metric][5:]
assert "40,3 M€" in at.caption[-2].value, at.caption[-2].value  # estudio_art135.json, sensitivity (last: the footer)
ok(at, "simulador: la base del estudio del art. 135")
at.segmented_control(key="mas_gente").set_value("Y todos los que entran nuevos").run()
assert at.metric[4].value == "58,1 M€", at.metric[4].value  # plan_income_limit, p_1
ok(at, "simulador: propuesta con el Plan y todos los que entran nuevos por su límite de ingresos")
at.segmented_control(key="mas_gente").set_value("Los mismos que en 2022").run()
at.segmented_control(key="cuantia").set_value("250 € (hoy)").run()
assert "recibe 5,4 ayudas por cada 1.000 jóvenes** (hoy, 3,7)" in at.info[0].value, at.info[0].value  # PLAN, 7-nov
ok(at, "simulador: propuesta con los 250 € de hoy")
at.segmented_control(key="tope").set_value("Hoy (600 / 900 €)").run()
at.segmented_control(key="reparto").set_value("Orden de llegada (hoy)").run()
assert {m.delta for m in at.metric[:5]} <= {"0", "0,0", "0,0 puntos", "0,0 M€"}, [m.delta for m in at.metric]
ok(at, "simulador: la regla de hoy no cambia nada")
at.segmented_control(key="tope").set_value("Un tope único").run()
at.slider(key="tope_unico").set_value(1200).run()
at.segmented_control(key="beta").set_value("Sin efecto (0)").run()
at.slider(key="presupuesto").set_value(10.0).run()
ok(at, "simulador: tope único de 1.200 €, sin efecto, 10 M€")

at.switch_page("app_pages/metodo.py").run()
ok(at, "método y datos")

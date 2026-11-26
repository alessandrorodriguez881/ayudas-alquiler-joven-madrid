"""App of the project: map, eligibility calculator, municipality card, allocation simulator and method.
Run:  streamlit run app/streamlit_app.py"""
import pathlib

import streamlit as st

st.set_page_config(page_title="Los invisibles del Bono", page_icon=":material/home_work:", layout="wide")
# the project's mark, left of the menu on every page: a house with a dashed young person inside, «the invisible ones»
st.logo(str(pathlib.Path(__file__).resolve().parent / "logo.svg"), size="large")
# 26-nov, a more modern look (visual only: no text, figure, order or colour of the content changes). Cards are the
# containers with a key that starts «card_» (st-key-card_… classes); «hero» is the header of the home page. Inside the
# same <style> as the rest, so it takes no room at the top of the pages (the demo blocks stay where they were)
MODERN_CSS = (
    " h1 {letter-spacing: -0.025em;} h2, h3 {letter-spacing: -0.015em;}"
    # the header of the home page: a blue band with the title in white and the project's name as a chip
    " .st-key-hero {background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 55%, #3b82f6 100%); border-radius: 22px;"
    " padding: 1.4rem 2rem 1.3rem; box-shadow: 0 22px 44px -24px rgba(30, 58, 138, .65); position: relative;"
    " overflow: hidden;}"
    " @media (max-width: 639px) {.st-key-hero {padding: 1.1rem 1.1rem 1rem; border-radius: 18px;}}"
    " .st-key-hero::after {content: ''; position: absolute; right: -80px; top: -90px; width: 320px; height: 320px;"
    " border-radius: 50%; background: radial-gradient(circle, rgba(255, 255, 255, .20), rgba(255, 255, 255, 0) 68%);"
    " pointer-events: none;}"
    " .st-key-hero h1, .st-key-hero h1 * {color: #ffffff !important;}"
    " .st-key-hero [data-testid='stHeaderActionElements'] {display: none;}"
    " .st-key-hero [data-testid='stCaptionContainer'], .st-key-hero [data-testid='stCaptionContainer'] * "
    "{color: rgba(255, 255, 255, .92) !important;}"
    " .st-key-hero [data-testid='stCaptionContainer'] {max-width: 64rem;}"
    " .st-key-hero [data-testid='stElementContainer']:first-child [data-testid='stCaptionContainer'] "
    "{display: inline-block; width: auto; background: rgba(255, 255, 255, .14); border: 1px solid rgba(255, 255, 255, .32);"
    " border-radius: 999px; padding: .1rem .85rem;}"
    # cards: a soft shadow; the figure cards of the home page and the three rules of the calculator rise on hover, with
    # a top stripe in the colour of their bar (blue today, orange the Plan, green the proposal, as in the chart)
    " [class*='st-key-card_'] {box-shadow: 0 1px 2px rgba(16, 24, 40, .05), 0 8px 24px -12px rgba(16, 24, 40, .18);}"
    " [class*='st-key-card_kpi'], [class*='st-key-card_regla'] {transition: transform .18s ease, box-shadow .18s ease;}"
    " [class*='st-key-card_kpi']:hover, [class*='st-key-card_regla']:hover {transform: translateY(-3px);"
    " box-shadow: 0 2px 4px rgba(16, 24, 40, .06), 0 18px 36px -14px rgba(37, 106, 191, .45);}"
    " .st-key-card_kpi_0 {border-top: 4px solid #2563eb !important;}"
    " .st-key-card_kpi_1 {border-top: 4px solid #ea580c !important;}"
    " .st-key-card_kpi_2 {border-top: 4px solid #16a34a !important;}"
    " .st-key-card_kpi_0 [data-testid='stMetricValue'] {color: #1d4ed8;}"
    " .st-key-card_kpi_1 [data-testid='stMetricValue'] {color: #c2410c;}"
    " .st-key-card_kpi_2 [data-testid='stMetricValue'] {color: #15803d;}"
    # index bars (app_pages/mapa.py, bars()): a label, its figure and a rounded bar in the colour of its rule
    " .ix {display: flex; flex-direction: column; gap: .3rem; margin: .15rem 0 .1rem;}"
    " .ix-head {display: flex; justify-content: space-between; gap: .75rem; font-size: .8rem; line-height: 1.25;}"
    " .ix-lab {opacity: .8;} .ix-val {font-weight: 700; font-variant-numeric: tabular-nums;}"
    " .ix-track {height: 8px; border-radius: 999px; background: rgba(128, 128, 128, .17); overflow: hidden;"
    " margin-bottom: .2rem;}"
    " .ix-fill {height: 100%; border-radius: 999px;}"
    " .ix-chip {display: inline-block; font-size: .72rem; font-weight: 700; letter-spacing: .02em; padding: .05rem .55rem;"
    " border-radius: 999px; color: #ffffff; vertical-align: middle;}"
    # chips under the text of the hero
    " .hero-chips {display: flex; flex-wrap: wrap; gap: .5rem;}"
    " .hero-chip {font-size: .8rem; font-weight: 600; color: #ffffff; background: rgba(255, 255, 255, .14);"
    " border: 1px solid rgba(255, 255, 255, .3); border-radius: 999px; padding: .2rem .8rem;}"
    " .hero-chip::before {content: ''; display: inline-block; width: 7px; height: 7px; border-radius: 50%;"
    " background: #8fd3b6; margin-right: .45rem; vertical-align: middle;}"
    " [class*='st-key-card_regla_hoy'] {border-top: 4px solid #2563eb !important;}"
    " [class*='st-key-card_regla_plan'] {border-top: 4px solid #ea580c !important;}"
    " [class*='st-key-card_regla_propuesta'] {border-top: 4px solid #16a34a !important;}"
    # the rules the case meets: a green halo (calculator, key …_ok)
    " [class*='st-key-card_regla_hoy_ok'], [class*='st-key-card_regla_plan_ok'], [class*='st-key-card_regla_propuesta_ok']"
    " {box-shadow: 0 0 0 2px rgba(22, 163, 74, .45), 0 16px 32px -16px rgba(22, 163, 74, .6);"
    " background-image: linear-gradient(180deg, rgba(22, 163, 74, .08), rgba(22, 163, 74, 0) 40%);}"
    # the three scenarios under the answer of the calculator: ✔ or ✘ and the cap of each rule, in the colour of its bar
    " .sc-row {display: flex; flex-wrap: wrap; gap: .5rem;}"
    " .sc {display: inline-flex; align-items: center; gap: .45rem; padding: .3rem .8rem .3rem .4rem; border-radius: 999px;"
    " font-size: .9rem; font-weight: 600; border: 1.5px solid; line-height: 1.3;}"
    " .sc-mark {display: inline-flex; align-items: center; justify-content: center; width: 1.35rem; height: 1.35rem;"
    " border-radius: 50%; color: #ffffff; font-size: .8rem; font-weight: 800;}"
    " .sc-no .sc-mark {background: #dc2626;} .sc-si .sc-mark {background: #16a34a;}"
    " .sc-hoy {border-color: #93b4f5; background: #eff6ff; color: #1e3a8a;}"
    " .sc-plan {border-color: #f6b48a; background: #fff7ed; color: #9a3412;}"
    " .sc-propuesta {border-color: #86d3a3; background: #f0fdf4; color: #14532d;}"
    " .sc-si {box-shadow: 0 6px 16px -8px rgba(22, 163, 74, .7);}"
    " @media (max-width: 639px) {.sc {font-size: .8rem; padding: .2rem .6rem .2rem .3rem;}}"
    # Tu municipio: the diagnosis row (need, rents above the Plan's cap in orange, the proposal's cap in green)
    " .st-key-ficha_cifras [data-testid='stElementContainer']:nth-child(2) > [data-testid='stMetric']"
    " {border-left: 5px solid #ea580c;}"
    " .st-key-ficha_cifras [data-testid='stElementContainer']:nth-child(2) [data-testid='stMetricValue'] {color: #c2410c;}"
    " .st-key-ficha_cifras [data-testid='stElementContainer']:nth-child(3) > [data-testid='stMetric']"
    " {border-left: 5px solid #16a34a;}"
    " .st-key-ficha_cifras [data-testid='stElementContainer']:nth-child(3) [data-testid='stMetricValue'] {color: #15803d;}"
    " .st-key-ficha_cifras [data-testid='stElementContainer']:nth-child(4) > [data-testid='stMetric']"
    " {border-left: 5px solid #94a3b8;}"
    # Inicio: the two ways in (young people, administration)
    " .st-key-ruta_jovenes, .st-key-ruta_admin {border-left: 6px solid #2563eb !important; padding: 1.25rem 1.4rem;"
    " background-image: linear-gradient(135deg, rgba(37, 99, 235, .09), rgba(37, 99, 235, 0) 60%);"
    " box-shadow: 0 1px 2px rgba(16, 24, 40, .05), 0 12px 28px -14px rgba(30, 58, 138, .35);"
    " transition: transform .18s ease, box-shadow .18s ease;}"
    " .st-key-ruta_admin {border-left-color: #1e3a8a !important;"
    " background-image: linear-gradient(135deg, rgba(30, 58, 138, .10), rgba(30, 58, 138, 0) 60%);}"
    " .st-key-ruta_jovenes:hover, .st-key-ruta_admin:hover {transform: translateY(-3px);"
    " box-shadow: 0 2px 4px rgba(16, 24, 40, .06), 0 20px 40px -16px rgba(30, 58, 138, .45);}"
    " .st-key-ruta_jovenes h4, .st-key-ruta_admin h4 {padding-top: 0;}"
    " [class*='st-key-card_kpi'] [data-testid='stMetricValue'] {letter-spacing: -0.02em;}"
    # the figures in a row of their own (Tu municipio, Simulador): the same soft shadow and rise
    " [data-testid='stHorizontalBlock'] > [data-testid='stElementContainer'] > [data-testid='stMetric'],"
    " [direction='row'] > [data-testid='stElementContainer'] > [data-testid='stMetric'] "
    "{box-shadow: 0 1px 2px rgba(16, 24, 40, .05), 0 8px 24px -14px rgba(16, 24, 40, .18);"
    " transition: transform .18s ease, box-shadow .18s ease;}"
    " [data-testid='stHorizontalBlock'] > [data-testid='stElementContainer'] > [data-testid='stMetric']:hover,"
    " [direction='row'] > [data-testid='stElementContainer'] > [data-testid='stMetric']:hover "
    "{transform: translateY(-2px); box-shadow: 0 2px 4px rgba(16, 24, 40, .06), 0 16px 30px -14px rgba(37, 106, 191, .4);}"
    # buttons: a soft lift on hover, and the main ones with a blue glow
    " [data-testid^='stBaseButton'] {transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;}"
    " [data-testid='stBaseButton-primary'] {box-shadow: 0 6px 16px -8px rgba(37, 106, 191, .75);}"
    " [data-testid^='stBaseButton']:hover {transform: translateY(-1px);}"
    " [data-testid='stBaseButton-primary']:hover {filter: brightness(1.06);"
    " box-shadow: 0 10px 22px -10px rgba(37, 106, 191, .85);}"
    # a thin line under the menu, and dividers that fade at the ends
    " [data-testid='stHeader'] {box-shadow: 0 1px 0 rgba(16, 24, 40, .07);}"
    " [data-testid='stMain'] hr {border: none; height: 1px;"
    " background: linear-gradient(90deg, rgba(37, 106, 191, 0), rgba(37, 106, 191, .45), rgba(37, 106, 191, 0));}"
)
# the big figures shrink a little between a phone and a wide screen, and the labels go down a line instead of being
# cut: at 1,024 px and below, «7.200 €» came out as «7.2…» and «Alquileres dentro del tope» as «Alquileres dentro d…»
st.html("<style>@media (min-width: 640px) and (max-width: 1399px) {[data-testid='stMetricValue'], "
        "[data-testid='stMetricValue'] * {font-size: clamp(1.15rem, 2.4vw, 2.25rem);}} "
        "[data-testid='stMetricLabel'] [data-testid='stMarkdownContainer'], [data-testid='stMetricLabel'] p "
        "{white-space: normal; overflow: visible; text-overflow: clip;} "
        # the menu: from 640 to 1,399 px without the small icons and with less padding, so the 7 pages fit in one line;
        # at 1,024 px two of them hid behind an English «2 more», and at 1,366 px «¿Cómo se aplica?» was cut (17-nov)
        "@media (min-width: 640px) and (max-width: 1399px) {[data-testid='stTopNavLink'] > span:first-child "
        "{display: none;} [data-testid='stTopNavLink'] {gap: 0; padding: 0 4px;}} "
        # and only the house of the logo (its 240 px with the name left room for 5 pages: at 1,024 px «¿Cómo se aplica?»
        # and «Método y datos» went behind «2 more» again on the published app; with the house alone the 7 fit, 24-nov)
        "@media (min-width: 640px) and (max-width: 1399px) {[data-testid='stHeaderLogo'] {width: 32px !important; "
        "max-width: 32px !important; object-fit: cover; object-position: left center;}} "
        # on a phone, a wide table (the 9 columns of «¿Cómo se aplica?») scrolls inside its own box instead of moving the
        # whole page sideways: at 375 px it was 739 px wide and the page scrolled (20-nov)
        "@media (max-width: 639px) {[data-testid='stMarkdownContainer'] table {display: block; overflow-x: auto;}}"
        + MODERN_CSS + "</style>")

page = st.navigation(
    [
        st.Page("app_pages/mapa.py", title="Inicio", icon=":material/home:", default=True),
        st.Page("app_pages/calculadora.py", title="¿Puedo pedirla?", icon=":material/checklist:"),
        st.Page("app_pages/donde.py", title="¿Dónde me llega?", icon=":material/explore:"),
        st.Page("app_pages/ficha.py", title="Tu municipio", icon=":material/location_city:"),
        st.Page("app_pages/simular.py", title="Simulador", icon=":material/tune:"),
        st.Page("app_pages/aplicar.py", title="¿Cómo se aplica?", icon=":material/gavel:"),
        st.Page("app_pages/metodo.py", title="Método y datos", icon=":material/fact_check:"),
    ],
    position="top",
)
page.run()
st.caption("Herramienta independiente hecha para DataMad 2026 con datos abiertos. **No es una herramienta oficial** de la "
           "Comunidad de Madrid ni del Ministerio de Vivienda: para pedir la ayuda, la convocatoria oficial es la que vale. "
           "Código, datos y método, abiertos (MIT): "
           "[github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid]"
           "(https://github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid).")

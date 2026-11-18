"""App of the project: map, eligibility calculator, municipality card, allocation simulator and method.
Run:  streamlit run app/streamlit_app.py"""
import pathlib

import streamlit as st

st.set_page_config(page_title="Los invisibles del Bono", page_icon=":material/home_work:", layout="wide")
# the project's mark, left of the menu on every page: a house with a dashed young person inside, «the invisible ones»
st.logo(str(pathlib.Path(__file__).resolve().parent / "logo.svg"), size="large")
# the big figures shrink a little between a phone and a wide screen, and the labels go down a line instead of being
# cut: at 1,024 px and below, «7.200 €» came out as «7.2…» and «Alquileres dentro del tope» as «Alquileres dentro d…»
st.html("<style>@media (min-width: 640px) and (max-width: 1399px) {[data-testid='stMetricValue'], "
        "[data-testid='stMetricValue'] * {font-size: clamp(1.15rem, 2.4vw, 2.25rem);}} "
        "[data-testid='stMetricLabel'] [data-testid='stMarkdownContainer'], [data-testid='stMetricLabel'] p "
        "{white-space: normal; overflow: visible; text-overflow: clip;}</style>")

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

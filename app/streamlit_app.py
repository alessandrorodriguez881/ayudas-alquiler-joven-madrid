"""App of the project: map, eligibility calculator, municipality card, allocation simulator and method.
Run:  streamlit run app/streamlit_app.py"""
import streamlit as st

st.set_page_config(page_title="El tope del Bono Alquiler Joven", page_icon=":material/home_work:", layout="wide")

page = st.navigation(
    [
        st.Page("app_pages/mapa.py", title="Mapa", icon=":material/map:", default=True),
        st.Page("app_pages/calculadora.py", title="¿Puedo pedirla?", icon=":material/checklist:"),
        st.Page("app_pages/ficha.py", title="Tu municipio", icon=":material/location_city:"),
        st.Page("app_pages/simular.py", title="Simulador", icon=":material/tune:"),
        st.Page("app_pages/metodo.py", title="Método y datos", icon=":material/fact_check:"),
    ],
    position="top",
)
page.run()
st.caption("Herramienta independiente hecha para DataMad 2026 con datos abiertos. **No es una herramienta oficial** de la "
           "Comunidad de Madrid ni del Ministerio de Vivienda: para pedir la ayuda, la convocatoria oficial es la que vale.")

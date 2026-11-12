"""How the proposal would work in a real call (RD 326/2026, art. 138): 4 bolsas, who loses and what it does not solve.
The text is data/COMO_SE_APLICA.md, written by scripts/como_se_aplica.py with the repository's figures, so the page, that
file and resultados/como_se_aplica.json always say the same."""
import re

import streamlit as st

from datos import ROOT, es, result

o = result("como_se_aplica")
ch, w = o["change_vs_plan_pct"]["bolsas"], o["who_loses_vs_plan"]
signed = lambda x: ("−" if x < 0 else "+") + es(abs(x))  # noqa: E731

st.title("¿Cómo se aplica?")
st.caption("Para la Consejería: la propuesta en una convocatoria abierta todo el año, como pide el Plan Estatal "
           "2026-2030 (art. 138), con el mismo dinero, y quién pierde. Es una propuesta de diseño, no un informe "
           "jurídico: decidirlo y comprobar que encaja en la norma les toca a la Comunidad y a sus servicios jurídicos.")
KPIS = [("Tercio con más necesidad", f"{signed(ch['resto, necesidad alta'])} %",
         "ayudas por cada 1.000 jóvenes, frente al Plan tal cual"),
        ("Madrid capital", f"{signed(ch['Madrid capital'])} %",
         f"{es(-w['aids_delta_by_group']['Madrid capital'])} ayudas menos que con el Plan tal cual"),
        ("Municipios que pierden", f"{w['municipalities_losing']} de {o['municipalities']}",
         "reciben menos ayudas que con el Plan tal cual")]
for col, (label, value, note) in zip(st.columns(3), KPIS):
    with col.container(border=True, height="stretch"):
        st.metric(label, value)
        st.caption(note)

text = (ROOT / "data" / "COMO_SE_APLICA.md").read_text(encoding="utf-8")
body = "\n### " + text.split("\n## ", 1)[1].replace("\n## ", "\n### ")  # the title and the line about the script are for the repository
body = body.replace("[ESTUDIO_ART135.md](ESTUDIO_ART135.md)", "la página «Simulador» y en `data/ESTUDIO_ART135.md`")
st.markdown(re.sub(r"\[([^\]]+)\]\((?!https?://)[^)]+\)", r"\1", body))  # links inside the repository do not work here

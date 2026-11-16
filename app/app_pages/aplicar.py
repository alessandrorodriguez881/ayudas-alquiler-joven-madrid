"""How the proposal would work in a real call (RD 326/2026, art. 138): 4 bolsas, who loses and what it does not solve.
The text is data/COMO_SE_APLICA.md, written by scripts/como_se_aplica.py with the repository's figures, so the page, that
file and resultados/como_se_aplica.json always say the same."""
import re

import altair as alt
import pandas as pd
import streamlit as st

from datos import ROOT, SLOT2, SLOT3, es, result

o = result("como_se_aplica")
ch, w = o["change_vs_plan_pct"]["bolsas"], o["who_loses_vs_plan"]
signed = lambda x: ("−" if x < 0 else "+") + es(abs(x))  # noqa: E731

st.title("¿Cómo se aplica?")
st.caption("Para la Consejería: la propuesta en una convocatoria abierta todo el año, como pide el Plan Estatal "
           "2026-2030 (art. 138), con el mismo dinero, y quién pierde. Es una propuesta de diseño, no un informe "
           "jurídico: decidirlo y comprobar que encaja en la norma les toca a la Comunidad y a sus servicios jurídicos.")
KPIS = [("Municipios con más necesidad", f"{signed(ch['resto, necesidad alta'])} %",
         "fuera de Madrid capital (los que suman un tercio de sus jóvenes): ayudas por cada 1.000 jóvenes, frente al "
         "Plan tal cual"),
        ("Madrid capital", f"{signed(ch['Madrid capital'])} %",
         f"{es(-w['aids_delta_by_group']['Madrid capital'])} ayudas menos que con el Plan tal cual"),
        ("Municipios que pierden", f"{w['municipalities_losing']} de {o['municipalities']}",
         "reciben menos ayudas que con el Plan tal cual")]
for col, (label, value, note) in zip(st.columns(3), KPIS):
    with col.container(border=True, height="stretch"):
        st.metric(label, value)
        st.caption(note)

# Improvement 1 of the mid-term jury (15-nov), with his yes (16-nov): inside Madrid city, its bolsa shared out by the need
# of its districts. Calculated after seeing the pre-registered result (scripts/distritos_cifra3.py, D_added_after_results)
dist = result("distritos_cifra3")
after = dist["D_added_after_results"]
sign1 = lambda x: ("+" if x > 0 else "−") + es(abs(x), 1)  # noqa: E731
LABEL = {"necesidad alta": "Más necesidad", "necesidad media": "Necesidad media", "necesidad baja": "Menos necesidad"}
rows = pd.DataFrame([{"grupo": LABEL[k], "cambio": v["change_vs_A_pct"], "distritos": ", ".join(v["districts"])}
                     for k, v in after["madrid_subthirds"].items()])
rows["etiqueta"] = [sign1(c) + " %" for c in rows["cambio"]]
ink = "#e6edf6" if st.context.theme.type == "dark" else "#18212f"  # the theme's text colour (.streamlit/config.toml)
st.subheader("Y dentro de Madrid capital, por distritos")
left, right = st.columns([3, 2], gap="large", vertical_alignment="center")
with left:
    y_group = alt.Y("grupo:N", sort=list(rows["grupo"]), title=None, axis=alt.Axis(labelLimit=260, labelFontSize=13))
    x_change = alt.X("cambio:Q", title="Ayudas por joven frente al Plan tal cual (%)",
                     scale=alt.Scale(domain=[min(rows["cambio"].min(), 0) - 9, max(rows["cambio"].max(), 0) + 9]),
                     axis=alt.Axis(labelExpr="replace(datum.label, '.', ',')"))
    bars = alt.Chart(rows).mark_bar(cornerRadiusEnd=4, size=26).encode(
        x=x_change, y=y_group, color=alt.condition("datum.cambio > 0", alt.value(SLOT3), alt.value(SLOT2)),
        tooltip=[alt.Tooltip("grupo:N", title="Grupo"), alt.Tooltip("distritos:N", title="Distritos"),
                 alt.Tooltip("etiqueta:N", title="Frente al Plan tal cual")])
    up = alt.Chart(rows).transform_filter("datum.cambio > 0").mark_text(
        align="left", dx=6, fontSize=13, fontWeight="bold", color=ink).encode(x="cambio:Q", y=y_group, text="etiqueta:N")
    down = alt.Chart(rows).transform_filter("datum.cambio <= 0").mark_text(
        align="right", dx=-6, fontSize=13, fontWeight="bold", color=ink).encode(x="cambio:Q", y=y_group, text="etiqueta:N")
    # left padding: Vega measures the labels before the Inter font loads, and without it they come out cut
    st.altair_chart((bars + up + down).properties(height=alt.Step(46), padding={"left": 24, "top": 4, "right": 4, "bottom": 4},
                                                  title=alt.TitleParams(
                        "Distritos de Madrid, por su necesidad", anchor="start", fontSize=15)),
                    alt="Ayudas por joven frente al Plan tal cual en los distritos de Madrid capital, con su bolsa repartida "
                        "por la necesidad de sus distritos: " + "; ".join(f"{g}, {e}" for g, e in zip(rows["grupo"],
                                                                                                       rows["etiqueta"])))
with right:
    hi, lo = after["madrid_subthirds"]["necesidad alta"], after["madrid_subthirds"]["necesidad baja"]
    st.info((f"Si la bolsa de Madrid capital se reparte en 3 subbolsas según la necesidad de sus distritos, los que más la "
            f"necesitan ({', '.join(hi['districts'])}) reciben un {sign1(hi['change_vs_A_pct'])} % de ayudas por joven "
            f"frente al Plan tal cual, en vez de perder; los que menos, un {sign1(lo['change_vs_A_pct'])} %. Fuera de "
            "Madrid capital, el +41 % se mantiene "
            f"({sign1(after['outside_madrid_by_third_change_vs_A_pct']['resto, necesidad alta'])} %). Lo calculamos "
            "después de ver el resultado preregistrado (con Madrid por distritos, el tercio con más necesidad gana un "
            f"{sign1(dist['by_third']['necesidad alta']['change_C_3_bolsas_vs_A_pct'])} %), y las solicitudes por "
            "distrito no existen: son las de Madrid repartidas con nuestro modelo.").replace(" %", " %"),  # «+41 %» in one line
            title="Calculado después de verlo", icon=":material/science:")

text = (ROOT / "data" / "COMO_SE_APLICA.md").read_text(encoding="utf-8")
body = "\n### " + text.split("\n## ", 1)[1].replace("\n## ", "\n### ")  # the title and the line about the script are for the repository
body = body.replace("[ESTUDIO_ART135.md](ESTUDIO_ART135.md)", "la página «Simulador» y en `data/ESTUDIO_ART135.md`")
st.markdown(re.sub(r"\[([^\]]+)\]\((?!https?://)[^)]+\)", r"\1", body))  # links inside the repository do not work here

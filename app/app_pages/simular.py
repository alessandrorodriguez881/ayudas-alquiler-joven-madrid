import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import simulador
from datos import SLOT1, SLOT2, es, pct, result, simulation_base

st.title("¿Y si el tope fuera otro?")
st.caption("Con un presupuesto fijo, subir el tope trae más solicitudes, no más bonos: lo que cambia es dónde van. "
           "Elige el tope, cómo se reparte y cuánto frena el tope, y compáralo con la regla de hoy (5.300 bonos, 31,8 M€, "
           "por orden de llegada).")

s, _ = simulation_base()
rules = simulador.rules(s)
cap_only = result("exploratorio_topes_falsos")["real_cap_and_uniform_900"]["real_cap"]["beta"]
BETAS = {f"Central ({es(cap_only, 2)})": cap_only,
         f"Contraste ({es(result('contraste_real')['H1']['beta'], 2)})": result("contraste_real")["H1"]["beta"],
         "Sin efecto (0)": 0.0}
CAPS = {"Hoy (600 / 900 €)": s["tope_2024"].to_numpy(float), "Plan 2026-2030": rules["plan_estatal"][0],
        "Plan o alquiler local (máx. 1.000 €)": rules["plan_p75_hasta_1000"][0], "Un tope único": None}
ALLOC = {"Orden de llegada (hoy)": "llegada", "Cupos: jóvenes × necesidad": ("necesidad", 1),
         "Cupos: jóvenes × necesidad × límite de ingresos": ("necesidad", 1, "requisito")}
AID = {"250 € (hoy)": "hoy", "La del Plan: hasta 300 €, sin pasar del 60 % del alquiler": "plan"}
MORE = {"Los mismos que en 2022": 0, "Y la mitad de los que entran nuevos": 0.5, "Y todos los que entran nuevos": 1}
let_in = result("simulador_reparto")["plan_income_limit"]["returns_let_in_vs_3iprem_weighted_by_young"]

with st.container(border=True):
    with st.container(horizontal=True, vertical_alignment="bottom"):
        cap_name = st.segmented_control("Tope del piso", list(CAPS), default="Plan o alquiler local (máx. 1.000 €)",
                                        key="tope") or "Hoy (600 / 900 €)"
        if cap_name == "Un tope único":
            single = st.slider("Tope único (€ al mes)", 400, 1500, 900, step=50, key="tope_unico", width=280)
    alloc_name = st.segmented_control("Cómo se reparten los bonos", list(ALLOC),
                                      default="Cupos: jóvenes × necesidad × límite de ingresos", key="reparto") or "Orden de llegada (hoy)"
    aid_name = st.segmented_control(
        "Cuánto da cada ayuda al mes", list(AID), default="250 € (hoy)", key="cuantia",
        help="Plan 2026-2030, art. 137: hasta 300 € al mes (habitación, 200 €) y nunca más del 60 % del alquiler. Aquí, "
             "con el alquiler mediano de 2024 del municipio, o el tope si el mediano pasa del tope.") or "250 € (hoy)"
    plan_rules = AID[aid_name] == "plan"
    more_name = st.segmented_control(
        "Con el límite de ingresos del Plan, quién la pide", list(MORE), default="Los mismos que en 2022",
        key="mas_gente", disabled=not plan_rules,
        help=f"El Plan deja pedirla con ingresos de hasta 5 × IPREM de la persona (42.000 € al año); hoy, 3 × IPREM del "
             f"hogar (25.200 €). En las declaraciones del IRPF, eso deja entrar a {es(let_in, 2)} veces más gente de "
             f"media, y más donde la renta es alta. «Todos» es el caso alto: los que entran nuevos ganan más y la "
             f"necesitan menos. Solo con la cuantía del Plan.") or "Los mismos que en 2022"
    left, right = st.columns(2, gap="large", vertical_alignment="bottom")
    with left:
        beta_name = st.segmented_control(
            "Cuánto frena el tope", list(BETAS), default=list(BETAS)[0], key="beta",
            help="Central: solo la parte del efecto que se debe al tope (análisis exploratorio). Contraste: el efecto "
                 "del contraste preregistrado, que también recoge que el alquiler caro frena. Sin efecto: el tope no "
                 "cambia cuánta gente pide.") or list(BETAS)[0]
    with right:
        budget = st.slider("Presupuesto (M€)", 10.0, 60.0, simulador.BUDGET_EUR / 1e6, step=0.1, key="presupuesto",
                           format="%.1f M€")

beta = BETAS[beta_name]
caps = CAPS[cap_name] if cap_name != "Un tope único" else np.full(len(s), float(single))
how = ALLOC[alloc_name]
req, sh = simulador.requests(s, caps, beta)
if plan_rules:  # the Plan's rules: its aid, its income limit in the quotas and, if chosen, more people asking
    req = req * simulador.more_eligible(s, MORE[more_name])
    aid = simulador.plan_aid(s, caps)
    weights = req if how == "llegada" else simulador.need_weights(s, how, simulador.PLAN_INCOME)
else:
    aid = np.full(len(s), simulador.BONO_EUR / 24)
    weights = req if how == "llegada" else simulador.need_weights(s, how)
bonos = simulador.allocate_money(req, weights, budget * 1e6, aid)
req0, sh0 = simulador.requests(s, s["tope_2024"].to_numpy(float), beta)
bonos0 = simulador.allocate(req0, req0, simulador.BUDGET_EUR / simulador.BONO_EUR)

young = s["jovenes_20_34_2024"].to_numpy(float)
madrid = (s["ine"] == simulador.MADRID).to_numpy()
small = (s["pob_total_2024"] <= 10000).to_numpy()
# money that gives today's share of requests an aid (31.8 M EUR for 5,300 bonos), with this rule's cost per aid
same_chance = bonos0.sum() / req0.sum() * (req * 24 * aid).sum() / 1e6
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Solicitudes esperadas", es(req.sum()), delta=es(req.sum() - req0.sum()), delta_color="off", border=True,
          height="stretch")
m2.metric("Solicitudes por bono", es(req.sum() / bonos.sum(), 1), delta=es(req.sum() / bonos.sum() - req0.sum() / bonos0.sum(), 1),
          delta_color="inverse", border=True, height="stretch")
m3.metric("Alquiler por encima del tope", pct(np.average(sh, weights=young)),
          delta=es(100 * (np.average(sh, weights=young) - np.average(sh0, weights=young)), 1) + " puntos",
          delta_color="inverse", border=True, height="stretch", help="Alquileres de 2024 (SERPAVI), pesando por jóvenes.")
m4.metric("Ídem, municipios de 10.000 hab. o menos", pct(np.average(sh[small], weights=young[small])),
          delta=es(100 * (np.average(sh[small], weights=young[small]) - np.average(sh0[small], weights=young[small])), 1)
          + " puntos", delta_color="inverse", border=True, height="stretch")
m5.metric("Dinero para la misma probabilidad que hoy", es(same_chance, 1) + " M€",
          delta=es(same_chance - simulador.BUDGET_EUR / 1e6, 1) + " M€", delta_color="inverse", border=True,
          height="stretch", help="Presupuesto que mantendría las solicitudes por bono de hoy (31,8 M€ para 5.300 bonos).")
st.caption(f"Con {es(budget, 1)} M€ y esta cuantía salen {es(bonos.sum())} ayudas de {es(np.average(aid, weights=req))} € "
           f"al mes de media durante 2 años (hoy, 5.300 de 250 €). De cada 100 que la piden, la consiguen unos "
           f"{es(100 * bonos.sum() / req.sum())} (hoy, unos {es(100 * bonos0.sum() / req0.sum())})."
           + (" Con las reglas del Plan, los cupos «× límite de ingresos» usan el suyo (5 × IPREM de la persona), y las "
              "solicitudes son las de 2022 más las de quienes entran nuevos, según el control de arriba (exploratorio: "
              "sale de las declaraciones del IRPF de todas las edades)." if plan_rules else ""))

groups = s["grupo_necesidad"].to_numpy()
ORDER = ["Madrid capital", "resto, necesidad alta", "resto, necesidad media", "resto, necesidad baja"]
rows = []
for label, b in (("Hoy", bonos0), ("Tu regla", bonos)):
    for g in ORDER:
        k = groups == g
        rows.append({"grupo": g.capitalize(), "regla": label, "valor": 1000 * b[k].sum() / young[k].sum()})
# field names without dots: Vega-Lite reads "1.000" as a nested field
chart = (alt.Chart(pd.DataFrame(rows))
         .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
         .encode(x=alt.X("grupo:N", sort=[g.capitalize() for g in ORDER], title=None,
                         axis=alt.Axis(labelAngle=0, labelLimit=250)),
                 xOffset=alt.XOffset("regla:N", sort=["Hoy", "Tu regla"]),
                 y=alt.Y("valor:Q", title="Bonos por 1.000 jóvenes"),
                 color=alt.Color("regla:N", scale=alt.Scale(domain=["Hoy", "Tu regla"], range=[SLOT1, SLOT2]),
                                 legend=alt.Legend(orient="top", title=None)),
                 tooltip=[alt.Tooltip("grupo:N", title="Grupo"), alt.Tooltip("regla:N", title="Regla"),
                          alt.Tooltip("valor:Q", title="Bonos por 1.000 jóvenes", format=".1f")])
         .properties(height=320))
st.subheader("Bonos por cada 1.000 jóvenes, por grupo de necesidad")
st.altair_chart(chart, alt="Barras de bonos por cada 1.000 jóvenes por grupo de necesidad, hoy y con la regla elegida")
st.caption(f"Madrid capital tiene el {pct(young[madrid].sum() / young.sum())} de los jóvenes; con tu regla recibe el "
           f"{pct(bonos[madrid].sum() / bonos.sum())} de los bonos (hoy, el {pct(bonos0[madrid].sum() / bonos0.sum())}). "
           "El resto de la Comunidad va en tres tercios de jóvenes según el índice de necesidad.")

d = s[["municipio"]].assign(hoy=bonos0, regla=bonos, cambio=bonos - bonos0).sort_values("cambio")
cfg = {"municipio": "Municipio", "hoy": st.column_config.NumberColumn("Hoy", format="%.0f"),
       "regla": st.column_config.NumberColumn("Tu regla", format="%.0f"),
       "cambio": st.column_config.NumberColumn("Cambio", format="%+.0f")}
gain, lose = st.columns(2, gap="large")
with gain:
    st.subheader("Los que más ganan")
    st.dataframe(d.tail(8)[::-1], hide_index=True, column_config=cfg, alt="Municipios que más bonos ganan con la regla elegida")
with lose:
    st.subheader("Los que más pierden")
    st.dataframe(d.head(8), hide_index=True, column_config=cfg, alt="Municipios que más bonos pierden con la regla elegida")
st.download_button("Descargar el reparto por municipio (CSV)",
                   s[["ine", "municipio"]].assign(tope=caps, solicitudes=req.round(1), bonos=bonos.round(1),
                                                  bonos_hoy=bonos0.round(1)).to_csv(index=False).encode("utf-8"),
                   "reparto_simulado.csv", "text/csv", icon=":material/download:")
st.caption("Supuestos: las solicitudes por joven de 2022 cambian con exp(β × cambio de la parte del alquiler por encima "
           "del tope); los cupos nunca dan más bonos que solicitudes. Es una simulación con supuestos escritos en "
           "scripts/simulador.py, no una predicción.")

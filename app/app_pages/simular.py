import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import simulador
from datos import DB, RES, SLOT1, SLOT2, es, pct, result, simulation_base

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
    aid_name = st.segmented_control(  # opens with the Plan's aid: the same figures as the cover and the slides
        "Cuánto da cada ayuda al mes", list(AID), default=list(AID)[1], key="cuantia",
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
groups = s["grupo_necesidad"].to_numpy()
high = lambda b: 1000 * b[groups == "resto, necesidad alta"].sum() / young[groups == "resto, necesidad alta"].sum()  # noqa: E731
capital = lambda b: 1000 * b[madrid].sum() / young[madrid].sum()  # noqa: E731
st.info(f"**Con esta regla, los municipios con más necesidad fuera de Madrid capital (los que suman un tercio de sus "
        f"jóvenes) reciben {es(high(bonos), 1)} ayudas por cada 1.000 jóvenes** (hoy, {es(high(bonos0), 1)}); Madrid "
        f"capital, {es(capital(bonos), 1)} (hoy, {es(capital(bonos0), 1)}). De cada 100 que la piden, la consiguen unos "
        f"{es(100 * bonos.sum() / req.sum())} (hoy, unos {es(100 * bonos0.sum() / req0.sum())})."
        + (" Ojo: hoy cada ayuda es de 250 € y con el Plan, de hasta 300 €: para comparar ayuda con ayuda, elige "
           "«250 € (hoy)»." if plan_rules else ""),
        icon=":material/insights:")
with st.container(horizontal=True):  # wraps on a narrow screen instead of cutting «40,3 M€» (a laptop at 125 % zoom)
    st.metric("Solicitudes esperadas", es(req.sum()), delta=es(req.sum() - req0.sum()), delta_color="off", border=True,
              height="stretch")
    st.metric("Solicitudes por bono", es(req.sum() / bonos.sum(), 1),
              delta=es(req.sum() / bonos.sum() - req0.sum() / bonos0.sum(), 1), delta_color="inverse", border=True,
              height="stretch")
    st.metric("Alquiler por encima del tope", pct(np.average(sh, weights=young)),
              delta=es(100 * (np.average(sh, weights=young) - np.average(sh0, weights=young)), 1) + " puntos",
              delta_color="inverse", border=True, height="stretch",
              help="Alquileres de 2024 (SERPAVI), pesando por jóvenes.")
    st.metric("Ídem, en los pueblos", pct(np.average(sh[small], weights=young[small])),
              delta=es(100 * (np.average(sh[small], weights=young[small]) - np.average(sh0[small], weights=young[small])),
                       1) + " puntos", delta_color="inverse", border=True, height="stretch",
              help="Municipios de 10.000 habitantes o menos, donde el Plan pone el tope en 500 €.")
    st.metric("Dinero para igualar a hoy", es(same_chance, 1) + " M€",
              delta=es(same_chance - simulador.BUDGET_EUR / 1e6, 1) + " M€", delta_color="inverse", border=True,
              height="stretch",
              help="Presupuesto que mantendría las solicitudes por bono de hoy (31,8 M€ para 5.300 bonos).")
st.caption(f"Con {es(budget, 1)} M€ y esta cuantía salen {es(bonos.sum())} ayudas de {es(np.average(aid, weights=req))} € "
           f"al mes de media durante 2 años (hoy, 5.300 de 250 €)."
           + (" Con las reglas del Plan, los cupos «× límite de ingresos» usan el suyo (5 × IPREM de la persona), y las "
              "solicitudes son las de 2022 más las de quienes entran nuevos, según el control de arriba (exploratorio: "
              "sale de las declaraciones del IRPF de todas las edades)." if plan_rules else ""))

ORDER =["Madrid capital", "resto, necesidad alta", "resto, necesidad media", "resto, necesidad baja"]
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

# The legal path for the proposal's caps: scripts/estudio_art135.py
st.divider()
st.subheader("Para la Consejería: la base del estudio del art. 135")
study = result("estudio_art135")
up, cpi, sens, measure = (study["where_proposal_raises_cap"], study["cpi"], study["sensitivity"],
                          study["measure_check"])
st.caption("El Plan deja que la Comunidad suba el tope de 500 € si lo justifica con «estudios actualizados de oferta de "
           "vivienda» en alquiler (art. 135). Así que miramos, primero, qué parte del alquiler deja fuera el tope del Plan. "
           "El estudio puede apoyarse también en dos supuestos de la Ley de Vivienda (art. 18.3): a) que el alquiler pase "
           "del 30 % de la renta del hogar; b) que en cinco años haya subido al menos 3 puntos más que el IPC (en la "
           f"Comunidad de Madrid, un {es(cpi['rise_pct'], 1)} % de 2019 a 2024). Lo medimos en cada municipio donde la "
           "propuesta sube el tope.")
STUDY = [  # short label, value, what it means (in sight: metric labels are cut to one line on a phone)
    ("Sube el tope", f"{up['municipalities']} pueblos",  # «municipios» did not fit at 1,024 px
     "municipios pequeños: de 500 € a su percentil 75 del alquiler, como mucho 1.000 €"),
    ("Con base en los datos", f"{up['with_base']} de {up['municipalities']}",
     f"en {up['offer_case']}, el tope del Plan deja fuera más de la mitad del alquiler (la oferta); en otros "
     f"{up['only_18_3']}, el alquiler subió más del {es(cpi['threshold_b_pct'], 1)} % (supuesto b, con la mediana del "
     "SERPAVI). El a) no se cumple en ninguno"),
    ("Jóvenes que viven ahí", es(up["young_with_base"]), f"de 20 a 34 años, en esos {up['with_base']} municipios"),
]
for col, (label, value, note) in zip(st.columns(3), STUDY):
    with col.container(border=True, height="stretch"):
        st.metric(label, value)
        st.caption(note)
table = pd.read_csv(RES / "estudio_art135.csv", dtype={"ine": str})
table = table[table["sube_tope"]].assign(parte=lambda d: 100 * d["parte_por_encima_tope_plan"])
table["oferta"] = table["cumple_oferta"].map({True: "sí", False: "no", "True": "sí", "False": "no"}).fillna("—")
st.dataframe(table[["municipio", "jovenes_20_34_2024", "mediana_2024", "tope_propuesta", "parte", "oferta",
                    "subida_alquiler_pct", "justificacion"]], hide_index=True,
             column_config={"municipio": "Municipio",
                            "jovenes_20_34_2024": st.column_config.NumberColumn("Jóvenes", format="%d"),
                            "mediana_2024": st.column_config.NumberColumn("Alquiler mediano", format="%.0f €"),
                            "tope_propuesta": st.column_config.NumberColumn("Tope propuesto", format="%.0f €"),
                            "parte": st.column_config.ProgressColumn("Fuera con 500 €", format="%.0f %%", min_value=0,
                                                                     max_value=100),
                            "oferta": st.column_config.TextColumn("Más de la mitad fuera",
                                                                  help="La oferta, lo que pide el art. 135"),
                            "subida_alquiler_pct": st.column_config.NumberColumn("Subida 2019-2024", format="%.0f %%"),
                            "justificacion": st.column_config.TextColumn("Supuesto (Ley 12/2023)")},
             alt="Municipios pequeños donde la propuesta sube el tope, con el alquiler, la parte que queda fuera del tope "
                 "del Plan, la subida y el supuesto de la Ley 12/2023 que se cumple")
with st.container(horizontal=True):
    st.download_button("Descargar la tabla (CSV)", (RES / "estudio_art135.csv").read_bytes(), "estudio_art135.csv",
                       "text/csv", icon=":material/download:")
    st.download_button("Descargar el informe", (DB.parent / "ESTUDIO_ART135.md").read_bytes(), "estudio_art135.md",
                       "text/markdown", icon=":material/description:")
st.caption(f"Si el tope solo sube donde hay base, la propuesta da lo mismo: "
           f"{es(sens['proposal_only_where_justified']['aids_per_1000_young_high_need'], 1)} ayudas por cada 1.000 jóvenes "
           "en los municipios con más necesidad fuera de Madrid capital y "
           f"{es(sens['proposal_only_where_justified']['meur_same_chance_as_today'], 1)} M€ "
           "para la misma probabilidad que hoy. Ojo con la medida: en los "
           f"{measure['municipalities']} municipios grandes donde el portal tiene un índice de precios del alquiler, el "
           f"supuesto b) se cumple en {measure['case_b_met']['serpavi_median']} con la mediana del SERPAVI y en "
           + (f"{measure['case_b_met']['portal_index']}" if measure["case_b_met"]["portal_index"] else "ninguno")
           + " con el índice. Es una base con datos abiertos, no el estudio oficial: decidirlo, elegir la medida y "
           "acordarlo con el Ministerio le toca a la Comunidad. Método y límites en el informe (scripts/estudio_art135.py).")
st.page_link("app_pages/aplicar.py", label="¿Cómo se aplica en una convocatoria abierta todo el año? Las 4 bolsas y "
             "quién pierde", icon=":material/gavel:")

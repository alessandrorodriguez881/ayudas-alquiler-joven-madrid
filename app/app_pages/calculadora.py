"""Calculator: does one young person meet the requirements today, with the Plan 2026-2030 and with our proposal, and how
much would they get. All the rules live in scripts/reglas_bono.py, one function per article."""
import pandas as pd
import streamlit as st

from datos import es, municipalities, query, rb

RULE_IN_DB = {"hoy": "bono_2024", "plan": "plan_2026_2030", "propuesta": "propuesta"}
INCLUDES = {"vivienda": "Solo la vivienda", "garaje": "Vivienda y garaje", "trastero": "Vivienda y trastero",
            "garaje_trastero": "Vivienda, garaje y trastero"}
LIVING = {"solo": "Solo o sola", "jovenes": "Con otros jóvenes de hasta 35 años que también firman",
          "otros": "Con otras personas (familia, pareja que no firma, mayores de 35…)"}
DISABILITY = {"no": "No", "33": "Discapacidad del 33 % o más, o hijo o hija de víctima de violencia de género",
              "65": "Discapacidad del 65 % o más"}

t = municipalities().set_index("municipio")
options = sorted(t.index, key=str.lower)
# defaults through session state, not value=: «¿Dónde te llega?» fills these keys before switching to this page.
# It opens with the case of the pitch: 750 EUR in Hoyo de Manzanares (cap 600 EUR today, 500 with the Plan, 900 with ours)
for key, value in {"calc_municipio": "Hoyo de Manzanares", "calc_precio": 750, "calc_ingresos": 18000, "calc_tipo": "Piso entero",
                   "calc_n": 2}.items():
    st.session_state.setdefault(key, value)

st.title("¿Puedo pedir la ayuda al alquiler?")
st.caption("Te decimos si cumples los requisitos hoy, con el Plan 2026-2030 y con nuestra propuesta, y cuánto cobrarías. "
           "Es orientativo y no se guarda nada de lo que escribes.")  # short: on a phone the answer is right below

with st.container(border=True):
    st.subheader("Tu caso")
    a, b, c = st.columns(3)
    name = a.selectbox("Municipio", options, key="calc_municipio")
    age = b.number_input("Edad", min_value=14, max_value=60, value=27, key="calc_edad")
    kind = c.segmented_control("¿Qué alquilas?", ["Piso entero", "Habitación"], key="calc_tipo")
    kind = "habitacion" if kind == "Habitación" else "piso"

    a, b = st.columns(2)
    price = a.number_input("Precio al mes del contrato (€)", min_value=0, max_value=10000, step=10,
                           key="calc_precio", help="Si compartís piso y firmáis todos el contrato, el precio del piso entero.")
    income = b.number_input("Tus ingresos del último año declarado (€ al año)", min_value=0, max_value=1000000,
                            step=500, key="calc_ingresos",
                            help="Los del último año con la declaración de la renta ya cerrada: la Comunidad los mira en "
                                 "Hacienda.")

    # the five questions above decide most cases; the rest keeps its usual answer unless the visitor opens this
    with st.expander("Más detalles: con quién vives, garaje o trastero, otras situaciones", icon=":material/tune:"):
        living, sharers, others = "solo", 1, 0
        if kind == "piso":
            a, b = st.columns([2, 1])
            living = a.radio("¿Con quién vives?", list(LIVING), format_func=LIVING.get, key="calc_convivencia")
            if living == "jovenes":
                sharers = b.number_input("¿Cuántos firmáis y la pedís, contándote?", min_value=2, max_value=8,
                                         key="calc_n")
            elif living == "otros":
                others = b.number_input("Ingresos al año de los demás que viven en el piso (€)", min_value=0,
                                        max_value=1000000, value=0, step=1000, key="calc_otros",
                                        help="Hoy cuentan los ingresos de todos los que viven en el piso; en el Plan, "
                                             "solo los tuyos.")
        a, b = st.columns(2, vertical_alignment="bottom")
        includes = a.selectbox("¿Qué incluye el precio?", list(INCLUDES), format_func=INCLUDES.get, key="calc_incluye",
                               help="Si el contrato no separa el garaje o el trastero, la norma cuenta como alquiler el "
                                    "80 %, el 95 % o el 75 % del precio.")
        expenses = b.checkbox("Incluye gastos sin separar", key="calc_gastos",
                              help="Comunidad, luz, agua… Leemos la norma así: esos gastos valen el 5 % del precio, y el "
                                   "alquiler es el 95 % restante.")
        a, b = st.columns(2, vertical_alignment="bottom")
        disability = a.selectbox("¿Alguna de estas situaciones?", list(DISABILITY), format_func=DISABILITY.get,
                                 key="calc_discapacidad",
                                 help="Solo cambia el límite de ingresos del Plan (5,5 o 6 × IPREM).")
        regular = b.checkbox("Tengo trabajo o una prestación", value=True, key="calc_fuente",
                             help="Con al menos 3 meses cotizados en los últimos 6, o una fuente de ingresos prevista de "
                                  "al menos 6 meses. La pide la regla de hoy (art. 4.1.d).")
        exclusions = st.multiselect("¿Te pasa alguna de estas cosas?", list(rb.EXCLUSIONS), format_func=rb.EXCLUSIONS.get,
                                    key="calc_exclusiones", placeholder="Ninguna")
        a, b = st.columns(2)
        nationality = a.checkbox("Nacionalidad o residencia válidas", value=True, key="calc_nacionalidad",
                                 help="Nacionalidad española, de la UE, del EEE o Suiza, o residencia legal en España.")
        other_aid = b.checkbox("Cobro otra ayuda al alquiler", key="calc_otra_ayuda",
                               help="Otra ayuda pública para pagar el alquiler. El Ingreso Mínimo Vital y las pensiones "
                                    "no contributivas no cuentan.")
        iprem = st.number_input("IPREM al año, en 14 pagas (€)", min_value=1000, max_value=20000,
                                value=int(rb.IPREM_YEAR_2024), step=100, key="calc_iprem",
                                help="Los ingresos se comparan con el IPREM del año al que se refieren. 8.400 € es el de "
                                     "2024 (600 € al mes en 14 pagas).")

case = rb.Case(age=int(age), kind=kind, price=float(price), includes=includes, expenses_included=expenses, living=living,
               sharers=int(sharers), income=float(income), others_income=float(others), regular_income=regular,
               nationality=nationality, disability=disability, exclusions=frozenset(exclusions),
               other_rent_aid=other_aid)
# caps from the database (table topes, written by scripts/base_datos.py with rb.caps)
caps = query("SELECT regla, tope_piso, tope_habitacion FROM topes WHERE ine = ?", (t.loc[name, "ine"],)).set_index("regla")
results = {rule: rb.evaluate(case, rule, float(caps.loc[key, "tope_piso"]), float(caps.loc[key, "tope_habitacion"]),
                             iprem=float(iprem))
           for rule, key in RULE_IN_DB.items()}

euros = lambda x: es(x) + " €" if x % 1 == 0 else es(x, 2) + " €"  # noqa: E731
today = results["hoy"]
if today.eligible:
    st.success(f"**Hoy cumples los requisitos del Bono:** te darían {euros(today.monthly)} al mes durante "
               f"{today.months} meses ({euros(today.monthly * today.months)} en total).", icon=":material/check_circle:")
else:
    why = next(ch.text for ch in today.checks if not ch.ok)
    plan_ok, ours_ok = results["plan"].eligible, results["propuesta"].eligible
    tail = (" Con el Plan 2026-2030 y con nuestra propuesta, sí." if plan_ok and ours_ok else
            " Con el Plan 2026-2030, sí." if plan_ok else
            " Con el Plan 2026-2030, tampoco. Con nuestra propuesta, sí." if ours_ok else "")
    st.error(f"**Hoy no cumples los requisitos del Bono.** {why}.{tail}", icon=":material/cancel:")

st.subheader(f"En {name}")
SUBTITLE = {"hoy": "Convocatoria abierta desde el 3-feb-2025: 250 € al mes durante 2 años",
            "plan": "Lo que fija el Estado. La Comunidad aún no ha sacado su convocatoria y puede añadir requisitos",
            "propuesta": "El Plan, con el tope subido al alquiler de cada municipio (hasta 1.000 €), como permite su art. 135"}
for col, (rule, res) in zip(st.columns(3), results.items()):
    with col.container(border=True, height="stretch"):
        st.markdown(f"**{rb.RULES[rule]}**")
        st.caption(SUBTITLE[rule])
        if res.eligible:
            st.badge("Cumples los requisitos", icon=":material/check_circle:", color="green")
        else:
            st.badge("No cumples algún requisito", icon=":material/cancel:", color="red")
        m1, m2 = st.columns(2)
        m1.metric("Ayuda al mes", es(res.monthly) + " €" if res.monthly % 1 == 0 else es(res.monthly, 2) + " €")
        m2.metric(f"En {res.months} meses", es(res.monthly * res.months) + " €")
        cap = res.room_cap if kind == "habitacion" else res.flat_cap
        st.caption(f"Tope del alquiler aquí: {es(cap)} € ({'habitación' if kind == 'habitacion' else 'piso entero'}).")
        for ch in res.checks:  # what fails, in sight; everything, one click away
            if not ch.ok:
                st.markdown(f":red[:material/close:] {ch.text}  \n:gray[{ch.article}]")
        with st.expander(f"Los {len(res.checks)} requisitos, uno a uno"):
            for ch in res.checks:
                icon = ":green[:material/check:]" if ch.ok else ":red[:material/close:]"
                st.markdown(f"{icon} {ch.text}  \n:gray[{ch.article}]")

st.warning("Cumplir los requisitos no asegura la ayuda. Hoy se da por orden de llegada mientras queda dinero: en la "
           "convocatoria de 2022 se acabó el 6-nov-2023 y quien llegó después se quedó fuera.", icon=":material/info:")
st.caption("Tampoco comprobamos aquí: estar empadronado en la vivienda, el contrato (o firmarlo en 2 meses si te la "
           "conceden) ni las demás condiciones del art. 13 de la Ley General de Subvenciones. Con el Plan, la ayuda dura 2 "
           "años y la Comunidad puede alargarla 2 más (art. 134). Con varios jóvenes en un mismo contrato, el Plan da el "
           "60 % de la parte de cada uno: es nuestra lectura de su art. 137.")

with st.expander("De la norma al código: cada requisito, su artículo y su línea"):
    st.caption("Las reglas están en `scripts/reglas_bono.py`, una función por requisito. Esta tabla se hace leyendo ese "
               "fichero, así que no se puede quedar vieja. `scripts/probar_reglas.py` las prueba con casos hechos a mano.")
    rows = pd.DataFrame(rb.article_table())
    rows["codigo"] = "scripts/reglas_bono.py:" + rows["linea"].astype(str) + " · " + rows["funcion"]
    rows["requisito"] = rows["requisito"].str.replace("_", " ")
    st.dataframe(rows[["regla", "requisito", "articulo", "codigo"]], hide_index=True, width="stretch",
                 column_config={"regla": "Regla", "requisito": "Requisito", "articulo": "Artículo", "codigo": "Código"})
    st.caption("Normas: Acuerdo del Consejo de Gobierno del Bono Alquiler Joven 2024 (BDNS 805618), con los mismos "
               "artículos que el de 14-sep-2022; Real Decreto 326/2026, Plan Estatal de Vivienda 2026-2030 (BOE-A-2026-8872).")

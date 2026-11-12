"""EXPLORATORY (not pre-registered; written 12-Nov-2026, before running): how the proposal's quotas would work in a real
call, and who loses.

The Plan (RD 326/2026) says, in art. 138: "Las comunidades autónomas y ciudades de Ceuta y Melilla realizarán
convocatorias abiertas de esta ayuda de forma continuada y permanente". So the call cannot close once a year to compare
all the requests. simulador.py gives the proposal as a quota for each of 132 municipalities (water-filling, block
plan_amount); here it runs as an open call could run it:
  - the 31.8 M EUR are split into 4 "bolsas" (reserves): Madrid city and the three need groups of the rest (thirds of
    young people by need index; simulador.need_groups). Each bolsa gets the sum, over its municipalities, of the
    proposal's quota weight (young x need index x share of IRPF returns under the Plan's income limit) times the cost of
    an aid there (24 x the Plan's monthly aid). Art. 8.4 lets the region add "preferencias adicionales"
  - inside each bolsa, first come, as today: every request in a bolsa has the same chance
  - a bolsa whose requests cannot use all its money releases the rest to the bolsas that still have requests waiting, in
    proportion to their reserves. Andalucía did this with the provinces of its Bono Alquiler Joven (Resolución de
    29-nov-2024 de la Secretaría General de Vivienda, BOJA 245 of 19-dic-2024: 1,503,067.85 EUR from 7 provinces to
    Sevilla; the resolution reads "Se podrán realizar cuantas redistribuciones de crédito sean necesarias hasta
    agotar el crédito disponible")
  - caps: the proposal's (the Plan's, or the local p75 up to 1,000 EUR), which need the Ministry's agreement in the
    comisión de seguimiento before the call (art. 135)
It is compared, with the same money, the Plan's aid and the simulator's central beta, with the Plan as it is (one bolsa,
first come) and with the proposal as simulated (a quota per municipality).
Written before running:
  - the Plan as it is and the quotas per municipality give the figures of simulador_reparto.json (a check)
  - no bolsa has money left over: with about 12 requests per aid, every bolsa runs out (0 EUR released)
  - by group, the bolsas give within 3 % of the quotas per municipality: the third with the most need, +38 % to +44 %
    against the Plan as it is (the quotas give +41 %)
  - against the Plan as it is, Madrid city loses about 11 % (some 300 aids) and the low-need third less than 5 %; fewer
    than half of the 132 municipalities lose aids
  - inside each bolsa, first come gives more to the municipalities that ask more per young person, so the half of each
    group with the most need gets fewer aids per 1,000 young people than with the quotas (some of the targeting is lost)
Usage:  python -P scripts/como_se_aplica.py   (after simulador.py) -> resultados/como_se_aplica.json and
        data/COMO_SE_APLICA.md
"""
import json
import pathlib
import sys
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT  # noqa: E402
import simulador as sim  # noqa: E402

RES = ROOT / "resultados"
DOC = ROOT / "data" / "COMO_SE_APLICA.md"
PROPOSAL = "necesidad_requisito_plan_p75_hasta_1000"
GROUPS = ["resto, necesidad alta", "resto, necesidad media", "resto, necesidad baja", "Madrid capital"]
NAMES = {"resto, necesidad alta": "Tercio con más necesidad", "resto, necesidad media": "Tercio de necesidad media",
         "resto, necesidad baja": "Tercio con menos necesidad", "Madrid capital": "Madrid capital"}
SCENARIOS = {"plan_tal_cual": "el Plan tal cual (una sola bolsa, por orden de llegada)",
             "cupos_por_municipio": "la propuesta con un cupo para cada municipio (scripts/simulador.py)",
             "bolsas": "la propuesta con 4 bolsas y orden de llegada dentro de cada una"}
BOE = "https://www.boe.es/buscar/act.php?id=BOE-A-2026-8872"
BOJA = "https://www.juntadeandalucia.es/boja/2024/245/2"


def bolsas(group, req, weights, aid, budget):
    """4 reserves in proportion to the quota weights in euros; first come inside each; leftovers released (water-filling
    between bolsas, capped at the money each bolsa's requests can use). Returns aids, reserves and final money."""
    cost = 24 * aid
    reserve_w = np.array([(weights * cost)[group == g].sum() for g in GROUPS])
    demand = np.array([(req * cost)[group == g].sum() for g in GROUPS])
    money = sim.allocate(demand, reserve_w, budget)
    aids = np.zeros(len(req))
    for g, m in zip(GROUPS, money):
        k = group == g
        aids[k] = sim.allocate_money(req[k], req[k], m, aid[k])
    return aids, budget * reserve_w / reserve_w.sum(), money


def by_group(group, young, req, aids, aid):
    out = {}
    for g in GROUPS:
        k = group == g
        out[g] = {"young": int(young[k].sum()), "requests": round(float(req[k].sum())),
                  "aids": round(float(aids[k].sum()), 1),
                  "aids_per_1000_young": round(float(1000 * aids[k].sum() / young[k].sum()), 4),
                  "chance_of_aid": round(float(aids[k].sum() / req[k].sum()), 4),
                  "meur": round(float((aids[k] * 24 * aid[k]).sum() / 1e6), 3)}
    return out


def more_need_half(s, group):
    """Inside each group outside Madrid city, the municipalities with the most need that hold (about) half its young."""
    half = np.zeros(len(s), bool)
    for g in GROUPS[:3]:
        d = s[group == g].sort_values("indice_necesidad", ascending=False)
        cum = d["jovenes_20_34_2024"].cumsum() / d["jovenes_20_34_2024"].sum()
        take = d.index[cum <= 0.5] if (cum <= 0.5).any() else d.index[:1]
        half[s.index.get_indexer(take)] = True
    return half


def es(x, d=0):
    """Spanish number format, halves rounded up (as the app's datos.es)."""
    q = Decimal(str(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{q:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def signed(x, d=0):
    """es() with the sign: +41 % or −4 % (minus sign, as in the rest of the project)."""
    v = es(abs(x), d)
    return v if v.strip("0,") == "" else ("+" if x > 0 else "−") + v


def nice(name):
    """«Rozas de Madrid (Las)» → «Las Rozas de Madrid»; Madrid city by its name in the project."""
    if name == "Madrid":
        return "Madrid capital"
    if name.endswith(")") and " (" in name:
        base, art = name[:-1].split(" (", 1)
        return f"{art} {base}"
    return name


def change(new, old):
    return round(100 * (new / old - 1), 2)


def build():
    s, _ = sim.load()
    s["grupo_necesidad"] = sim.need_groups(s)
    beta = json.loads((RES / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))[
        "real_cap_and_uniform_900"]["real_cap"]["beta"]
    rules = sim.rules(s)
    group, young = s["grupo_necesidad"].to_numpy(), s["jovenes_20_34_2024"].to_numpy(float)
    plan_caps = rules["plan_estatal"][0]
    prop_caps, how = rules[PROPOSAL]
    req_plan, req_prop = sim.requests(s, plan_caps, beta)[0], sim.requests(s, prop_caps, beta)[0]
    aid_plan, aid_prop = sim.plan_aid(s, plan_caps), sim.plan_aid(s, prop_caps)
    w = sim.need_weights(s, how, sim.PLAN_INCOME)
    aids = {"plan_tal_cual": sim.allocate_money(req_plan, req_plan, sim.BUDGET_EUR, aid_plan),
            "cupos_por_municipio": sim.allocate_money(req_prop, w, sim.BUDGET_EUR, aid_prop)}
    aids["bolsas"], reserve, money = bolsas(group, req_prop, w, aid_prop, sim.BUDGET_EUR)
    req = {"plan_tal_cual": req_plan, "cupos_por_municipio": req_prop, "bolsas": req_prop}
    aid = {"plan_tal_cual": aid_plan, "cupos_por_municipio": aid_prop, "bolsas": aid_prop}

    # check: the same figures as simulador.py (block plan_amount)
    pa = json.loads((RES / "simulador_reparto.json").read_text(encoding="utf-8"))["plan_amount"]
    for name, rule in (("plan_tal_cual", "plan_estatal"), ("cupos_por_municipio", PROPOSAL)):
        for g in GROUPS:
            k = group == g
            got = round(float(1000 * aids[name][k].sum() / young[k].sum()), 4)
            assert abs(got - pa[rule]["aids_per_1000_young_by_group"][g]) < 1e-9, (name, g, got)

    out = {"note": "EXPLORATORIO: la propuesta en una convocatoria abierta todo el año (RD 326/2026, art. 138): 4 bolsas "
                   "de dinero por necesidad, orden de llegada dentro de cada una y el sobrante a las demás; supuestos "
                   "en el docstring de scripts/como_se_aplica.py",
           "budget_meur": sim.BUDGET_EUR / 1e6, "beta": beta, "municipalities": len(s),
           "scenarios": {k: v for k, v in SCENARIOS.items()},
           "by_group": {name: by_group(group, young, req[name], aids[name], aid[name]) for name in aids},
           "bolsas": {g: {"reserve_meur": round(float(r / 1e6), 3), "reserve_share": round(float(r / sim.BUDGET_EUR), 4),
                          "money_meur": round(float(m / 1e6), 3)} for g, r, m in zip(GROUPS, reserve, money)},
           "released_between_bolsas_meur": round(float(np.clip(reserve - money, 0, None).sum() / 1e6), 3)}
    out["change_vs_plan_pct"] = {
        name: {g: change(out["by_group"][name][g]["aids_per_1000_young"], out["by_group"]["plan_tal_cual"][g]["aids_per_1000_young"])
               for g in GROUPS} for name in ("cupos_por_municipio", "bolsas")}

    delta = aids["bolsas"] - aids["plan_tal_cual"]
    lose = delta < -0.05
    rows = s.assign(grupo=[NAMES[g] for g in group], plan=aids["plan_tal_cual"].round(1), bolsas=aids["bolsas"].round(1),
                    delta=delta.round(1))[["municipio", "grupo", "indice_necesidad", "plan", "bolsas", "delta"]]
    rows = rows.sort_values("delta")
    out["who_loses_vs_plan"] = {
        "aids_delta_by_group": {g: round(float(delta[group == g].sum()), 1) for g in GROUPS},
        "municipalities_losing": int(lose.sum()), "young_in_losing": int(young[lose].sum()),
        "young_share_in_losing": round(float(young[lose].sum() / young.sum()), 4),
        "young_share_in_losing_outside_madrid": round(float(young[lose & (group != "Madrid capital")].sum() / young.sum()), 4),
        "municipalities_losing_outside_madrid": int((lose & (group != "Madrid capital")).sum()),
        "lose_most": rows.head(5).round(3).to_dict("records"),
        "gain_most": rows.tail(5)[::-1].round(3).to_dict("records")}

    half = more_need_half(s, group)
    out["more_need_half_of_each_third"] = {
        g: {"young": int(young[half & (group == g)].sum()),
            **{name: round(float(1000 * aids[name][half & (group == g)].sum() / young[half & (group == g)].sum()), 4)
               for name in aids}} for g in GROUPS[:3]}
    return out


def report(o):
    bg, ch, w = o["by_group"], o["change_vs_plan_pct"], o["who_loses_vs_plan"]
    rows = []
    for g in GROUPS:
        p, b = bg["plan_tal_cual"][g], bg["bolsas"][g]
        rows.append(f"| {NAMES[g]} | {es(p['young'])} | {es(o['bolsas'][g]['reserve_meur'], 1)} M€ "
                    f"({es(100 * o['bolsas'][g]['reserve_share'])} %) | {es(b['aids'])} | {es(100 * p['chance_of_aid'], 1)} | "
                    f"{es(100 * b['chance_of_aid'], 1)} | {es(p['aids_per_1000_young'], 2)} | "
                    f"{es(b['aids_per_1000_young'], 2)} | {signed(ch['bolsas'][g])} % |")
    named = lambda recs: "; ".join(f"{nice(r['municipio'])} ({signed(r['delta'])})" for r in recs)  # noqa: E731
    mad, low, high = "Madrid capital", "resto, necesidad baja", "resto, necesidad alta"
    half = o["more_need_half_of_each_third"][high]
    way = (half["bolsas"] - half["plan_tal_cual"]) / (half["cupos_por_municipio"] - half["plan_tal_cual"])
    cap_part = 100 * (np.exp(0.1 * o["beta"]) - 1)
    released = o["released_between_bolsas_meur"]
    left = ("Con los datos de 2022, **ninguna bolsa tiene dinero de sobra**: en todas hay muchas más solicitudes que "
            "ayudas, así que el dinero se acaba en todas y no se mueve nada entre bolsas. La regla del sobrante es para "
            "cuando una bolsa reciba menos solicitudes de las esperadas") if released == 0 else (
        f"Con los datos de 2022, entre bolsas se mueven **{es(released, 2)} M€** que sobran en alguna")
    return f"""# Cómo se aplicaría la propuesta en una convocatoria

Lo genera `scripts/como_se_aplica.py` con los datos del repositorio. **Es una propuesta de diseño, no un informe jurídico:** decidir y comprobar que encaja en la norma les toca a la Comunidad de Madrid y a sus servicios jurídicos.

## Lo que pide la norma
- **La convocatoria no se cierra** ([RD 326/2026]({BOE}), art. 138): las comunidades «realizarán convocatorias abiertas de esta ayuda de forma continuada y permanente», y la ayuda se paga de forma periódica. Por eso la propuesta no compara solicitudes entre sí: reparte el dinero en bolsas que se gastan por orden de llegada
- **La Comunidad puede poner sus preferencias** (art. 8.4): reconoce las ayudas con las preferencias del Plan y con las «preferencias adicionales» que ella establezca, si respetan las del Plan
- **Subir el tope necesita al Ministerio** (art. 135): un estudio actualizado del alquiler y, antes de convocar, un acuerdo en la comisión de seguimiento que acredite que el Ministerio está conforme con el tope nuevo. La base de ese estudio está en [ESTUDIO_ART135.md](ESTUDIO_ART135.md)
- **Ya se ha hecho algo parecido:** Andalucía repartió por provincias el dinero de su Bono Alquiler Joven. Como en Sevilla había solicitudes sin dinero, le pasó 1.503.067,85 € que sobraban en otras siete provincias ([Resolución de 29 de noviembre de 2024]({BOJA}), BOJA núm. 245, de 19-dic-2024). En la resolución se lee: «Se podrán realizar cuantas redistribuciones de crédito sean necesarias hasta agotar el crédito disponible»

## La propuesta, paso a paso
1. **Antes de convocar,** la Comunidad acuerda los topes nuevos con el Ministerio en la comisión de seguimiento (art. 135): el del Plan o, en los municipios de 10.000 habitantes o menos, el alquiler por debajo del cual quedan 3 de cada 4 contratos, sin pasar de 1.000 €
2. **La convocatoria se abre y no se cierra** (art. 138)
3. **El dinero se reparte en 4 bolsas,** que se publican con la convocatoria, con la lista de municipios de cada una: Madrid capital y tres grupos con el resto de municipios, cada uno con un tercio de sus jóvenes, de más a menos necesidad. Cada bolsa recibe según sus jóvenes de 20 a 34 años, su índice de necesidad, la parte de las declaraciones del IRPF por debajo del límite de ingresos del Plan y lo que cuesta allí cada ayuda
4. **Dentro de cada bolsa, por orden de llegada,** como hoy. No hay que comparar solicitudes, así que la convocatoria puede seguir abierta
5. **Lo que sobra no se pierde:** cada trimestre, el dinero que una bolsa no va a usar, porque no le quedan solicitudes esperando, pasa a las bolsas que sí tienen, en proporción a su reserva
6. **Cada año, las bolsas se recalculan** con los datos nuevos, con un comando: `python scripts/rehacer_todo.py`

## Lo que sale, con el mismo dinero ({es(o['budget_meur'], 1)} M€)
Simulación con la cuantía del Plan (art. 137) y las solicitudes de 2022, como en `scripts/simulador.py`.

| Bolsa | Jóvenes de 20 a 34 | Reserva | Ayudas | De cada 100 que la piden, la consiguen: con el Plan | Con las bolsas | Ayudas por 1.000 jóvenes: con el Plan | Con las bolsas | Cambio |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

- **Las 4 bolsas dan casi lo mismo que los cupos por municipio,** que es lo que simula el resto del proyecto: el tercio con más necesidad recibe un {es(ch['bolsas'][high], 1)} % más que con el Plan tal cual (con cupos por municipio, un {es(ch['cupos_por_municipio'][high], 1)} %)
- {left}

## Quién pierde
- **Madrid capital:** {es(-w['aids_delta_by_group'][mad])} ayudas menos que con el Plan tal cual ({signed(ch['bolsas'][mad], 1)} %). De cada 100 jóvenes de Madrid capital que la piden, la conseguirían {es(100 * bg['plan_tal_cual'][mad]['chance_of_aid'], 1)} con el Plan y {es(100 * bg['bolsas'][mad]['chance_of_aid'], 1)} con las bolsas
- **El tercio con menos necesidad:** {es(-w['aids_delta_by_group'][low])} ayudas menos ({signed(ch['bolsas'][low], 1)} %)
- **Por municipios:** {w['municipalities_losing']} de los {o['municipalities']} reciben menos ayudas que con el Plan tal cual: Madrid capital, donde viven el {es(100 * (w['young_share_in_losing'] - w['young_share_in_losing_outside_madrid']))} % de los jóvenes, y otros {w['municipalities_losing_outside_madrid']}, con el {es(100 * w['young_share_in_losing_outside_madrid'])} %. Los que más pierden: {named(w['lose_most'])}. Los que más ganan: {named(w['gain_most'])}
- **Dentro de cada bolsa manda el orden de llegada,** así que se pierde algo de puntería. En los municipios del tercio con más necesidad que más la necesitan (la mitad de sus jóvenes), las bolsas dan {es(half['bolsas'], 2)} ayudas por cada 1.000 jóvenes; los cupos por municipio, {es(half['cupos_por_municipio'], 2)}, y el Plan tal cual, {es(half['plan_tal_cual'], 2)}. Las bolsas consiguen el {es(100 * way)} % de la mejora de los cupos. Con más bolsas se afinaría más (no lo hemos simulado)

## Lo que esto no resuelve
- **Madrid capital va en una sola bolsa,** porque las solicitudes son por municipio: dentro de Madrid, todos los distritos perderían lo mismo, también los de menos renta. Para una bolsa por distrito harían falta las solicitudes por distrito, que no tenemos
- **Suponemos que el orden de llegada no depende del municipio,** como en el simulador. Si en un municipio se pide antes, se lleva más de su bolsa
- **Los núcleos de 10.000 habitantes o menos** dentro de municipios más grandes también tienen el tope de 500 € del Plan, y con datos por municipio no se ven
- **Las cifras son una simulación** con las solicitudes de 2022 y la parte del efecto que se debe al tope ({signed(cap_part, 1)} % de solicitudes por cada 10 puntos de alquiler por encima)

Todas las cifras, en `resultados/como_se_aplica.json`.
"""


def main():
    out = build()
    with open(RES / "como_se_aplica.json", "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1, default=float) + "\n")
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write(report(out))
    print(json.dumps({k: out[k] for k in ("bolsas", "released_between_bolsas_meur", "change_vs_plan_pct",
                                          "more_need_half_of_each_third")}, ensure_ascii=False, indent=1))
    print(json.dumps(out["who_loses_vs_plan"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

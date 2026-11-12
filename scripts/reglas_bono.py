"""Who can get the youth rent aid, requirement by requirement, under three rules (written 8-Nov-2026 for the calculator):
  - hoy: Bono Alquiler Joven 2024 of the Comunidad de Madrid (Acuerdo of 2024, BDNS 805618; arts. 4, 5, 7 and 8 say the
    same as the Acuerdo of 14-Sep-2022). Open since 3-Feb-2025
  - plan: Plan Estatal de Vivienda 2026-2030 (RD 326/2026, BOE-A-2026-8872), youth aid: arts. 8.2, 133, 134, 136, 137
  - propuesta: the Plan with the cap raised under its art. 135 to the local p75 of 2024 (SERPAVI) rounded up to 50 EUR,
    never below the Plan's cap and never above 1,000 EUR (rule necesidad_requisito_plan_p75_hasta_1000 of simulador.py);
    room cap 60 % of the flat cap rounded to 50 EUR (habitaciones.py)
The Plan only sets the State's minimum: the Comunidad may add requirements (RD 326/2026, art. 8.1) and its call is not out.
Every requirement is one function and names its article; article_table() gives each one's line in this file, so the list
article -> line of code is built from here and cannot drift from the code.
Two readings the norm does not settle (the app says so):
  - a price with expenses not broken down: the rent is 95 % of the price (Bono, art. 5: expenses valued at 5 % of the price)
  - Plan, young people sharing one flat contract: 60 % of each one's share of the rent (art. 137: "que deban satisfacer")
No pandas and no Streamlit: the app's calculator and scripts/probar_reglas.py import it."""
import inspect
import math
from dataclasses import dataclass

IPREM_YEAR_2024 = 600.0 * 14  # IPREM of 14 payments in 2024: 8,400 EUR (income is compared with the IPREM of its year)
ROOM_RATIO_PROPOSAL = 0.6  # as habitaciones.py: the Plan's 600 EUR room for a 1,000 EUR flat
# Bono, art. 5: share of a price that is rent when the contract adds a garage and/or a storage room without breaking it down
ANNEX_SHARE = {"vivienda": 1.0, "garaje": 0.80, "trastero": 0.95, "garaje_trastero": 0.75}
EXPENSES_SHARE = 0.95  # reading of art. 5: expenses not broken down are valued at 5 % of the price
EXCLUSIONS = {
    "vivienda_propia": "Tengo una vivienda en propiedad o usufructo en España y puedo usarla",
    "vivienda_conviviente": "Alguien que vive conmigo tiene una vivienda en propiedad o usufructo en España",
    "familiar_casero": "Soy familiar del casero hasta 2.º grado (padres, hijos, abuelos, nietos, hermanos o los de mi pareja)",
    "familiar_casero_conviviente": "Alguien que vive conmigo es familiar del casero hasta 2.º grado",
    "socio_casero": "Soy socio de la persona o la empresa que me alquila",
    "socio_casero_conviviente": "Alguien que vive conmigo es socio de quien alquila",
}
OWN_EXCLUSIONS = {"vivienda_propia", "familiar_casero", "socio_casero"}  # the Plan only looks at the applicant (art. 133.2)
RULES = {
    "hoy": "Hoy: Bono Alquiler Joven 2024",
    "plan": "Plan Estatal 2026-2030",
    "propuesta": "Nuestra propuesta",
}


@dataclass(frozen=True)
class Case:
    age: int
    kind: str = "piso"  # "piso" (the whole flat) or "habitacion"
    price: float = 0.0  # monthly price written in the contract; for a shared flat, the whole flat
    includes: str = "vivienda"  # key of ANNEX_SHARE
    expenses_included: bool = False  # community fees or bills inside the price, not broken down
    living: str = "solo"  # flat only: "solo", "jovenes" (others up to 35 who also sign and apply) or "otros"
    sharers: int = 1  # flat with "jovenes": how many sign and apply, the applicant included
    income: float = 0.0  # own yearly income in the last year declared
    others_income: float = 0.0  # flat with "otros": yearly income of everyone else who lives there
    regular_income: bool = True  # job, or a public benefit, with 3 months worked in the last 6 (Bono, art. 4.1.d)
    nationality: bool = True  # Spanish, EU, EEA or Swiss, or legal residence in Spain
    disability: str = "no"  # Plan: "no", "33" (33 % or more, or child of a victim of gender violence) or "65"
    exclusions: frozenset = frozenset()  # keys of EXCLUSIONS
    other_rent_aid: bool = False  # another public aid for the rent (not the IMV or a non-contributory pension)


@dataclass(frozen=True)
class Context:
    rule: str
    flat_cap: float
    room_cap: float
    iprem: float
    rent: float  # what counts as rent under art. 5 (Bono); the Plan's call may say otherwise


@dataclass(frozen=True)
class Check:
    key: str
    article: str
    ok: bool
    text: str


@dataclass(frozen=True)
class Result:
    rule: str
    eligible: bool
    monthly: float  # aid per month for this person (0 if not eligible)
    months: int
    checks: tuple
    flat_cap: float
    room_cap: float
    rent: float


def eur(x):
    """1.234 € / 191,99 €, as in the rest of the app."""
    x = round(float(x), 2)
    s = f"{x:,.0f}" if x.is_integer() else f"{x:,.2f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".") + " €"


def times_iprem(t):
    return f"{t:g}".replace(".", ",")


def caps(rule, cap_2024, population, p75=None):
    """(flat cap, room cap) in EUR/month for one municipality under one rule."""
    if rule == "hoy":  # Bono, art. 5: 600 / 300 EUR; 900 / 450 EUR in the 55 municipalities of Annex II
        return float(cap_2024), cap_2024 / 2
    plan = (500.0, 250.0) if population <= 10000 else (1000.0, 600.0)  # RD 326/2026, art. 133.1.e
    if rule == "plan":
        return plan
    flat = plan[0] if p75 is None or math.isnan(p75) else min(max(math.ceil(p75 / 50) * 50, plan[0]), 1000.0)
    return float(flat), float(round(ROOM_RATIO_PROPOSAL * flat / 50) * 50)


def counted_rent(c):
    """Rent that counts against the cap (Bono, art. 5): garage / storage room and expenses taken out of the price."""
    return round(c.price * ANNEX_SHARE[c.includes] * (EXPENSES_SHARE if c.expenses_included else 1.0), 2)


# --- requirements: each returns (ok, text) --------------------------------------------------------------------------
def age(c, x):
    return 18 <= c.age <= 35, f"Tienes {c.age} años; hace falta ser mayor de edad y tener 35 o menos"


def nationality(c, x):
    return c.nationality, ("Nacionalidad española, de la UE, del EEE o Suiza, o residencia legal en España"
                           + ("" if c.nationality else ": has dicho que no"))


def regular_income(c, x):
    return c.regular_income, ("Hace falta una fuente regular de ingresos: trabajo o una prestación pública, con al menos "
                              "3 meses cotizados en los últimos 6 o una duración prevista de 6 meses"
                              + ("" if c.regular_income else ": has dicho que no"))


def income_today(c, x):
    limit = 3 * x.iprem
    if c.kind == "piso" and c.living == "otros":
        counted, who = c.income + c.others_income, "los ingresos de todos los que viven en el piso"
    else:  # a room, living alone, or young people who all sign: each one's own income
        counted, who = c.income, "tus ingresos"
    return counted <= limit, f"Cuentan {who}: {eur(counted)} al año, y el límite es {eur(limit)} (3 × IPREM)"


def income_plan(c, x):
    times = {"no": 5.0, "33": 5.5, "65": 6.0}[c.disability]
    limit = times * x.iprem
    return c.income <= limit, (f"Cuentan solo tus ingresos: {eur(c.income)} al año, y el límite es {eur(limit)} "
                               f"({times_iprem(times)} × IPREM)")


def rent_cap(c, x):
    cap = x.room_cap if c.kind == "habitacion" else x.flat_cap
    what = "de la habitación" if c.kind == "habitacion" else "del piso entero"
    adjusted = "" if x.rent == c.price else f" (de un precio de {eur(c.price)}, sin garaje, trastero ni gastos)"
    return x.rent <= cap, f"El alquiler {what} cuenta {eur(x.rent)}{adjusted}, y el tope es {eur(cap)}"


def exclusions_today(c, x):
    hit = sorted(c.exclusions)
    return not hit, ("No puede haber vivienda en propiedad, parentesco ni sociedad con el casero, ni en ti ni en quien "
                     "vive contigo" + (f": has marcado {len(hit)}" if hit else ""))


def exclusions_plan(c, x):
    hit = sorted(c.exclusions & OWN_EXCLUSIONS)
    return not hit, ("No puedes tener vivienda en propiedad, ni parentesco ni sociedad con el casero (solo cuentas tú)"
                     + (f": has marcado {len(hit)}" if hit else ""))


def other_aid(c, x):
    return not c.other_rent_aid, ("No se puede cobrar a la vez otra ayuda pública para el alquiler (sí el Ingreso Mínimo "
                                  "Vital o una pensión no contributiva)" + (": tendrías que elegir" if c.other_rent_aid else ""))


# --- amount ---------------------------------------------------------------------------------------------------------
def amount_today(c, x):
    """Bono, art. 8: 250 EUR a month, never more than the rent; sharers split it when 250 each would pass the rent."""
    n = c.sharers if c.kind == "piso" and c.living == "jovenes" else 1
    return min(250.0, x.rent / n), 24


def amount_plan(c, x):
    """RD 326/2026, art. 137: up to 300 EUR (flat) or 200 EUR (room), never more than 60 % of the rent; art. 134: 2 years,
    which the Comunidad may extend by up to 2 more."""
    n = c.sharers if c.kind == "piso" and c.living == "jovenes" else 1
    return min(200.0 if c.kind == "habitacion" else 300.0, 0.6 * x.rent / n), 24


TODAY = [("edad", "Bono, art. 4.1.a", age), ("nacionalidad", "Bono, art. 4.1.b", nationality),
         ("fuente_de_ingresos", "Bono, art. 4.1.d", regular_income), ("ingresos", "Bono, art. 4.1.d", income_today),
         ("alquiler", "Bono, art. 5 y anexo II", rent_cap), ("exclusiones", "Bono, art. 4.2", exclusions_today),
         ("otras_ayudas", "Bono, art. 7", other_aid)]
PLAN = [("edad", "RD 326/2026, art. 133.1.b", age), ("nacionalidad", "RD 326/2026, art. 8.2.a", nationality),
        ("ingresos", "RD 326/2026, art. 133.1.d", income_plan), ("alquiler", "RD 326/2026, art. 133.1.e", rent_cap),
        ("exclusiones", "RD 326/2026, art. 133.2", exclusions_plan), ("otras_ayudas", "RD 326/2026, art. 136", other_aid)]
PROPOSAL = [(k, "RD 326/2026, art. 135 (tope del alquiler local, hasta 1.000 €)" if k == "alquiler" else a, f)
            for k, a, f in PLAN]
REQUIREMENTS = {"hoy": TODAY, "plan": PLAN, "propuesta": PROPOSAL}
AMOUNT = {"hoy": ("Bono, art. 8", amount_today), "plan": ("RD 326/2026, arts. 134 y 137", amount_plan),
          "propuesta": ("RD 326/2026, arts. 134 y 137", amount_plan)}


def evaluate(c, rule, flat_cap, room_cap, iprem=IPREM_YEAR_2024):
    x = Context(rule, flat_cap, room_cap, iprem, counted_rent(c))
    checks = tuple(Check(k, a, *f(c, x)) for k, a, f in REQUIREMENTS[rule])
    eligible = all(ch.ok for ch in checks)
    monthly, months = AMOUNT[rule][1](c, x)
    return Result(rule, eligible, round(monthly, 2) if eligible else 0.0, months, checks, flat_cap, room_cap, x.rent)


def article_table():
    """Rows (rule, requirement, article, function, line in this file): the list article -> line of code."""
    rows = []
    for rule, reqs in REQUIREMENTS.items():
        for key, article, f in [*reqs, ("cuantía", *AMOUNT[rule])]:
            rows.append({"regla": RULES[rule], "requisito": key, "articulo": article, "funcion": f.__name__,
                         "linea": inspect.getsourcelines(f)[1]})
    rows.append({"regla": "Todas", "requisito": "tope del alquiler por municipio", "articulo":
                 "Bono, art. 5; RD 326/2026, arts. 133.1.e y 135", "funcion": caps.__name__,
                 "linea": inspect.getsourcelines(caps)[1]})
    rows.append({"regla": "Todas", "requisito": "alquiler que cuenta", "articulo": "Bono, art. 5", "funcion":
                 counted_rent.__name__, "linea": inspect.getsourcelines(counted_rent)[1]})
    return rows

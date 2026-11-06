"""Feasibility check of the central hypothesis (before the development period, 27-Oct-2026; exploration only).

Hypothesis: the Bono Alquiler Joven rent cap (600 EUR/month, 900 EUR in the 29 municipalities of Annex II of the
Acuerdo of 14-Sep-2022) leaves out young people in municipalities where typical rents are above the cap.

Feasibility rules, written BEFORE running this script (27-Oct). The hypothesis "can be tested" from 7-Nov if:
  F1  SERPAVI 2022 median rent exists for >= 80 % of the municipalities with >= 50 Bono requests
  F2  >= 10 municipalities with >= 50 requests in EACH cap group (600 and 900)
  F3  the estimated share of the rental market above the cap varies: interquartile range >= 10 points
  F4  the two cap groups overlap in local rent: >= 5 municipalities per group inside the common rent range
      (needed for the "natural experiment": same rent, different cap)
First look (descriptive, not a test): expected sign of corr(acceptance rate, share above cap) is NEGATIVE.
Known confounder (BOCM 16-Aug-2024): many rejections were "credit exhausted" (Orden 6-Nov-2023), not "rent too high".

Usage:  python scripts/hipotesis_tope.py
"""
import math
import pathlib
import re
import unicodedata

import numpy as np
import openpyxl
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "interim"
YEAR = 22  # SERPAVI year suffix: 2022 rents, same year as the Bono call
# Annex II of the Acuerdo del Consejo de Gobierno of 14-Sep-2022 (cap 900 EUR flat / 450 EUR room), checked on 27-Oct
CAP900 = ["Alcalá de Henares", "Alcobendas", "Alcorcón", "Algete", "Arroyomolinos", "Boadilla del Monte", "Getafe",
          "Collado Villalba", "Coslada", "Fuenlabrada", "Galapagar", "Las Rozas de Madrid", "Leganés", "Madrid",
          "Majadahonda", "Móstoles", "Parla", "Pinto", "Pozuelo de Alarcón", "Rivas-Vaciamadrid",
          "San Fernando de Henares", "San Sebastián de los Reyes", "Torrejón de Ardoz", "Torrelodones", "Tres Cantos",
          "Valdemoro", "Villanueva de la Cañada", "Villanueva del Pardillo", "Villaviciosa de Odón"]


def norm(name):
    """'Rozas de Madrid, Las' / 'Las Rozas de Madrid' / 'Rivas Vaciamadrid' → same key."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    words = re.sub(r"[(),.\-]", " ", s).split()
    arts = {"el", "la", "los", "las"}
    return " ".join([w for w in words if w not in arts] + sorted(w for w in words if w in arts))


def share_above(cap, p25, p75):
    """Share of rents above the cap, assuming log-normal rents fitted on the 25th and 75th percentiles."""
    if not (p25 and p75 and p25 > 0 and p75 > p25):
        return np.nan
    mu, sigma = (math.log(p25) + math.log(p75)) / 2, (math.log(p75) - math.log(p25)) / (2 * 0.6745)
    return 1 - 0.5 * (1 + math.erf((math.log(cap) - mu) / (sigma * math.sqrt(2))))


def serpavi_madrid():
    wb = openpyxl.load_workbook(RAW / "serpavi_mivau" / "bd_SERPAVI_2011-2024.xlsx", read_only=True)
    rows = wb["Municipios"].iter_rows(values_only=True)
    head = next(rows)
    df = pd.DataFrame([r for r in rows if str(r[0]).zfill(2) == "28"], columns=head)  # CPRO mixes '01' and 28
    cols = {f"BI_ALVHEPCO_TVC_{YEAR}": "n_rentals_flats", f"ALQTBID12_M_VC_{YEAR}": "rent_median",
            f"ALQTBID12_25_VC_{YEAR}": "rent_p25", f"ALQTBID12_75_VC_{YEAR}": "rent_p75"}
    df = df[["CUMUN", "NMUN", *cols]].rename(columns=cols)
    df["ine"] = df["CUMUN"].astype(str).str.zfill(5).str[-3:]
    return df


bono = pd.read_csv(RAW / "spacm_bono_alquiler_joven_2022" / "spacm_bono_alquiler_joven_2022.csv", sep=";",
                   encoding="latin-1", dtype={"municipio": str})
b = bono[bono["municipio"].str.fullmatch(r"\d{3}", na=False)].copy()
b["acc_rate"] = b["aceptadas"] / b["solicitudes"]
cap_keys = {norm(n) for n in CAP900}
b["cap"] = np.where(b["municipio_nombre"].map(norm).isin(cap_keys), 900, 600)
print(f"Annex II matched in the Bono file: {(b['cap'] == 900).sum()} of {len(CAP900)} "
      f"(missing: {sorted(cap_keys - set(b['municipio_nombre'].map(norm)))})")

s = serpavi_madrid()
m = b.merge(s, left_on="municipio", right_on="ine", how="left")
for c in ["rent_median", "rent_p25", "rent_p75", "n_rentals_flats"]:
    m[c] = pd.to_numeric(m[c], errors="coerce")
m["share_above_cap"] = [share_above(c, a, z) for c, a, z in zip(m["cap"], m["rent_p25"], m["rent_p75"])]
m["rent_to_cap"] = m["rent_median"] / m["cap"]

# young people (20-34) from the annual census; Comunidad de Madrid code = INE code * 10 + check digit
pop = pd.read_csv(next((RAW / "poblacion_censada_por_edad_nacionalidad_y_sexo").glob("*.csv")), sep=";", encoding="latin-1")
pop = pop[(pop["Tipo territorio"] == "Municipios") & (pop["Nacionalidad"] == "Total") & (pop["Sexo"] == "Total")
          & pop["Edad"].isin(["De 20-24 años", "De 25-29 años", "De 30-34 años"]) & (pop["Año"] == 2022)]
pop = pop.assign(ine=(pop["Código territorio"] // 10).astype(int).map("{:03d}".format)).groupby("ine")["Valor"].sum()
m["young_20_34"] = m["municipio"].map(pop)
ten = pd.read_csv(next((RAW / "censo_2021_viviendas_familiares_por_tenencia").glob("*.csv")), sep=";", encoding="latin-1")
ten = ten[(ten["Tipo territorio"] == "Municipios") & (ten["Régimen"] == "Alquiler")]
m["rented_households_2021"] = m["municipio"].map(
    ten.assign(ine=(ten["Código territorio"] // 10).astype(int).map("{:03d}".format)).set_index("ine")["Valor"])
m["accepted_per_1000_young"] = 1000 * m["aceptadas"] / m["young_20_34"]

big = m[m["solicitudes"] >= 50]
print(f"\nmunicipalities in the Bono file: {len(m)} | with >= 50 requests: {len(big)} "
      f"({big['solicitudes'].sum():,} of {m['solicitudes'].sum():,} requests)")
print(f"SERPAVI 20{YEAR} median rent found: {m['rent_median'].notna().sum()} of {len(m)}; "
      f"population 20-34 found: {m['young_20_34'].notna().sum()}; rented households 2021 found: "
      f"{m['rented_households_2021'].notna().sum()}")

f1 = big["rent_median"].notna().mean()
g = big.groupby("cap")
f2 = g.size()
q = big["share_above_cap"].quantile([0.25, 0.75])
lo, hi = (max(g["rent_median"].min()), min(g["rent_median"].max()))
f4 = big[big["rent_median"].between(lo, hi)].groupby("cap").size()
print("\n--- feasibility rules ---")
print(f"F1 rent available for {f1:.0%} of municipalities with >= 50 requests -> {'PASS' if f1 >= 0.8 else 'FAIL'}")
print(f"F2 municipalities per cap group: {f2.to_dict()} -> {'PASS' if f2.min() >= 10 and len(f2) == 2 else 'FAIL'}")
print(f"F3 share above cap, IQR {q[0.25]:.1%} to {q[0.75]:.1%} ({(q[0.75] - q[0.25]) * 100:.1f} points) -> "
      f"{'PASS' if q[0.75] - q[0.25] >= 0.10 else 'FAIL'}")
print(f"F4 common rent range {lo:.0f}-{hi:.0f} EUR; municipalities inside it per group: {f4.to_dict()} -> "
      f"{'PASS' if len(f4) == 2 and f4.min() >= 5 else 'FAIL'}")

print("\n--- first look (descriptive only) ---")
ok = big.dropna(subset=["share_above_cap"])
w = ok["solicitudes"]
r = np.corrcoef(ok["acc_rate"], ok["share_above_cap"])[0, 1]
print(f"corr(acceptance rate, share above cap), n={len(ok)}: {r:+.2f}")
print(ok.groupby("cap").apply(lambda d: pd.Series({
    "municipalities": len(d), "requests": d["solicitudes"].sum(),
    "acceptance": d["aceptadas"].sum() / d["solicitudes"].sum(),
    "median_rent": d["rent_median"].median(), "share_above_cap_median": d["share_above_cap"].median()})).round(3).to_string())
ok = ok.assign(band=pd.qcut(ok["share_above_cap"], 3, labels=["low share above cap", "mid", "high share above cap"]))
print(ok.groupby("band", observed=True).apply(lambda d: pd.Series({
    "municipalities": len(d), "acceptance": d["aceptadas"].sum() / d["solicitudes"].sum(),
    "share_above_cap": d["share_above_cap"].median()})).round(3).to_string())
# Second look, written on 27-Oct AFTER seeing the flat first look and BEFORE running this part: if the cap filters people
# out before they apply, applications per 1,000 young people (and per 1,000 rented households) should be LOWER where the
# share above the cap is higher, also inside the common rent range of both cap groups.
print("\n--- second look: does the cap act before applying? (descriptive only) ---")
ok = ok.assign(req_per_1000_young=1000 * ok["solicitudes"] / ok["young_20_34"],
               req_per_1000_rented=1000 * ok["solicitudes"] / ok["rented_households_2021"])
for c in ["req_per_1000_young", "req_per_1000_rented"]:
    d = ok.dropna(subset=[c])
    print(f"corr({c}, share above cap), n={len(d)}: {np.corrcoef(d[c], d['share_above_cap'])[0, 1]:+.2f} | "
          f"Spearman {d[c].corr(d['share_above_cap'], method='spearman'):+.2f}")
print(ok.groupby("band", observed=True)[["req_per_1000_young", "req_per_1000_rented"]].median().round(1).to_string())
common = ok[ok["rent_median"].between(lo, hi)]
print(f"inside the common rent range {lo:.0f}-{hi:.0f} EUR:")
print(common.groupby("cap").agg(municipalities=("cap", "size"), median_rent=("rent_median", "median"),
                                share_above_cap=("share_above_cap", "median"),
                                req_per_1000_young=("req_per_1000_young", "median"),
                                req_per_1000_rented=("req_per_1000_rented", "median")).round(3).to_string())
cols = ["municipio_nombre", "cap", "solicitudes", "acc_rate", "rent_median", "share_above_cap", "accepted_per_1000_young"]
print("\nlargest 12 municipalities by requests:")
print(big.sort_values("solicitudes", ascending=False)[cols].head(12).round(3).to_string(index=False))

OUT.mkdir(parents=True, exist_ok=True)
m.drop(columns=["CUMUN", "ine"]).to_csv(OUT / "exploracion_tope_municipios.csv", index=False, encoding="utf-8")
print(f"\nsaved {OUT / 'exploracion_tope_municipios.csv'}")

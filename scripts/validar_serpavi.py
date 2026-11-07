"""Does the SERPAVI (Ministry) agree with the Comunidad de Madrid's own rent data? (development period)

The key variable of the project (share of the rental market above the cap) comes from the SERPAVI percentiles. The
portal has two rent sources of its own, and this script checks the SERPAVI against both:
  1. Level: average monthly rent of rented homes (viviendas habituales), municipalities over 20,000 people, 2023 and
     2024 (dataset alquiler_medio_mensual_..._municipios_mas_20000) against the SERPAVI median of the same year
  2. Change: rental price index (base 2015), municipalities over 10,000 people (dataset 1934445), growth 2022 -> 2024,
     against the growth of the SERPAVI median over the same years
Usage:  python -P scripts/validar_serpavi.py   -> resultados/validacion_serpavi.json
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT, cm_to_ine, leer_csv, share_above  # noqa: E402


def portal(ds):
    d = leer_csv(next((RAW / ds).glob("*.csv")))
    d = d[d["Tipo territorio"] == "Municipios"].copy()
    d["ine"] = d["Código territorio"].map(cm_to_ine)
    d["Valor"] = pd.to_numeric(d["Valor"], errors="coerce")  # "-" = protected by statistical secrecy
    return d


def compare(a, b):
    both = pd.concat([a, b], axis=1).dropna()
    return {"n": len(both), "pearson": round(float(both.iloc[:, 0].corr(both.iloc[:, 1])), 3),
            "spearman": round(float(both.iloc[:, 0].corr(both.iloc[:, 1], method="spearman")), 3),
            "median_ratio_serpavi_over_portal": round(float((both.iloc[:, 0] / both.iloc[:, 1]).median()), 3)}


def gap_sensitivity(s, growth):
    """Share of the market above the current cap in 2024 (weighted by young people) if, where the portal has an index,
    the 2022 SERPAVI percentiles had grown like the portal index instead of like the SERPAVI itself."""
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str}).set_index("ine")
    p22 = s[s["year"] == 2022].set_index("ine")
    g = growth.reindex(t.index)
    alt25 = (p22["p25"].reindex(t.index) * g).fillna(t["serpavi_p25_2024"])
    alt75 = (p22["p75"].reindex(t.index) * g).fillna(t["serpavi_p75_2024"])
    alt = pd.Series([share_above(c, a, z) for c, a, z in zip(t["tope_2024"], alt25, alt75)], index=t.index)
    w = t["jovenes_20_34_2024"]
    ok = alt.notna() & t["share_above_tope_2024_en_2024"].notna() & w.notna()
    avg = lambda v, m: round(float((v[m] * w[m]).sum() / w[m].sum()), 3)  # noqa: E731
    mad = t.index == "079"
    return {"municipalities_with_portal_index": int(g.notna().sum()),
            "serpavi_2024": {"all": avg(t["share_above_tope_2024_en_2024"], ok),
                             "without_madrid_city": avg(t["share_above_tope_2024_en_2024"], ok & ~mad)},
            "portal_growth": {"all": avg(alt, ok), "without_madrid_city": avg(alt, ok & ~mad)}}


def main():
    s = pd.read_csv(INTERIM / "serpavi_madrid_municipios.csv", dtype={"ine": str})
    med = s.pivot_table(index="ine", columns="year", values="med")
    out = {}
    rent = portal("alquiler_medio_mensual_viviendas_arrendadas_valor_catastral_municipios_mas_20000")
    rent = rent[rent["Tipo de vivienda"] == "Viviendas habituales"]
    for y in (2023, 2024):
        p = rent[rent["Año"] == y].set_index("ine")["Valor"].rename("portal")
        out[f"level_{y}"] = compare(med[y].rename("serpavi"), p)
    idx = portal("1934445").pivot_table(index="ine", columns="Año", values="Valor")
    growth_s, growth_p = (med[2024] / med[2022]).rename("serpavi"), (idx[2024] / idx[2022]).rename("portal_index")
    out["change_2022_2024"] = compare(growth_s - 1, growth_p - 1)
    both = pd.concat([growth_s, growth_p], axis=1).dropna()
    out["change_2022_2024"]["median_growth_pct"] = {k: round(100 * float(both[k].median() - 1), 1) for k in both}
    out["gap_2024_with_portal_growth"] = gap_sensitivity(s, growth_p)
    out["note"] = ("SERPAVI: median rent of collective rented dwellings; portal: average rent of rented homes (level) "
                   "and rental price index base 2015 (change). Pearson and Spearman by municipality.")
    print(json.dumps(out, indent=1, ensure_ascii=False))
    (ROOT / "resultados" / "validacion_serpavi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                               encoding="utf-8")


if __name__ == "__main__":
    main()

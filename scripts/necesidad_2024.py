"""2024 municipality table for the product (development period, after the pre-registered test): data/interim/municipios_2024.csv.

Not part of the pre-registered test (that one reads data/raw only and data/interim/municipios.csv).
  - Need index 0-100: mean of three percentile ranks among municipalities with all three
      rent effort      = 12 x SERPAVI median rent 2024 / gross disposable income per capita 2024
      youth jobless    = registered unemployment under 25 (mean of 2024) per 1,000 people aged 15-24 (2024)
      renting          = % of households that rent (Census 2021)
  - Eligibility gap: share of the rental market above the cap with the 2022 list (29) and the 2024 list (55), and above
    1,000 EUR (default cap of the Plan Estatal 2026-2030)
  - Did the Comunidad pick the right municipalities in Dec-2024? Ranks the 600 EUR municipalities of 2022 by their share
    of rents above 600 EUR in 2023 (the last SERPAVI year it could see) and compares with the 26 it moved to 900 EUR
Usage:  python -P scripts/necesidad_2024.py   (run preparar_datos.py and topes_convocatorias.py first)
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT, cm_to_ine, leer_csv, norm, share_above  # noqa: E402

NEW = ROOT / "data" / "raw_2026-11-06"  # renta and paro with 2024 (downloaded 6-Nov, identical on 7-Nov)
COMPONENTS = {"esfuerzo_alquiler_2024": "rent effort", "paro25_por_1000_15_24_2024": "youth jobless",
              "pct_alquiler_2021": "renting"}


def csv(base, folder):
    return leer_csv(next((base / folder).glob("*.csv")), dtype={"municipio": str})


def build():
    t = pd.read_csv(INTERIM / "topes_900_convocatorias.csv", dtype={"ine": str, "ine5": str})
    t = t.rename(columns={"nombre_estadistica_cm": "municipio", "tope_bono_2022": "tope_2022", "tope_bono_2024": "tope_2024"})
    t = t[["ine", "municipio", "tope_2022", "tope_2024", "sube_a_900_en_2024"]].copy()

    pop = csv(RAW, "poblacion_censada_por_edad_nacionalidad_y_sexo")
    pop = pop[(pop["Tipo territorio"] == "Municipios") & (pop["Nacionalidad"] == "Total") & (pop["Sexo"] == "Total")
              & (pop["Año"] == 2024)].assign(ine=lambda d: d["Código territorio"].map(cm_to_ine))
    by_age = pop.pivot_table(index="ine", columns="Edad", values="Valor", aggfunc="sum")
    t["pob_total_2024"] = t["ine"].map(by_age["Total"])
    t["jovenes_20_34_2024"] = t["ine"].map(by_age[["De 20-24 años", "De 25-29 años", "De 30-34 años"]].sum(axis=1))
    t["jovenes_15_24_2024"] = t["ine"].map(by_age[["De 15-19 años", "De 20-24 años"]].sum(axis=1))

    renta = csv(NEW, "irpf_indicador_renta")
    renta = renta[(renta["Tipo territorio"] == "Municipios") & (renta["Medida"] == "Per cápita") & (renta["Año"] == 2024)]
    t["renta_pc_2024"] = t["ine"].map(renta.assign(ine=renta["Código territorio"].map(cm_to_ine))
                                      .set_index("ine")["Valor"].pipe(pd.to_numeric, errors="coerce"))

    paro = csv(NEW, "paro_registrado_edad_municipio")
    paro = paro[(paro["Año"] == 2024) & (paro["Indicador"] == "Serie") & (paro["Edad"] == "Menor de 25 años")]
    loose = lambda s: " ".join(w for w in norm(s).split() if w not in ("de", "del"))  # noqa: E731 (as in preparar_datos)
    months = paro.groupby(paro["Municipio"].map(loose))["Valor"].agg(["mean", "size"])
    t["paro_menor25_2024"] = t["municipio"].map(loose).map(months["mean"])
    t["paro25_por_1000_15_24_2024"] = 1000 * t["paro_menor25_2024"] / t["jovenes_15_24_2024"]

    ten = csv(RAW, "censo_2021_viviendas_familiares_por_tenencia")
    ten = ten[ten["Tipo territorio"] == "Municipios"].assign(ine=lambda d: d["Código territorio"].map(cm_to_ine))
    ten = ten.pivot_table(index="ine", columns="Régimen", values="Valor", aggfunc="sum")
    t["pct_alquiler_2021"] = t["ine"].map(100 * ten["Alquiler"] / ten.sum(axis=1))

    s = pd.read_csv(INTERIM / "serpavi_madrid_municipios.csv", dtype={"ine": str})
    for y in (2023, 2024):
        sy = s[s["year"] == y].set_index("ine")
        for c in ("n", "med", "p25", "p75"):
            t[f"serpavi_{c}_{y}"] = t["ine"].map(sy[c])
    sh = lambda caps, y: [share_above(c, a, z) for c, a, z in zip(caps, t[f"serpavi_p25_{y}"], t[f"serpavi_p75_{y}"])]  # noqa: E731
    t["share_above_tope_2022_en_2024"] = sh(t["tope_2022"], 2024)
    t["share_above_tope_2024_en_2024"] = sh(t["tope_2024"], 2024)
    t["share_above_1000_2024"] = sh([1000] * len(t), 2024)
    t["share_above_600_2023"] = sh([600] * len(t), 2023)

    t["esfuerzo_alquiler_2024"] = 12 * t["serpavi_med_2024"] / t["renta_pc_2024"]
    full = t[list(COMPONENTS)].notna().all(axis=1)
    for c in COMPONENTS:
        t.loc[full, f"rango_{c}"] = t.loc[full, c].rank(pct=True)
    t["indice_necesidad"] = 100 * t.loc[full, [f"rango_{c}" for c in COMPONENTS]].mean(axis=1)
    t["tercil_necesidad"] = pd.qcut(t["indice_necesidad"], 3, labels=["baja", "media", "alta"])

    # Bono 2022 demand (base of the simulator): requests per young person and the 2022 share above the cap
    m = pd.read_csv(INTERIM / "municipios.csv", dtype={"ine": str}).set_index("ine")
    for c in ("bono_solicitudes", "bono_aceptadas", "jovenes_20_34_2022", "share_above_cap_2022"):
        t[c] = t["ine"].map(m[c])
    return t, months


def chosen_right(t):
    """Of the 2022 600-EUR municipalities with SERPAVI 2023 data, were the 26 moved to 900 the most expensive ones?"""
    c = t[(t["tope_2022"] == 600) & t["share_above_600_2023"].notna()].copy()
    c = c.sort_values("share_above_600_2023", ascending=False).reset_index(drop=True)
    k = int(c["sube_a_900_en_2024"].sum())
    top = c.head(k)
    left_out = top[~top["sube_a_900_en_2024"]]
    moved_low = c[c["sube_a_900_en_2024"]].index[c[c["sube_a_900_en_2024"]].index >= k]
    cols = ["municipio", "share_above_600_2023", "serpavi_med_2023", "pob_total_2024"]
    return {"candidates_600_with_serpavi_2023": len(c), "moved_with_data": k,
            "moved_total": int(t["sube_a_900_en_2024"].sum()),
            "moved_among_top_k": int(top["sube_a_900_en_2024"].sum()),
            "left_out_in_top_k": left_out[cols].round(3).to_dict("records"),
            "moved_outside_top_k": c.loc[moved_low, cols + []].assign(rank=moved_low + 1).round(3).to_dict("records")}


def main():
    t, months = build()
    t.to_csv(INTERIM / "municipios_2024.csv", index=False, encoding="utf-8")
    full = t["indice_necesidad"].notna()
    print(f"municipios_2024.csv: {len(t)} municipalities | need index: {full.sum()} "
          f"({t.loc[full, 'jovenes_20_34_2024'].sum() / t['jovenes_20_34_2024'].sum():.1%} of young people 20-34)")
    print("unemployment months per municipality (2024):", months["size"].value_counts().to_dict())
    print("missing:", {c: int(t[c].isna().sum()) for c in ["renta_pc_2024", "paro_menor25_2024", "serpavi_med_2024",
                                                           "pct_alquiler_2021", "jovenes_20_34_2024"]})
    print("Spearman between components:\n", t.loc[full, list(COMPONENTS)].corr("spearman").round(2).to_string())
    right = chosen_right(t)
    print(json.dumps(right, indent=1, ensure_ascii=False, default=float))
    (ROOT / "resultados" / "acierto_ampliacion_2024.json").write_text(
        json.dumps(right, indent=1, ensure_ascii=False, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()

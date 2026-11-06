"""Crosswalk of municipality identifiers across our sources (the trainer's warning of 5-Nov: each source names and codes
municipalities differently). Output: data/interim/codigos_municipios.{csv,json}, one row per municipality of the
Comunidad de Madrid (179), with every code and spelling we meet, and whether each source reaches it.
Usage:  python -P scripts/codigos_municipios.py   (run scripts/preparar_datos.py first: it caches the SERPAVI rows)
"""
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import CAP900_KEYS, INTERIM, RAW, cm_to_ine, leer_csv, norm  # noqa: E402


def csv(folder):
    return leer_csv(next((RAW / folder).glob("*.csv")), dtype={"municipio": str})


def loose(name):
    """norm() that also ignores 'de'/'del' ('Paracuellos de Jarama' = 'Paracuellos del Jarama')."""
    return " ".join(w for w in norm(name).split() if w not in ("de", "del"))


def main():
    pop = csv("poblacion_censada_por_edad_nacionalidad_y_sexo")
    pop = pop[pop["Tipo territorio"] == "Municipios"][["Código territorio", "Territorio"]].drop_duplicates()
    t = pd.DataFrame({"codigo_estadistica_cm": pop["Código territorio"].astype(int),
                      "nombre_estadistica_cm": pop["Territorio"]})
    t["ine"] = t["codigo_estadistica_cm"].map(cm_to_ine)
    t["ine5"] = "28" + t["ine"]
    t = t.drop_duplicates("ine").sort_values("ine").reset_index(drop=True)

    bono = csv("spacm_bono_alquiler_joven_2022")
    bono = bono[bono["municipio"].str.fullmatch(r"\d{3}", na=False)].set_index("municipio")["municipio_nombre"]
    t["nombre_bono_ayudas"] = t["ine"].map(bono)

    serpavi = pd.read_csv(INTERIM / "serpavi_madrid_municipios.csv", dtype={"ine": str})
    t["nombre_serpavi"] = t["ine"].map(serpavi.drop_duplicates("ine").set_index("ine")["nombre"])

    paro = csv("paro_registrado_edad_municipio")["Municipio"].drop_duplicates()
    paro_by_key = dict(zip(paro.map(loose), paro))
    t["nombre_paro"] = t["nombre_estadistica_cm"].map(loose).map(paro_by_key)

    t["tope_bono_2022"] = [900 if norm(n) in CAP900_KEYS else 600 for n in t["nombre_estadistica_cm"]]
    for col, label in [("nombre_bono_ayudas", "bono"), ("nombre_serpavi", "serpavi"), ("nombre_paro", "paro")]:
        t[f"en_{label}"] = t[col].notna()

    t.to_csv(INTERIM / "codigos_municipios.csv", index=False, encoding="utf-8")
    (INTERIM / "codigos_municipios.json").write_text(
        json.dumps(t.to_dict(orient="records"), ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(t)} municipalities | cap 900: {(t['tope_bono_2022'] == 900).sum()}")
    for label in ("bono", "serpavi", "paro"):
        miss = t.loc[~t[f"en_{label}"], "nombre_estadistica_cm"].tolist()
        print(f"in {label}: {t[f'en_{label}'].sum()} | missing ({len(miss)}): {miss[:25]}")
    diff = t[t["nombre_bono_ayudas"].notna() & (t["nombre_bono_ayudas"] != t["nombre_estadistica_cm"])]
    print(f"\nnames that differ between the statistics file and the Bono file: {len(diff)}; e.g.")
    print(diff[["ine", "nombre_estadistica_cm", "nombre_bono_ayudas", "nombre_serpavi", "nombre_paro"]].head(8).to_string(index=False))


if __name__ == "__main__":
    main()

"""Feasibility check (before the development period): does the Bono Alquiler Joven acceptance rate vary across
municipalities, and does it relate to income? Exploration only; the product is built from 7-Nov.
Usage:  python scripts/viabilidad.py
"""
import pathlib
import re
import unicodedata

import numpy as np
import pandas as pd

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"


def norm(name):
    """'Álamo, El' / 'Álamo (El)' / 'El Álamo' → 'alamo el'."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[(),.]", " ", s)
    words = s.split()
    arts = [w for w in words if w in ("el", "la", "los", "las")]
    rest = [w for w in words if w not in ("el", "la", "los", "las")]
    return " ".join(rest + arts)


bono = pd.read_csv(next((RAW / "spacm_bono_alquiler_joven_2022").glob("*.csv")), sep=";", encoding="latin-1", dtype={"municipio": str})
ayudas = pd.read_csv(next((RAW / "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos").glob("*.csv")), sep=";", encoding="latin-1", dtype={"municipio": str})
renta = pd.read_csv(next((RAW / "irpf_indicador_renta").glob("*.csv")), sep=";", encoding="latin-1")
paro = pd.read_csv(next((RAW / "302038").glob("*.csv")), sep=";", encoding="latin-1")

tot = bono[["solicitudes", "aceptadas", "rechazadas"]].sum()
print(f"Bono Alquiler Joven 2022: {len(bono)} rows | requests {tot.solicitudes:,} | accepted {tot.aceptadas:,} "
      f"({tot.aceptadas / tot.solicitudes:.1%}) | rejected {tot.rechazadas:,}")
print("rows without a real municipality:", bono[~bono["municipio"].str.fullmatch(r"\d{3}", na=False)][["municipio_nombre", "solicitudes"]].to_string(index=False))
b = bono[bono["municipio"].str.fullmatch(r"\d{3}", na=False)].copy()
b["acc_rate"] = b["aceptadas"] / b["solicitudes"]
big = b[b["solicitudes"] >= 100].sort_values("acc_rate")
print("\nacceptance rate, municipalities with ≥ 100 requests: lowest 8 / highest 8")
print(big.head(8)[["municipio_nombre", "solicitudes", "aceptadas", "acc_rate"]].round(3).to_string(index=False))
print(big.tail(8)[["municipio_nombre", "solicitudes", "aceptadas", "acc_rate"]].round(3).to_string(index=False))

print("\nayudas al alquiler (programas, años):", ayudas.groupby(["programa", "año_convocatoria"])[["solicitudes", "aceptadas"]].sum().to_string())

r = renta[(renta["Tipo territorio"] == "Municipios") & (renta["Medida"] == "Per cápita")].copy()
r["Valor"] = pd.to_numeric(r["Valor"], errors="coerce")
last = r["Año"].max()
r = r[r["Año"] == last][["Territorio", "Valor"]].rename(columns={"Valor": "renta_pc"})
r["key"] = r["Territorio"].map(norm)
b["key"] = b["municipio_nombre"].map(norm)
m = b.merge(r, on="key", how="left")
print(f"\nincome year {last}: matched {m['renta_pc'].notna().sum()} of {len(m)} municipalities; unmatched:",
      m.loc[m["renta_pc"].isna(), "municipio_nombre"].tolist()[:15])
mm = m[(m["solicitudes"] >= 50) & m["renta_pc"].notna()]
print(f"correlation acceptance rate vs income per capita (municipalities with ≥ 50 requests, n={len(mm)}): "
      f"{np.corrcoef(mm['acc_rate'], mm['renta_pc'])[0, 1]:+.2f}")
mm = mm.assign(tercil=pd.qcut(mm["renta_pc"], 3, labels=["low income", "mid", "high income"]))
print(mm.groupby("tercil", observed=True).apply(lambda g: pd.Series({"municipalities": len(g), "requests": g["solicitudes"].sum(),
      "acceptance": g["aceptadas"].sum() / g["solicitudes"].sum()})).round(3).to_string())

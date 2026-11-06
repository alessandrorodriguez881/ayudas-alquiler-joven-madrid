"""Build the municipality table used by the pre-registered test (PREREGISTRO.md): data/interim/municipios.csv.

Prints only coverage (how many municipalities each source reaches); it does not look at relations between variables.
The SERPAVI workbook (68 MB) is read once and cached in data/interim/serpavi_madrid_{municipios,distritos}.csv.
Usage:  python -P scripts/preparar_datos.py
"""
import pathlib
import sys

import numpy as np
import openpyxl
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import CAP900, CAP900_KEYS, INTERIM, RAW, cm_to_ine, leer_csv, norm, share_above  # noqa: E402

YEARS = range(11, 25)
MEASURES = {"BI_ALVHEPCO_TVC": "n", "ALQTBID12_M_VC": "med", "ALQTBID12_25_VC": "p25", "ALQTBID12_75_VC": "p75"}


def csv(folder):
    return leer_csv(next((RAW / folder).glob("*.csv")), dtype={"municipio": str})


def serpavi():
    """Madrid rows of the SERPAVI 'Municipios' and 'Distritos' sheets, long format (one row per area and year)."""
    out = {k: INTERIM / f"serpavi_madrid_{k}.csv" for k in ("municipios", "distritos")}
    if all(p.exists() for p in out.values()):
        return {k: pd.read_csv(p, dtype={"ine": str, "cudis": str}) for k, p in out.items()}
    wb = openpyxl.load_workbook(RAW / "serpavi_mivau" / "bd_SERPAVI_2011-2024.xlsx", read_only=True)
    res = {}
    for sheet, key, ids in [("Municipios", "municipios", ["CUMUN", "NMUN"]), ("Distritos", "distritos", ["CUMUN", "LITMUN", "CUDIS"])]:
        rows = wb[sheet].iter_rows(values_only=True)
        head = next(rows)
        df = pd.DataFrame([r for r in rows if str(r[0]).zfill(2) == "28"], columns=head)  # CPRO mixes '01' and 28
        long = []
        for y in YEARS:
            cols = {f"{c}_{y}": v for c, v in MEASURES.items() if f"{c}_{y}" in df.columns}
            part = df[ids + list(cols)].rename(columns=cols).assign(year=2000 + y)
            long.append(part)
        long = pd.concat(long, ignore_index=True)
        long["ine"] = long["CUMUN"].astype(str).str.zfill(5).str[-3:]
        long = long.rename(columns={"CUDIS": "cudis", "NMUN": "nombre", "LITMUN": "nombre"}).drop(columns="CUMUN")
        for c in MEASURES.values():
            long[c] = pd.to_numeric(long[c], errors="coerce")
        INTERIM.mkdir(parents=True, exist_ok=True)
        long.to_csv(out[key], index=False, encoding="utf-8")
        res[key] = long
    return res


def main():
    bono = csv("spacm_bono_alquiler_joven_2022")
    m = bono[bono["municipio"].str.fullmatch(r"\d{3}", na=False)].rename(columns={
        "municipio": "ine", "municipio_nombre": "municipio", "solicitudes": "bono_solicitudes",
        "aceptadas": "bono_aceptadas", "rechazadas": "bono_rechazadas"}).copy()
    m["cap"] = np.where(m["municipio"].map(norm).isin(CAP900_KEYS), 900, 600)
    assert (m["cap"] == 900).sum() == len(CAP900), "Annex II list does not match the Bono file"

    ay = csv("spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos")
    ay = ay[ay["municipio"].str.fullmatch(r"\d{3}", na=False)]
    for prog, tag in [(5.1, "ayudas51"), (2.0, "ayudas2")]:
        g = ay[ay["programa"] == prog].groupby("municipio")[["solicitudes", "aceptadas"]].sum()
        m[f"{tag}_solicitudes"] = m["ine"].map(g["solicitudes"]).fillna(0).astype(int)
        m[f"{tag}_aceptadas"] = m["ine"].map(g["aceptadas"]).fillna(0).astype(int)

    pop = csv("poblacion_censada_por_edad_nacionalidad_y_sexo")
    pop = pop[(pop["Tipo territorio"] == "Municipios") & (pop["Nacionalidad"] == "Total") & (pop["Sexo"] == "Total")
              & (pop["Año"] == 2022)].assign(ine=lambda d: d["Código territorio"].map(cm_to_ine))
    by_age = pop.pivot_table(index="ine", columns="Edad", values="Valor", aggfunc="sum")
    m["pob_total_2022"] = m["ine"].map(by_age["Total"])
    m["jovenes_20_34_2022"] = m["ine"].map(by_age[["De 20-24 años", "De 25-29 años", "De 30-34 años"]].sum(axis=1))
    m["jovenes_15_24_2022"] = m["ine"].map(by_age[["De 15-19 años", "De 20-24 años"]].sum(axis=1))

    renta = csv("irpf_indicador_renta")
    renta = renta[(renta["Tipo territorio"] == "Municipios") & (renta["Medida"] == "Per cápita") & (renta["Año"] == 2022)]
    m["renta_pc_2022"] = m["ine"].map(renta.assign(ine=renta["Código territorio"].map(cm_to_ine))
                                      .set_index("ine")["Valor"].pipe(pd.to_numeric, errors="coerce"))

    paro = csv("paro_registrado_edad_municipio")
    paro = paro[(paro["Año"] == 2022) & (paro["Indicador"] == "Serie") & (paro["Edad"] == "Menor de 25 años")]
    # this file writes 'Paracuellos del Jarama' / 'Berzosa de Lozoya' where the Bono file has 'de' / 'del'
    loose = lambda s: " ".join(w for w in norm(s).split() if w not in ("de", "del"))  # noqa: E731
    paro = paro.assign(key=paro["Municipio"].map(loose)).groupby("key")["Valor"].mean()
    m["paro_menor25_2022"] = m["municipio"].map(loose).map(paro)
    m["paro25_por_1000_15_24"] = 1000 * m["paro_menor25_2022"] / m["jovenes_15_24_2022"]

    ten = csv("censo_2021_viviendas_familiares_por_tenencia")
    ten = ten[ten["Tipo territorio"] == "Municipios"].assign(ine=lambda d: d["Código territorio"].map(cm_to_ine))
    ten = ten.pivot_table(index="ine", columns="Régimen", values="Valor", aggfunc="sum")
    m["hogares_alquiler_2021"] = m["ine"].map(ten["Alquiler"])
    m["hogares_total_2021"] = m["ine"].map(ten.sum(axis=1))
    m["pct_alquiler_2021"] = 100 * m["hogares_alquiler_2021"] / m["hogares_total_2021"]

    s = serpavi()["municipios"]
    for y in (2022, 2023):
        sy = s[s["year"] == y].set_index("ine")
        for c in ("n", "med", "p25", "p75"):
            m[f"serpavi_{c}_{y}"] = m["ine"].map(sy[c])
        m[f"share_above_cap_{y}"] = [share_above(c, a, z) for c, a, z in zip(m["cap"], m[f"serpavi_p25_{y}"], m[f"serpavi_p75_{y}"])]
        for cap in (600, 900):
            m[f"share_above_{cap}_{y}"] = [share_above(cap, a, z) for a, z in zip(m[f"serpavi_p25_{y}"], m[f"serpavi_p75_{y}"])]

    port = csv("alquiler_medio_mensual_viviendas_arrendadas_valor_catastral_municipios_mas_20000")
    port = port[(port["Tipo territorio"] == "Municipios") & (port["Año"] == 2023) & (port["Tipo de vivienda"] == "Viviendas habituales")]
    m["alq_medio_portal_2023"] = m["ine"].map(port.assign(ine=port["Código territorio"].map(cm_to_ine))
                                              .set_index("ine")["Valor"].pipe(pd.to_numeric, errors="coerce"))

    m = m.sort_values("ine").reset_index(drop=True)
    m.to_csv(INTERIM / "municipios.csv", index=False, encoding="utf-8")

    print(f"municipios.csv: {len(m)} municipalities x {m.shape[1]} columns | cap 900: {(m['cap'] == 900).sum()}")
    cov = m.notna().sum().rename("with value")
    print(cov[cov < len(m)].to_string())
    controls = ["serpavi_med_2022", "renta_pc_2022", "pct_alquiler_2021", "paro25_por_1000_15_24", "pob_total_2022",
                "jovenes_20_34_2022", "share_above_cap_2022"]
    sample = m.dropna(subset=controls)
    print(f"\nmunicipalities with every variable of model M1: {len(sample)} "
          f"({sample['bono_solicitudes'].sum():,} of {m['bono_solicitudes'].sum():,} Bono requests); "
          f"by cap: {sample.groupby('cap').size().to_dict()}")
    print("unmatched unemployment names:", sorted(m.loc[m["paro_menor25_2022"].isna(), "municipio"])[:10])


if __name__ == "__main__":
    main()

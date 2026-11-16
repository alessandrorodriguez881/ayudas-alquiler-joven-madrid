"""EXPLORATORY (not pre-registered; written 16-Nov-2026, BEFORE running it on the data): is the 500 EUR cap of
the Plan Estatal 2026-2030 in small municipalities a Madrid problem, or a Spanish one?

The Plan (RD 326/2026, art. 133.1.e) caps the rent at 1,000 EUR, or at 500 EUR in municipalities (and "núcleos") of
10,000 people or fewer, for every region; art. 135 lets each region raise it with up-to-date studies of the rental
supply, after agreeing it with the Ministry. In Madrid, 58 % of the 2024 rents of the small municipalities would be above
500 EUR (robustez_pueblos.py, weighted by young people). Here the same reading for all of Spain:
  - rents: SERPAVI 2024, flats (vivienda colectiva), 25th and 75th percentiles read as a log-normal, as in the rest of
    the project (comun.share_above); weights: rented flats in SERPAVI (BI_ALVHEPCO_TVC_24), because the young people
    of each municipality of Spain are not in our data
  - population: INE official figures (Revisión del Padrón) on 1-Jan-2024, one table per province (2854 to 2905)
  - "small" = 10,000 people or fewer in 2024, as in simulador.py; País Vasco and Navarra are not in SERPAVI
Written before running (16-Nov-2026, 23:18, in the commit that adds this script):
  E1  Spain: in the small municipalities with SERPAVI flat data, weighted by rented flats, the share of the rents above
      500 EUR is between 25 % and 45 %
  E2  Madrid is in the top 3 of the regions by that share, and over 50 %; the other two are Illes Balears and Catalunya
  E3  Madrid weighted by rented flats is within 5 points of the 58 % weighted by young people
  E4  SERPAVI has flat data for under half of Spain's small municipalities, but they hold over 60 % of the people who
      live in small municipalities
  E5  Spain has between 200 and 600 small municipalities where the 500 EUR cap leaves out more than half of the rent
Limits: municipal data cannot see the small "núcleos" inside bigger municipalities (also 500 EUR in the Plan); today's
caps are not the same in every region (600 EUR, and up to 900 EUR where each region decided), so "above 600 EUR" is only
a reference for today; houses (vivienda unifamiliar) are left out, as in the rest of the project.
Usage:  python -P scripts/espana_tope500.py [--descargar]   -> resultados/espana_tope500.json, data/ESPANA_TOPE500.md
        --descargar downloads the INE tables to data/raw_2026-11-16/ine_cifras_oficiales_municipios/ (52 requests)
"""
import datetime
import json
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT, share_above  # noqa: E402

INE_DIR = ROOT / "data" / "raw_2026-11-16" / "ine_cifras_oficiales_municipios"
INE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=2&tip=AM"
FIRST_TABLE = 2853  # table of province CPRO = 2853 + CPRO (2854 = Araba/Álava ... 2881 = Madrid ... 2905 = Melilla)
SERPAVI_XLSX = RAW / "serpavi_mivau" / "bd_SERPAVI_2011-2024.xlsx"
SERPAVI_CACHE = INTERIM / "serpavi_espana_municipios_2024.csv"
OUT_JSON = ROOT / "resultados" / "espana_tope500.json"
OUT_MD = ROOT / "data" / "ESPANA_TOPE500.md"
SMALL, CAP_SMALL, CAP_TODAY_REF = 10000, 500.0, 600.0
# INE province code -> region (comunidad autónoma), INE names
CCAA = {"01": "País Vasco", "20": "País Vasco", "48": "País Vasco", "31": "Navarra", "02": "Castilla-La Mancha",
        "13": "Castilla-La Mancha", "16": "Castilla-La Mancha", "19": "Castilla-La Mancha", "45": "Castilla-La Mancha",
        "03": "Comunitat Valenciana", "12": "Comunitat Valenciana", "46": "Comunitat Valenciana", "04": "Andalucía",
        "11": "Andalucía", "14": "Andalucía", "18": "Andalucía", "21": "Andalucía", "23": "Andalucía", "29": "Andalucía",
        "41": "Andalucía", "05": "Castilla y León", "09": "Castilla y León", "24": "Castilla y León",
        "34": "Castilla y León", "37": "Castilla y León", "40": "Castilla y León", "42": "Castilla y León",
        "47": "Castilla y León", "49": "Castilla y León", "06": "Extremadura", "10": "Extremadura",
        "07": "Illes Balears", "08": "Catalunya", "17": "Catalunya", "25": "Catalunya", "43": "Catalunya",
        "15": "Galicia", "27": "Galicia", "32": "Galicia", "36": "Galicia", "22": "Aragón", "44": "Aragón",
        "50": "Aragón", "26": "La Rioja", "28": "Comunidad de Madrid", "30": "Región de Murcia",
        "33": "Principado de Asturias", "35": "Canarias", "38": "Canarias", "39": "Cantabria", "51": "Ceuta",
        "52": "Melilla"}


def download():
    INE_DIR.mkdir(parents=True, exist_ok=True)
    for cpro in range(1, 53):
        t = FIRST_TABLE + cpro
        req = urllib.request.Request(INE_URL.format(t=t), headers={"User-Agent": "datamad-2026-script"})
        with urllib.request.urlopen(req, timeout=60) as r:
            (INE_DIR / f"t{t}.json").write_bytes(r.read())
        time.sleep(0.5)
    meta = {"name": "ine_cifras_oficiales_municipios", "publisher": "Instituto Nacional de Estadística (INE)",
            "title": "Cifras oficiales de población de los municipios españoles (Revisión del Padrón Municipal), "
                     "una tabla por provincia",
            "api": INE_URL.format(t="2854…2905"), "downloaded": datetime.date.today().isoformat(),
            "license": "Condiciones de uso del INE (https://www.ine.es/aviso_legal): reutilización permitida "
                       "citando la fuente", "years": "2024 y 2025 (nult=2)"}
    (INE_DIR / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def population(year=2024):
    rows = []
    for cpro in range(1, 53):
        data = json.loads((INE_DIR / f"t{FIRST_TABLE + cpro}.json").read_text(encoding="utf-8"))
        for s in data:
            md = {m["T3_Variable"]: m for m in s["MetaData"]}
            muni = next((m for k, m in md.items() if k.startswith("Municipio")), None)
            sex = next((m for k, m in md.items() if k.startswith("Sexo")), None)
            if not muni or not sex or sex["Codigo"] != "0" or len(str(muni["Codigo"])) != 5:
                continue  # province totals and men/women series
            if str(muni["Codigo"])[:2] != f"{cpro:02d}":
                raise ValueError(f"table {FIRST_TABLE + cpro} is not province {cpro:02d}: {muni}")
            val = next((d["Valor"] for d in s["Data"] if d["Anyo"] == year), None)
            rows.append({"cumun": str(muni["Codigo"]), "pob": val})
    return pd.DataFrame(rows).drop_duplicates("cumun")


def serpavi_spain():
    if SERPAVI_CACHE.exists():
        return pd.read_csv(SERPAVI_CACHE, dtype={"cpro": str, "cumun": str})
    import openpyxl
    wb = openpyxl.load_workbook(SERPAVI_XLSX, read_only=True)
    rows = wb["Municipios"].iter_rows(values_only=True)
    head = list(next(rows))
    cols = {"CPRO": "cpro", "CUMUN": "cumun", "NMUN": "municipio", "BI_ALVHEPCO_TVC_24": "n",
            "ALQTBID12_M_VC_24": "med", "ALQTBID12_25_VC_24": "p25", "ALQTBID12_75_VC_24": "p75"}
    idx = [head.index(c) for c in cols]
    df = pd.DataFrame([[r[i] for i in idx] for r in rows if r[0] is not None], columns=list(cols.values()))
    df["cpro"] = df["cpro"].astype(str).str.zfill(2)
    df["cumun"] = df["cumun"].astype(str).str.zfill(5)
    for c in ("n", "med", "p25", "p75"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.to_csv(SERPAVI_CACHE, index=False, encoding="utf-8")
    return df


def wavg(v, w):
    ok = ~(np.isnan(v) | np.isnan(w))
    return float(np.average(v[ok], weights=w[ok])) if ok.any() and w[ok].sum() > 0 else float("nan")


def main():
    if "--descargar" in sys.argv:
        download()
    pob = population(2024)
    s = serpavi_spain()
    m = pob.merge(s, on="cumun", how="left")
    m["cpro"] = m["cumun"].str[:2]
    m["ccaa"] = m["cpro"].map(CCAA)
    m["small"] = m["pob"] <= SMALL
    m["con_datos"] = m[["p25", "p75", "n"]].notna().all(axis=1) & (m["p75"] > m["p25"]) & (m["n"] > 0)
    for cap, col in ((CAP_SMALL, "sobre_500"), (CAP_TODAY_REF, "sobre_600"), (1000.0, "sobre_1000")):
        m[col] = [share_above(cap, a, z) if ok else np.nan for cap, a, z, ok in
                  zip([cap] * len(m), m["p25"], m["p75"], m["con_datos"])]
    sm = m[m["small"]]
    smd = sm[sm["con_datos"]]

    def block(d, dd):
        return {"municipios_pequenos": int(len(d)), "con_datos_serpavi": int(len(dd)),
                "habitantes_pequenos": int(d["pob"].sum()), "habitantes_con_datos": int(dd["pob"].sum()),
                "parte_habitantes_con_datos": round(float(dd["pob"].sum() / d["pob"].sum()), 3) if len(d) else None,
                "alquileres_serpavi_con_datos": int(dd["n"].sum()),
                "parte_alquiler_sobre_500": round(wavg(dd["sobre_500"].to_numpy(float), dd["n"].to_numpy(float)), 3),
                "parte_alquiler_sobre_600_referencia": round(wavg(dd["sobre_600"].to_numpy(float),
                                                                  dd["n"].to_numpy(float)), 3),
                "municipios_mas_de_la_mitad_sobre_500": int((dd["sobre_500"] > 0.5).sum()),
                "habitantes_en_ellos": int(dd.loc[dd["sobre_500"] > 0.5, "pob"].sum())}

    out = {"creado": datetime.datetime.now().isoformat(timespec="minutes"), "espana": block(sm, smd),
           "por_comunidad": {}}
    for c in sorted(m["ccaa"].dropna().unique()):
        d, dd = sm[sm["ccaa"] == c], smd[smd["ccaa"] == c]
        if len(d):
            out["por_comunidad"][c] = block(d, dd)
    ranked = sorted(((v["parte_alquiler_sobre_500"], c) for c, v in out["por_comunidad"].items()
                     if v["con_datos_serpavi"] >= 10 and not np.isnan(v["parte_alquiler_sobre_500"])), reverse=True)
    out["ranking_parte_sobre_500"] = [{"comunidad": c, "parte": p} for p, c in ranked]
    mad = smd[smd["ccaa"] == "Comunidad de Madrid"]
    out["madrid_comparacion"] = {"ponderado_por_alquileres_serpavi": round(wavg(mad["sobre_500"].to_numpy(float),
                                                                                mad["n"].to_numpy(float)), 3),
                                 "ponderado_por_jovenes_robustez_pueblos": 0.58}
    out["top_municipios_mas_poblados_sobre_500"] = (
        smd[smd["sobre_500"] > 0.5].sort_values("pob", ascending=False).head(15)
        [["cumun", "municipio", "ccaa", "pob", "sobre_500"]].round(3).to_dict("records"))
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("espana", "ranking_parte_sobre_500", "madrid_comparacion")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

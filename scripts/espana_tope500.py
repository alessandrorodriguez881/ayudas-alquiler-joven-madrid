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
        --descargar downloads the INE tables to data/raw_2026-11-16/ine_cifras_oficiales_municipios/ (52 requests, 17 MB,
        not in the repository); the population and the SERPAVI rows used are cached in data/interim/
"""
import datetime
import json
import sys
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT, share_above  # noqa: E402

INE_DIR = ROOT / "data" / "raw_2026-11-16" / "ine_cifras_oficiales_municipios"
INE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=2&tip=AM"
TABLES = range(2854, 2910)  # one table per province, not in province order (2881 = Madrid, 2901 = Córdoba);
#                             4 ids in between do not exist (404). The province is read from the codes inside
SERPAVI_XLSX = RAW / "serpavi_mivau" / "bd_SERPAVI_2011-2024.xlsx"
SERPAVI_CACHE = INTERIM / "serpavi_espana_municipios_2024.csv"  # the 71 MB workbook is not in the repository
POP_CACHE = INTERIM / "ine_poblacion_municipios_2024.csv"  # the 52 INE tables (17 MB) are not either
OUT_JSON = ROOT / "resultados" / "espana_tope500.json"
OUT_MD = ROOT / "data" / "ESPANA_TOPE500.md"
SMALL, CAP_SMALL, CAP_TODAY_REF = 10000, 500.0, 600.0
# RD 326/2026, art. 1.5: the Plan applies where the regions wish, "con excepción del País Vasco y Navarra".
# Added on 16-Nov at 23:45, AFTER seeing the results: a blind jury pointed it out and the BOE confirms it
OUTSIDE_PLAN = ("País Vasco", "Navarra")
MIN_RENTALS = 30  # as estudio_art135.py: a municipality counts as "more than half above" only with 30+ contracts
FIG = ROOT / "resultados" / "figuras" / "espana_tope500_comunidades.png"
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
    got = []
    for t in TABLES:
        req = urllib.request.Request(INE_URL.format(t=t), headers={"User-Agent": "datamad-2026-script"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                (INE_DIR / f"t{t}.json").write_bytes(r.read())
            got.append(t)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        time.sleep(0.5)
    meta = {"name": "ine_cifras_oficiales_municipios", "publisher": "Instituto Nacional de Estadística (INE)",
            "title": "Cifras oficiales de población de los municipios españoles (Revisión del Padrón Municipal), "
                     "una tabla por provincia",
            "api": INE_URL.format(t="<tabla>"), "tablas": got, "downloaded": datetime.date.today().isoformat(),
            "license": "Condiciones de uso del INE (https://www.ine.es/aviso_legal): reutilización permitida "
                       "citando la fuente", "years": "2024 y 2025 (nult=2)"}
    (INE_DIR / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path):
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("latin-1"))


def population(year=2024):
    if POP_CACHE.exists():
        return pd.read_csv(POP_CACHE, dtype={"cumun": str})
    if not any(INE_DIR.glob("t*.json")):
        download()
    rows = []
    for path in sorted(INE_DIR.glob("t*.json")):
        for s in read_json(path):
            md = {m["T3_Variable"]: m for m in s["MetaData"]}
            muni = next((m for k, m in md.items() if k.startswith("Municipio")), None)
            sex = next((m for k, m in md.items() if k.startswith("Sexo")), None)
            if not muni or not sex or sex["Codigo"] != "0" or len(str(muni["Codigo"])) != 5:
                continue  # province totals and men/women series
            val = next((d["Valor"] for d in s["Data"] if d["Anyo"] == year), None)
            rows.append({"cumun": str(muni["Codigo"]), "pob": val, "tabla": path.stem})
    df = pd.DataFrame(rows)
    provinces = set(df["cumun"].str[:2])
    if provinces != {f"{c:02d}" for c in range(1, 53)}:
        raise ValueError(f"provinces missing in the INE tables: {sorted({f'{c:02d}' for c in range(1, 53)} - provinces)}")
    if df.groupby("cumun")["pob"].nunique().max() > 1:
        raise ValueError("a municipality has two different populations")
    df = df.drop_duplicates("cumun")[["cumun", "pob"]]
    df.to_csv(POP_CACHE, index=False, encoding="utf-8")
    return df


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


def es(x, d=0):
    """Spanish number: 1.234,5"""
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def figure(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "text.color": "#0b0b0b"})
    rows = [(r["comunidad"], r["parte"]) for r in out["ranking_parte_sobre_500"]][::-1]
    fig, ax = plt.subplots(figsize=(7.2, 5.6), dpi=200)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for i, (c, v) in enumerate(rows):
        mad = c == "Comunidad de Madrid"
        ax.barh(i, 100 * v, height=0.66, color="#184f95" if mad else "#9ec5f4", edgecolor="#fcfcfb", linewidth=2)
        ax.text(100 * v + 0.8, i, f"{es(100 * v)} %", va="center", fontsize=8.5, zorder=3,
                color="#0b0b0b" if mad else "#52514e", fontweight="bold" if mad else "normal",
                bbox={"facecolor": "#fcfcfb", "edgecolor": "none", "pad": 0.6})
    spain = 100 * out["espana"]["parte_alquiler_sobre_500"]
    ax.axvline(spain, color="#898781", linestyle=(0, (3, 3)), linewidth=1)
    ax.text(spain + 0.6, len(rows) - 0.4, f"España: {es(spain)} %", fontsize=8, color="#52514e", va="bottom")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=8.5)
    for lab in ax.get_yticklabels():
        if lab.get_text() == "Comunidad de Madrid":
            lab.set_fontweight("bold")
    ax.set_xlim(0, 100)
    ax.set_xlabel("% del alquiler de 2024 por encima de 500 €", color="#52514e", fontsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors="#52514e")
    fig.suptitle("Con el tope del Plan (500 €), qué parte del alquiler de los pueblos\nquedaría fuera, por comunidad "
                 "donde se aplica el Plan",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, "Municipios de 10.000 habitantes o menos (INE, 2024) con datos de pisos del SERPAVI (MIVAU) "
             "de 2024, ponderados por pisos alquilados. Sin el País Vasco ni Navarra:\nel Plan no se aplica allí "
             "(RD 326/2026, art. 1.5). Percentiles 25 y 75 leídos como log-normal, como en el resto del proyecto. "
             "Cálculo propio.", fontsize=7, color="#898781", ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    fig.savefig(FIG, facecolor=fig.get_facecolor())
    plt.close(fig)


def expectations(out):
    e, rank = out["espana"], [r["comunidad"] for r in out["ranking_parte_sobre_500"]]
    e17, rank17 = out["espana_17_comunidades"], [r["comunidad"] for r in out["ranking_17_comunidades"]]
    mad = out["por_comunidad"]["Comunidad de Madrid"]
    ok = lambda c: "✅" if c else "❌"  # noqa: E731
    return [
        "- **Ojo:** las expectativas se escribieron para «toda España». Después de ver los resultados, un jurado ciego "
        "avisó de que el Plan no se aplica en el País Vasco ni en Navarra (RD 326/2026, art. 1.5), y así es. Cada "
        "expectativa se mide con las comunidades donde se aplica el Plan, y entre paréntesis, con las 17",
        f"- **E1** (España, del 25 % al 45 %): {es(100 * e['parte_alquiler_sobre_500'])} % → "
        f"{ok(0.25 <= e['parte_alquiler_sobre_500'] <= 0.45)} (con las 17: {es(100 * e17['parte_alquiler_sobre_500'])} %)",
        f"- **E2** (Madrid entre las 3 primeras y por encima del 50 %; las otras dos, Illes Balears y Catalunya): "
        f"Madrid es la {rank.index('Comunidad de Madrid') + 1}.ª, con el {es(100 * mad['parte_alquiler_sobre_500'])} % → "
        f"{ok('Comunidad de Madrid' in rank[:3] and mad['parte_alquiler_sobre_500'] > 0.5)}. Las tres primeras son "
        f"{', '.join(rank[:3])} → {ok(set(rank[:3]) == {'Comunidad de Madrid', 'Illes Balears', 'Catalunya'})}. "
        f"Con las 17, las tres primeras son {', '.join(rank17[:3])} y Madrid es la "
        f"{rank17.index('Comunidad de Madrid') + 1}.ª: suponía que el SERPAVI no tenía el País Vasco ni Navarra, y sí "
        "los tiene; acierta solo porque el Plan no se aplica allí",
        f"- **E3** (Madrid, a menos de 5 puntos del 58 %): "
        f"{es(100 * out['madrid_comparacion']['ponderado_por_alquileres_serpavi'], 1)} % → "
        f"{ok(abs(out['madrid_comparacion']['ponderado_por_alquileres_serpavi'] - 0.58) <= 0.05)}",
        f"- **E4** (datos en menos de la mitad de los municipios pequeños, donde vive más del 60 % de su gente): "
        f"{es(e['con_datos_serpavi'])} de {es(e['municipios_pequenos'])}, con el "
        f"{es(100 * e['parte_habitantes_con_datos'])} % → "
        f"{ok(e['con_datos_serpavi'] < e['municipios_pequenos'] / 2 and e['parte_habitantes_con_datos'] > 0.6)}",
        f"- **E5** (de 200 a 600 municipios con más de la mitad fuera): {es(e['municipios_mas_de_la_mitad_sobre_500'])} "
        f"con {MIN_RENTALS} contratos o más, y {es(e['municipios_mas_de_la_mitad_sin_minimo_de_contratos'])} sin mínimo "
        f"→ {ok(200 <= e['municipios_mas_de_la_mitad_sobre_500'] <= 600)} (con las 17: "
        f"{es(e17['municipios_mas_de_la_mitad_sobre_500'])})"]


def write_md(out):
    e, m = out["espana"], out["por_comunidad"]["Comunidad de Madrid"]
    rank = [r["comunidad"] for r in out["ranking_parte_sobre_500"]]
    i_mad = rank.index("Comunidad de Madrid")
    lines = [
        "# El tope de 500 € del Plan, en toda España (exploratorio)", "",
        f"> Hecho con `scripts/espana_tope500.py` el {out['creado'][:10]}. Lo esperado (E1 a E5) se escribió en la "
        "cabecera del script antes de ejecutarlo, en el commit que lo añade. No está preregistrado.", "",
        "## La pregunta",
        "El Plan Estatal 2026-2030 (RD 326/2026, art. 133.1.e) pone el tope del alquiler en 500 € en los municipios de "
        "10.000 habitantes o menos, en todas las comunidades donde se aplica: todas menos el País Vasco y Navarra "
        "(art. 1.5). En Madrid quedaría por encima el 58 % del alquiler de esos municipios (ponderado por jóvenes). "
        "¿Pasa solo en Madrid?", "",
        "## Cómo",
        "- **Alquiler:** SERPAVI 2024 (MIVAU), pisos (vivienda colectiva), con los percentiles 25 y 75 leídos como una "
        "log-normal, igual que en el resto del proyecto (`scripts/comun.py`, `share_above`)",
        "- **Población:** cifras oficiales del INE a 1-ene-2024 (Revisión del Padrón), una tabla por provincia, en "
        "`data/raw_2026-11-16/ine_cifras_oficiales_municipios/`",
        "- **Pesos:** los pisos alquilados del SERPAVI, porque no tenemos los jóvenes de cada municipio de España. Por eso "
        f"Madrid da aquí un {es(100 * out['madrid_comparacion']['ponderado_por_alquileres_serpavi'])} % y no el 58 %, "
        "que se pondera por jóvenes",
        f"- **«Más de la mitad fuera»:** solo cuenta en municipios con al menos {MIN_RENTALS} contratos en el SERPAVI, "
        f"como en la base del estudio del art. 135. Con esa regla, Madrid da {m['municipios_mas_de_la_mitad_sobre_500']}, "
        "los mismos que `data/ESTUDIO_ART135.md`", "",
        "## Resultados",
        f"- **España, donde se aplica el Plan:** en los {es(e['con_datos_serpavi'])} municipios pequeños con datos del SERPAVI (de "
        f"{es(e['municipios_pequenos'])}; en ellos vive el {es(100 * e['parte_habitantes_con_datos'])} % de la gente de "
        f"los municipios pequeños), quedaría por encima de 500 € el {es(100 * e['parte_alquiler_sobre_500'])} % del "
        f"alquiler (por encima de 600 €, el {es(100 * e['parte_alquiler_sobre_600_referencia'])} %)",
        f"- **En {es(e['municipios_mas_de_la_mitad_sobre_500'])} municipios pequeños, donde viven "
        f"{es(e['habitantes_en_ellos'])} personas, el tope de 500 € dejaría fuera más de la mitad del alquiler**",
        f"- **Madrid es la {i_mad + 1}.ª de las {len(rank)} comunidades con 10 municipios pequeños con datos o más** donde más alquiler de sus pueblos queda por "
        f"encima: el {es(100 * m['parte_alquiler_sobre_500'])} %, después de {' y '.join(rank[:i_mad])}",
        f"- **Con el País Vasco y Navarra** (no se aplica allí el Plan): {es(out['espana_17_comunidades']['municipios_mas_de_la_mitad_sobre_500'])} "
        f"municipios y {es(out['espana_17_comunidades']['habitantes_en_ellos'])} personas, y Madrid sería la "
        f"{[r['comunidad'] for r in out['ranking_17_comunidades']].index('Comunidad de Madrid') + 1}.ª. Al principio "
        "los conté: lo corregí la misma noche, después de ver los resultados, cuando un jurado ciego avisó del art. 1.5",
        "",
        "| Comunidad | Municipios pequeños | Con datos | Gente que vive en los que tienen datos | Alquiler por encima "
        "de 500 € | Por encima de 600 € (referencia) | Municipios con más de la mitad fuera | Habitantes en ellos |",
        "|---|---|---|---|---|---|---|---|"]
    ranked = [r["comunidad"] for r in out["ranking_parte_sobre_500"]]
    few = [c for c in out["por_comunidad"] if c not in ranked and c not in OUTSIDE_PLAN]
    for c in ranked + few + list(OUTSIDE_PLAN):
        v = out["por_comunidad"][c]
        name = c + (" (fuera del Plan)" if c in OUTSIDE_PLAN else " (menos de 10 municipios con datos: fuera del orden)"
                    if c in few else "")
        lines.append(f"| {name} | {es(v['municipios_pequenos'])} | {es(v['con_datos_serpavi'])} | "
                     f"{es(100 * v['parte_habitantes_con_datos'])} % | {es(100 * v['parte_alquiler_sobre_500'])} % | "
                     f"{es(100 * v['parte_alquiler_sobre_600_referencia'])} % | "
                     f"{es(v['municipios_mas_de_la_mitad_sobre_500'])} | {es(v['habitantes_en_ellos'])} |")
    lines += ["", f"![Por comunidad](../resultados/figuras/{FIG.name})", "",
              "## Lo esperado, frente a lo que salió", *out["esperado"], "",
              "## Límites",
              "- Los datos municipales no ven los núcleos pequeños dentro de municipios mayores, que en el Plan también "
              "tienen el tope de 500 €",
              "- El tope de hoy no es igual en todas las comunidades (600 €, y hasta 900 € donde cada una lo decidió), "
              "así que «por encima de 600 €» es solo una referencia",
              "- Solo pisos: las casas (vivienda unifamiliar) quedan fuera, como en el resto del proyecto",
              "- El SERPAVI tiene datos de una cuarta parte de los municipios pequeños, pero en ellos vive la mayor parte "
              "de su gente. Los que no tienen datos suelen ser los más pequeños",
              "- Solo mide el alquiler frente al tope: no dice nada de las solicitudes ni de los jóvenes de otras "
              "comunidades"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
                "municipios_mas_de_la_mitad_sobre_500": int(((dd["sobre_500"] > 0.5) & (dd["n"] >= MIN_RENTALS)).sum()),
                "habitantes_en_ellos": int(dd.loc[(dd["sobre_500"] > 0.5) & (dd["n"] >= MIN_RENTALS), "pob"].sum()),
                "municipios_mas_de_la_mitad_sin_minimo_de_contratos": int((dd["sobre_500"] > 0.5).sum())}

    inplan, inplan_d = ~sm["ccaa"].isin(OUTSIDE_PLAN), ~smd["ccaa"].isin(OUTSIDE_PLAN)
    out = {"creado": datetime.datetime.now().isoformat(timespec="minutes"),
           "ambito": "comunidades donde se aplica el Plan: todas menos el País Vasco y Navarra (RD 326/2026, art. 1.5)",
           "espana": block(sm[inplan], smd[inplan_d]), "espana_17_comunidades": block(sm, smd), "por_comunidad": {}}
    for c in sorted(m["ccaa"].dropna().unique()):
        d, dd = sm[sm["ccaa"] == c], smd[smd["ccaa"] == c]
        if len(d):
            out["por_comunidad"][c] = block(d, dd)
    ranked = sorted(((v["parte_alquiler_sobre_500"], c) for c, v in out["por_comunidad"].items()
                     if v["con_datos_serpavi"] >= 10 and not np.isnan(v["parte_alquiler_sobre_500"])), reverse=True)
    out["ranking_parte_sobre_500"] = [{"comunidad": c, "parte": p} for p, c in ranked if c not in OUTSIDE_PLAN]
    out["ranking_17_comunidades"] = [{"comunidad": c, "parte": p} for p, c in ranked]
    mad = smd[smd["ccaa"] == "Comunidad de Madrid"]
    out["madrid_comparacion"] = {"ponderado_por_alquileres_serpavi": round(wavg(mad["sobre_500"].to_numpy(float),
                                                                                mad["n"].to_numpy(float)), 3),
                                 "ponderado_por_jovenes_robustez_pueblos": 0.58}
    out["top_municipios_mas_poblados_sobre_500"] = (
        smd[(smd["sobre_500"] > 0.5) & inplan_d].sort_values("pob", ascending=False).head(15)
        [["cumun", "municipio", "ccaa", "pob", "sobre_500"]].round(3).to_dict("records"))
    out["esperado"] = expectations(out)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    figure(out)
    write_md(out)
    print(json.dumps({k: out[k] for k in ("espana", "ranking_parte_sobre_500", "madrid_comparacion")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

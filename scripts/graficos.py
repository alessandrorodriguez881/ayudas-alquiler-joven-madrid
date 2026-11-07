"""Figures for the report and the slides (development period, after the pre-registered test), and the municipal map
for the app.

  resultados/figuras/contraste_todas_las_pruebas.png    every estimate of the cap effect, the ones that failed included
  resultados/figuras/brecha_2022_2024.png               share of the rental market above the cap: 2022, 2024, Plan
                                                        2026-2030 (1,000 / 500 EUR) and the proposal
  resultados/figuras/reparto_por_necesidad.png          bonos per 1,000 young people by need group, simulated rules
  resultados/figuras/cuadrante_necesidad_cobertura.png  need 2024 against Bono 2022 coverage: underserved municipalities
  resultados/figuras/mapa_necesidad_cobertura.png       the same two measures as maps (for the app more than the slides)
  resultados/infraatendidos.json                        the underserved municipalities of the scatter
  data/interim/municipios_wgs84.geojson                 179 municipalities (Madrid city: its 21 districts as one feature)
Coverage = Bono 2022 accepted per 1,000 young people 20-34 (2022), only where there are at least MIN_YOUNG of them (the
rate of a village with 1 or 2 bonos is noise); the acceptance rate alone misleads (it depends on when the money ran
out). Underserved = top need tercile and coverage below the rest of the Comunidad (Madrid city, 54 % of the young
people, would set the bar on its own).
Boundaries: «Municipios y Distritos de Madrid (2020)», shapefile of the Comunidad de Madrid portal (dataset
covid19_tia_muni_y_distritos, CC BY 4.0), ETRS89 / UTM 30N; downloaded once to data/raw_2026-11-07/.
Colours: reference palette of the dataviz method (light surface); one hue per sequential measure.
Usage:  python -P scripts/graficos.py   (run exploratorio_topes_falsos.py, necesidad_2024.py and simulador.py first)
"""
import io
import json
import math
import pathlib
import sys
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shapefile  # noqa: E402  (pyshp)
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from pyproj import Transformer  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, ROOT  # noqa: E402
from descargar import API, get  # noqa: E402

GEO_DS = "covid19_tia_muni_y_distritos"
GEO_ZIP = ROOT / "data" / "raw_2026-11-07" / GEO_DS / "municipios_y_distritos_madrid_20.zip"
GEO_URL = ("https://datos.comunidad.madrid/dataset/6c63b14c-9f5d-414f-958f-b8a9c53d69fc/resource/"
           "3f4435b7-ecdb-4c1e-961a-dd55506c2e10/download/municipios_y_distritos_madrid_20.zip")
FIG = ROOT / "resultados" / "figuras"
MIN_YOUNG = 500
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # steps 100-700, every 100
ORANGE = ["#fde4d8", "#f9c2a8", "#f39a74", "#eb6834", "#c94f1f", "#9c3c17", "#6e2a10"]  # one-hue ramp on slot 2
SLOT1, SLOT2, SLOT3 = "#2a78d6", "#eb6834", "#1baf7a"  # first three categorical slots (validated all-pairs)
ORDINAL = ["#86b6ef", "#2a78d6", "#104281"]  # blue steps 250 / 450 / 650: ordered classes (validated with --ordinal)
SOURCE = "Fuente: Comunidad de Madrid (portal de datos abiertos) y SERPAVI (MIVAU). Cálculo propio."
RULES = {"actual_2024_55": "Actual: 600 / 900 €\npor orden de llegada",
         "plan_o_p75_local": "Plan + p75 local, sin límite\npor orden de llegada",
         "plan_p75_hasta_1000": "Plan + p75 local, hasta 1.000 €\npor orden de llegada",
         "necesidad_plan_p75_hasta_1000": "Plan + p75 local, hasta 1.000 €\ncupos por jóvenes × necesidad",
         "necesidad_requisito_plan_p75_hasta_1000": "Propuesta: plan + p75 hasta 1.000 €\ncupos por jóvenes × necesidad\n× parte bajo el límite de ingresos"}
GROUPS = [("Madrid capital", "Madrid capital", MUTED), ("resto, necesidad alta", "Resto: necesidad alta", ORDINAL[2]),
          ("resto, necesidad media", "Resto: necesidad media", ORDINAL[1]),
          ("resto, necesidad baja", "Resto: necesidad baja", ORDINAL[0])]

plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "text.color": INK,
                     "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def es(v, d=1):
    """Spanish decimal comma."""
    return f"{v:.{d}f}".replace(".", ",")


def thousands(v):
    return f"{v:,.0f}".replace(",", ".")


def boundaries():
    """Municipal polygons (UTM 30N) by INE code; Madrid city's 21 districts all map to 079."""
    if not GEO_ZIP.exists():
        GEO_ZIP.parent.mkdir(parents=True, exist_ok=True)
        meta = json.loads(get(API + GEO_DS))["result"]
        keep = {k: meta.get(k) for k in ("name", "title", "license_title", "license_url", "metadata_modified")}
        keep["portal_url"] = f"https://datos.comunidad.madrid/dataset/{GEO_DS}"
        keep["resource"] = GEO_URL
        (GEO_ZIP.parent / "metadata.json").write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
        GEO_ZIP.write_bytes(get(GEO_URL))
    z = zipfile.ZipFile(GEO_ZIP)
    base = "municipios_y_distritos_madrid"
    r = shapefile.Reader(**{k: io.BytesIO(z.read(f"{base}.{k}")) for k in ("shp", "shx", "dbf")}, encoding="latin-1")
    shapes = {}
    for sr in r.iterShapeRecords():
        shapes.setdefault(sr.record["codigo_geo"][:3], []).append(sr.shape)  # '0072' -> '007'; '079603' -> '079'
    return shapes


def path_of(shapes):
    """One compound path per municipality (holes stay holes: shapefile rings wind the opposite way)."""
    verts, codes = [], []
    for s in shapes:
        for a, b in zip(s.parts, list(s.parts[1:]) + [len(s.points)]):
            ring = s.points[a:b]
            verts += ring + [ring[0]]
            codes += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 1) + [Path.CLOSEPOLY]
    return Path(verts, codes)


def outline(shapes):
    """Outer boundary of a group of polygons: the edges that only one of them uses (shared edges cancel out)."""
    count = {}
    for s in shapes:
        pts = [tuple(np.round(q, 1)) for q in s.points]
        for a, b in zip(pts[:-1], pts[1:]):
            if a != b:
                k = (min(a, b), max(a, b))
                count[k] = count.get(k, 0) + 1
    return [list(k) for k, n in count.items() if n == 1]


def geojson(shapes, out):
    """WGS84 GeoJSON for the app: 4 decimals (about 10 m), consecutive repeats dropped."""
    to_wgs = Transformer.from_crs(25830, 4326, always_xy=True)

    def ring(pts):
        x, y = to_wgs.transform(*np.array(pts).T)
        r = np.round(np.c_[x, y], 4)
        keep = np.r_[True, (np.diff(r, axis=0) != 0).any(axis=1)]
        return r[keep].tolist()

    feats = []
    for ine, ss in sorted(shapes.items()):
        polys = []
        for s in ss:
            g = s.__geo_interface__
            for p in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
                polys.append([ring(rg) for rg in p])
        feats.append({"type": "Feature", "id": ine, "properties": {"ine": ine},
                      "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")), encoding="utf-8")
    return len(feats)


def note(fig, text, y=0.01):
    fig.text(0.01, y, text, fontsize=7.5, color=MUTED, ha="left", va="bottom")


def title(fig, text, size=12.5):
    fig.suptitle(text, x=0.01, ha="left", fontsize=size, fontweight="bold")


def tests_chart(test, explo):
    """Forest plot: % change in requests per +10 points of market above the cap, in every specification."""
    pct = lambda b: 100 * (math.exp(0.1 * b) - 1)  # noqa: E731  (share is 0-1, so +10 points = +0.1)
    rob = test["robustness_beta"]
    rows = [("H1: contraste preregistrado (132 municipios)", test["H1"]["beta"], test["H1"]["ci95"], "pre"),
            ("H1 sin Madrid capital", test["H1"]["beta_without_madrid"], None, "pre"),
            ("R1: Ayudas al alquiler 2022 (mismos topes)", test["R1_ayudas51"]["beta"], test["R1_ayudas51"]["ci95"], "pre"),
            ("Binomial negativa", rob["negative_binomial"], None, "pre"),
            ("Por hogar de alquiler", rob["per_rented_household"], None, "pre"),
            ("Alquileres del SERPAVI de 2023", rob["serpavi_2023"], None, "pre"),
            (f"Alquiler del portal ({rob['portal_rent_over_20k']['n']} de más de 20.000 hab.)",
             rob["portal_rent_over_20k"]["beta"], None, "pre"),
            (f"Solo con 1.000 jóvenes o más ({rob['young_at_least_1000']['n']})", rob["young_at_least_1000"]["beta"],
             None, "pre"),
            ("Exploratorio: con un umbral de 900 € igual para todos\n(solo la parte del tope; β central del simulador)",
             explo["real_cap_and_uniform_900"]["real_cap"]["beta"], explo["real_cap_and_uniform_900"]["real_cap"]["ci95"],
             "exp")]
    fig, ax = plt.subplots(figsize=(8, 5.0))
    for i, (label, b, ci, kind) in enumerate(rows):
        colour = SLOT1 if kind == "pre" else MUTED
        if ci:
            ax.plot([pct(ci[0]), pct(ci[1])], [i, i], color=colour, linewidth=2, solid_capstyle="round")
        ax.plot(pct(b), i, "o", color=colour, markersize=8, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(pct(b), i - 0.32, f"{es(pct(b))} %", ha="center", fontsize=7.5, color=INK2)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], color=INK, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_ylim(len(rows) - 0.4, -0.8)
    ax.set_xlim(-13, 2)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Cambio en las solicitudes por cada 10 puntos más de mercado por encima del tope (%)")
    dot = lambda c: Line2D([], [], marker="o", color=c, markersize=7, linewidth=2)  # noqa: E731
    ax.legend([dot(SLOT1), dot(MUTED)], ["Preregistrado (línea: intervalo del 95 %)", "Exploratorio, hecho después"],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=8.5, labelcolor=INK2)
    title(fig, "En todas las variantes, más mercado por encima del tope = menos solicitudes")
    h2 = test["H2"]
    note(fig, "Lo que no salió: con topes falsos (600 o 900 € para todos) el modelo ajusta mejor que con el tope real, así "
              "que el alquiler caro\ntambién frena por sí solo; y el experimento natural (H2) va en la misma dirección "
              f"(razón {es(h2['rate_ratio_cap600'], 2)}) pero su intervalo ({es(h2['ci95'][0], 2)} a "
              f"{es(h2['ci95'][1], 2)}) incluye el «sin efecto».\nPreregistro, resultados y código: PREREGISTRO.md, "
              "resultados/contraste_real.json, scripts/contraste.py.")
    fig.tight_layout(rect=(0, 0.09, 1, 0.97))
    fig.savefig(FIG / "contraste_todas_las_pruebas.png", dpi=200)
    plt.close(fig)


def gap_chart(gap):
    rows = [("all", "Toda la Comunidad"), ("madrid_city", "Madrid capital"),
            ("over_10000_without_madrid", "Resto, más de 10.000 hab."), ("10000_or_fewer", "10.000 hab. o menos")]
    bars = [("2022_rents_2022_list", "2022: 600 / 900 € (lista de 29)", MUTED),
            ("2024_rents_2024_list", "2024: 600 / 900 € (lista de 55, la actual)", SLOT1),
            ("2024_rents_plan_estatal", "Plan 2026-2030: 1.000 €, o 500 € en los pequeños", SLOT2),
            ("2024_rents_plan_p75_hasta_1000", "Propuesta: subir hasta el p75 local, máx. 1.000 €", SLOT3)]
    fig, ax = plt.subplots(figsize=(8, 5.0))
    h = 0.2
    for j, (key, label, colour) in enumerate(bars):
        y = np.arange(len(rows)) + (j - 1.5) * h
        v = [100 * gap[key][r] for r, _ in rows]
        ax.barh(y, v, height=h - 0.03, color=colour, label=label)
        for yi, vi in zip(y, v):
            ax.text(vi + 0.8, yi, f"{vi:.0f} %", va="center", fontsize=8, color=INK2)
    ax.set_yticks(range(len(rows)), [r[1] for r in rows], color=INK, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 65)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("% del mercado de alquiler por encima del tope del Bono (ponderado por jóvenes de 20 a 34 años)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=8, labelcolor=INK2)
    small = gap["municipalities_10000_or_fewer"]
    title(fig, f"El Plan 2026-2030 alivia las ciudades, pero en los pueblos deja fuera el "
               f"{100 * gap['2024_rents_plan_estatal']['10000_or_fewer']:.0f} % del alquiler", size=12)
    note(fig, SOURCE + "\nReparto log-normal entre los percentiles 25 y 75 del SERPAVI (2022 para 2022; 2024 para lo "
                       "demás). Plan Estatal 2026-2030: RD 326/2026, art. 133.1.e.\nEl tope de 500 € también vale para "
                       "núcleos pequeños dentro de municipios grandes, que aquí no se ven. "
                       f"Municipios de 10.000 habitantes o menos con datos: {small['n']}, con "
                       f"{thousands(small['young_2024'])} jóvenes de 20 a 34 años.")
    fig.tight_layout(rect=(0, 0.09, 1, 0.97))
    fig.savefig(FIG / "brecha_2022_2024.png", dpi=200)
    plt.close(fig)


def allocation_chart(sim):
    fig, ax = plt.subplots(figsize=(8, 6.6))
    h = 0.2
    for j, (key, label, colour) in enumerate(GROUPS):
        y = np.arange(len(RULES)) + (j - 1.5) * h
        v = [sim["rules"][r]["central"]["bonos_per_1000_young_by_group"][key] for r in RULES]
        ax.barh(y, v, height=h - 0.03, color=colour, label=label)
        for yi, vi in zip(y, v):
            ax.text(vi + 0.06, yi, es(vi), va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(RULES)), list(RULES.values()), color=INK, fontsize=8.5)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Bonos por cada 1.000 jóvenes de 20 a 34 años (simulación con los 5.300 bonos de 31,8 M€)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=8, labelcolor=INK2)
    by = lambda r: sim["rules"][r]["central"]["bonos_per_1000_young_by_group"]["resto, necesidad alta"]  # noqa: E731
    title(fig, f"Con cupos por necesidad, el resto con más necesidad pasa de {es(by('actual_2024_55'))} a "
               f"{es(by('necesidad_requisito_plan_p75_hasta_1000'))} bonos por cada 1.000 jóvenes", size=11.5)
    young = sim["young_by_group"]
    note(fig, "Simulación propia (scripts/simulador.py): demanda del Bono 2022 por municipio y β = "
              f"{es(sim['betas']['central'], 2)} (solo la parte del tope). Fuera de Madrid capital ("
              f"{thousands(young['Madrid capital'])} jóvenes),\nlos municipios se agrupan en tres tercios de jóvenes "
              "por su índice de necesidad 2024. Plan: 1.000 €, o 500 € en municipios de 10.000 habitantes o menos.\n"
              "Límite de ingresos: parte de las declaraciones del IRPF 2024 con base imponible de hasta 3 × IPREM (25.200 €), de todas las edades.\n"
              "Con cupos, el tope no cambia el reparto: solo cuánta gente pide cada bono.")
    fig.tight_layout(rect=(0, 0.09, 1, 0.97))
    fig.savefig(FIG / "reparto_por_necesidad.png", dpi=200)
    plt.close(fig)


def choropleth(ax, paths, madrid_edge, values, bins, colours, title_, unit):
    cmap, norm = ListedColormap(colours), BoundaryNorm(bins, len(colours))
    for ine, p in paths.items():
        v = values.get(ine, np.nan)
        face = GRID if pd.isna(v) else cmap(norm(v))
        edge = face if ine == "079" else SURFACE  # Madrid city comes as 21 districts: hide the lines between them
        ax.add_patch(PathPatch(p, facecolor=face, edgecolor=edge, linewidth=0.35, hatch="////" if pd.isna(v) else None))
    ax.add_collection(LineCollection(madrid_edge, colors=INK, linewidths=0.9))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title_, loc="left", fontsize=10.5, color=INK, fontweight="bold")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cb = plt.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04, pad=0.02, spacing="uniform")
    cb.set_label(unit, color=INK2, fontsize=8.5)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, color=AXIS, labelcolor=INK2)


def need_coverage_map(t, shapes):
    paths = {ine: path_of(ss) for ine, ss in shapes.items()}
    madrid_edge = outline(shapes["079"])
    need = t.set_index("ine")["indice_necesidad"].to_dict()
    cov = t.set_index("ine")["cobertura_2022"].to_dict()
    fig, axes = plt.subplots(1, 2, figsize=(10, 6.4))
    choropleth(axes[0], paths, madrid_edge, need, [0, 30, 40, 50, 60, 70, 80, 100], BLUE, "Necesidad (2024)",
               "Índice de 0 a 100")
    top = max(20, math.ceil(max(v for v in cov.values() if pd.notna(v))))  # last class reaches the real maximum
    choropleth(axes[1], paths, madrid_edge, cov, [0, 2, 4, 6, 8, 10, 12, top], ORANGE, "Cobertura del Bono 2022",
               "Bonos concedidos por cada 1.000 jóvenes de 20 a 34 años")
    title(fig, "¿Llega el Bono a donde más se necesita?")
    note(fig, SOURCE + f" Rayado: sin dato, o cobertura con menos de {MIN_YOUNG} jóvenes (tasa poco fiable). "
                       "Contorno negro: Madrid capital.\nLímites: «Municipios y Distritos de Madrid (2020)», portal de "
                       "datos abiertos de la Comunidad de Madrid (CC BY 4.0).")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(FIG / "mapa_necesidad_cobertura.png", dpi=200)
    plt.close(fig)


def spread(labels, gap=0.75, lo=0.4, hi=25.5, near=18):
    """Move label heights apart (only labels that would share a line) so that none sits on top of another."""
    ys = np.array([y for _, _, y in labels], dtype=float)
    xs = np.array([x for _, x, _ in labels], dtype=float)
    for _ in range(200):
        moved = False
        for i in range(len(ys)):
            for j in range(i + 1, len(ys)):
                d = ys[i] - ys[j]
                if abs(xs[i] - xs[j]) < near and abs(d) < gap:
                    push = (gap - abs(d)) / 2 * (1 if d >= 0 else -1)
                    ys[i] += push
                    ys[j] -= push
                    moved = True
        ys = np.clip(ys, lo, hi)
        if not moved:
            break
    return ys


def quadrant(t):
    d = t.dropna(subset=["indice_necesidad", "cobertura_2022"]).copy()
    rest = d[d["ine"] != "079"]
    ref = 1000 * rest["bono_aceptadas"].sum() / rest["jovenes_20_34_2022"].sum()
    d["infraatendido"] = (d["tercil_necesidad"] == "alta") & (d["cobertura_2022"] < ref)
    fig, ax = plt.subplots(figsize=(8, 5.6))
    size = 8 + 600 * np.sqrt(d["jovenes_20_34_2024"] / d["jovenes_20_34_2024"].max())
    for flag, colour, z in ((False, AXIS, 2), (True, SLOT1, 3)):
        s = d[d["infraatendido"] == flag]
        ax.scatter(s["indice_necesidad"], s["cobertura_2022"], s=size[s.index], color=colour, alpha=0.85,
                   edgecolor=SURFACE, linewidth=1, zorder=z)
    up = d[d["infraatendido"] & (d["sube_a_900_en_2024"] == True)]  # noqa: E712  (column may hold NaN)
    ax.scatter(up["indice_necesidad"], up["cobertura_2022"], s=size[up.index] + 40, facecolor="none", edgecolor=INK,
               linewidth=0.9, zorder=4)
    cut = d.loc[d["tercil_necesidad"] == "alta", "indice_necesidad"].min()
    ax.axvline(cut, color=AXIS, linewidth=0.8)
    ax.axhline(ref, color=AXIS, linewidth=0.8)
    ax.text(1, ref + 0.3, f"Resto de la Comunidad (sin Madrid capital): {es(ref)}", ha="left", va="bottom", fontsize=8,
            color=INK2)
    ax.text(cut + 0.8, 19.5, "Tercio con más necesidad →", ha="left", va="top", fontsize=8, color=INK2)
    big = d[d["infraatendido"] & (d["jovenes_20_34_2024"] >= 2000)]
    labels = [(r["municipio"], r["indice_necesidad"], r["cobertura_2022"]) for _, r in big.iterrows()]
    # one column of names to the right, in the same order as the points, so the leader lines do not cross
    for (name, x, y), ly in zip(labels, spread(labels, near=1000, hi=19)):
        ax.annotate(name, (x, y), xytext=(86, ly), textcoords="data", fontsize=7.5, color=INK2, va="center",
                    arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 0.6, "shrinkA": 0, "shrinkB": 4})
    mad = d[d["ine"] == "079"].iloc[0]
    ax.annotate("Madrid capital", (mad["indice_necesidad"], mad["cobertura_2022"]), xytext=(8, 8),
                textcoords="offset points", fontsize=7.5, color=INK2)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.set_yticks([0, 5, 10, 15, 20])
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Índice de necesidad 2024 (0-100)")
    ax.set_ylabel("Bonos 2022 concedidos por cada 1.000 jóvenes")
    dot = lambda c, **k: Line2D([], [], marker="o", linestyle="", markersize=7, color=c, **k)  # noqa: E731
    ax.legend([dot(SLOT1), dot(AXIS), dot("none", markeredgecolor=INK)],
              ["Necesidad alta y cobertura por debajo del resto", "Resto de municipios",
               "Subió de 600 a 900 € en 2024"], loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK2)
    title(fig, "Municipios infraatendidos en 2022: mucha necesidad y poco Bono")
    note(fig, SOURCE + f" Solo municipios con {MIN_YOUNG} jóvenes o más.\nTamaño del punto: jóvenes de 20 a 34 años "
                       "(2024). Con nombre, los infraatendidos con 2.000 jóvenes o más; la lista completa está en "
                       "resultados/infraatendidos.json.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(FIG / "cuadrante_necesidad_cobertura.png", dpi=200)
    plt.close(fig)
    cols = ["ine", "municipio", "indice_necesidad", "cobertura_2022", "bono_aceptadas", "jovenes_20_34_2024",
            "tope_2022", "tope_2024"]
    under = d[d["infraatendido"]].sort_values("jovenes_20_34_2024", ascending=False)[cols].round(2)
    return {"coverage_rest_without_madrid_per_1000": round(ref, 2),
            "coverage_madrid_city_per_1000": round(float(mad["cobertura_2022"]), 2),
            "need_cut_top_tercile": round(float(cut), 1), "min_young_2022": MIN_YOUNG,
            "n": len(under), "young_2024": int(under["jovenes_20_34_2024"].sum()),
            "n_cap_900_already_2022": int((under["tope_2022"] == 900).sum()),
            "n_moved_to_900_in_2024": int(((under["tope_2022"] == 600) & (under["tope_2024"] == 900)).sum()),
            "municipalities": under.to_dict("records")}


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    for old in ("brecha_2022_2024.png", "reparto_por_necesidad.png"):  # regenerated below; nothing stale stays
        (FIG / old).unlink(missing_ok=True)
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    t["cobertura_2022"] = 1000 * t["bono_aceptadas"] / t["jovenes_20_34_2022"].where(t["jovenes_20_34_2022"] >= MIN_YOUNG)
    res = ROOT / "resultados"
    sim = json.loads((res / "simulador_reparto.json").read_text(encoding="utf-8"))
    test = json.loads((res / "contraste_real.json").read_text(encoding="utf-8"))
    explo = json.loads((res / "exploratorio_topes_falsos.json").read_text(encoding="utf-8"))
    shapes = boundaries()
    missing = sorted(set(t["ine"]) ^ set(shapes))
    print(f"boundaries: {len(shapes)} municipalities | not matched: {missing}")
    print("geojson features:", geojson(shapes, INTERIM / "municipios_wgs84.geojson"))
    tests_chart(test, explo)
    gap_chart(sim["gap_above_cap"])
    allocation_chart(sim)
    need_coverage_map(t, shapes)
    under = quadrant(t)
    (res / "infraatendidos.json").write_text(json.dumps(under, indent=1, ensure_ascii=False, default=float),
                                             encoding="utf-8")
    print("underserved:", {k: v for k, v in under.items() if k != "municipalities"})
    print("  named (2,000+ young):", [(m["municipio"], m["tope_2022"], m["tope_2024"]) for m in under["municipalities"]
                                      if m["jovenes_20_34_2024"] >= 2000])
    print("figures:", sorted(p.name for p in FIG.glob("*.png")))


if __name__ == "__main__":
    main()

"""Figures for the report and the slides (development period, after the pre-registered test), and the municipal map
for the app.

  resultados/figuras/brecha_2022_2024.png               share of the rental market above the cap, 2022 against 2024
  resultados/figuras/mapa_necesidad_cobertura.png       need index 2024 next to Bono 2022 coverage
  resultados/figuras/cuadrante_necesidad_cobertura.png  the same two as a scatter: high need + low coverage = underserved
  resultados/figuras/reparto_por_necesidad.png          bonos per 1,000 young people by need tercile, simulated rules
  resultados/infraatendidos.json                        the underserved municipalities of the scatter
  data/interim/municipios_wgs84.geojson                 179 municipalities (Madrid city: its 21 districts as one feature)
Coverage = Bono 2022 accepted per 1,000 young people 20-34 (2022); the acceptance rate alone misleads (it depends on
when the money ran out). Underserved = top need tercile and coverage below the Comunidad's.
Boundaries: «Municipios y Distritos de Madrid (2020)», shapefile of the Comunidad de Madrid portal (dataset
covid19_tia_muni_y_distritos, CC BY 4.0), ETRS89 / UTM 30N; downloaded once to data/raw_2026-11-07/.
Colours: reference palette of the dataviz method (light surface); one hue per sequential measure.
Usage:  python -P scripts/graficos.py   (run necesidad_2024.py and simulador.py first)
"""
import io
import json
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
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # steps 100-700, every 100
ORANGE = ["#fde4d8", "#f9c2a8", "#f39a74", "#eb6834", "#c94f1f", "#9c3c17", "#6e2a10"]  # one-hue ramp on slot 2
SLOT1 = "#2a78d6"
ORDINAL = ["#86b6ef", "#2a78d6", "#104281"]  # blue steps 250 / 450 / 650: ordered classes (validated with --ordinal)
SOURCE = "Fuente: Comunidad de Madrid (portal de datos abiertos) y SERPAVI (MIVAU). Cálculo propio."
RULES = {"actual_2024_55": "Actual: 600 / 900 € (lista de 55)\npor orden de llegada",
         "1000_o_p75_local": "1.000 € o el p75 local\npor orden de llegada",
         "necesidad_topes_actuales": "Topes actuales\ncupos por jóvenes × necesidad",
         "necesidad2_topes_actuales": "Topes actuales\ncupos por jóvenes × necesidad²"}

plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "text.color": INK,
                     "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def es(v, d=1):
    """Spanish decimal comma."""
    return f"{v:.{d}f}".replace(".", ",")


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


def gap_chart(gap):
    rows = [("all", "Toda la Comunidad"), ("without_madrid_city", "Sin Madrid capital"), ("madrid_city", "Madrid capital")]
    bars = [("2022_rents_2022_list", "2022 (lista de 29 con 900 €)", MUTED),
            ("2024_rents_2022_list", "2024 con la lista de 29", ORDINAL[0]),
            ("2024_rents_2024_list", "2024 con la lista actual (55)", SLOT1)]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    h = 0.26
    for j, (key, label, colour) in enumerate(bars):
        y = np.arange(len(rows)) + (j - 1) * h
        v = [100 * gap[key][r] for r, _ in rows]
        ax.barh(y, v, height=h - 0.04, color=colour, label=label)
        for yi, vi in zip(y, v):
            ax.text(vi + 0.8, yi, f"{vi:.0f} %", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(rows)), [r[1] for r in rows], color=INK, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 60)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("% del mercado de alquiler por encima del tope del Bono (ponderado por jóvenes de 20 a 34 años)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=8.5, labelcolor=INK2)
    fig.suptitle("El alquiler sube y el tope no: la mitad del mercado de Madrid capital ya no cabe",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold")
    note(fig, SOURCE + " Reparto log-normal entre los percentiles 25 y 75 del SERPAVI de cada año.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(FIG / "brecha_2022_2024.png", dpi=200)
    plt.close(fig)


def choropleth(ax, paths, madrid_edge, values, bins, colours, title, unit):
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
    ax.set_title(title, loc="left", fontsize=10.5, color=INK, fontweight="bold")
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
    choropleth(axes[1], paths, madrid_edge, cov, [0, 2, 4, 6, 8, 10, 13, 30], ORANGE, "Cobertura del Bono 2022",
               "Bonos concedidos por cada 1.000 jóvenes de 20 a 34 años")
    fig.suptitle("¿Llega el Bono a donde más se necesita?", x=0.01, ha="left", fontsize=12.5, fontweight="bold")
    note(fig, SOURCE + " Rayado: sin dato (municipio pequeño o dato protegido). Contorno negro: Madrid capital.\n"
                       "Límites: «Municipios y Distritos de Madrid (2020)», portal de datos abiertos de la Comunidad "
                       "de Madrid (CC BY 4.0).")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(FIG / "mapa_necesidad_cobertura.png", dpi=200)
    plt.close(fig)


def quadrant(t):
    d = t.dropna(subset=["indice_necesidad", "cobertura_2022"]).copy()
    region = 1000 * d["bono_aceptadas"].sum() / d["jovenes_20_34_2022"].sum()
    d["infraatendido"] = (d["tercil_necesidad"] == "alta") & (d["cobertura_2022"] < region)
    fig, ax = plt.subplots(figsize=(8, 5.6))
    size = 8 + 600 * np.sqrt(d["jovenes_20_34_2024"] / d["jovenes_20_34_2024"].max())
    for flag, colour, z in ((False, AXIS, 2), (True, SLOT1, 3)):
        s = d[d["infraatendido"] == flag]
        ax.scatter(s["indice_necesidad"], s["cobertura_2022"], s=size[s.index], color=colour, alpha=0.85,
                   edgecolor=SURFACE, linewidth=1, zorder=z)
    cut = d.loc[d["tercil_necesidad"] == "alta", "indice_necesidad"].min()
    ax.axvline(cut, color=AXIS, linewidth=0.8)
    ax.axhline(region, color=AXIS, linewidth=0.8)
    ax.text(1, region + 0.3, f"Media de la Comunidad: {es(region)}", ha="left", va="bottom", fontsize=8, color=INK2)
    ax.text(cut + 0.8, 25.5, "Tercio con más necesidad →", ha="left", va="top", fontsize=8, color=INK2)
    # names of the underserved with 2,000+ young people, in a column to the right, never on top of each other
    big = d[d["infraatendido"] & (d["jovenes_20_34_2024"] >= 2000)].sort_values("cobertura_2022", ascending=False)
    step = min(0.8, (region - 0.8) / max(len(big), 1))
    label_y = region - 0.2
    for _, r in big.iterrows():
        label_y = min(r["cobertura_2022"], label_y - step)
        ax.annotate(r["municipio"], (r["indice_necesidad"], r["cobertura_2022"]), xytext=(85, label_y),
                    textcoords="data", fontsize=7.5, color=INK2, va="center",
                    arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 0.6, "shrinkA": 0, "shrinkB": 3})
    mad = d[d["ine"] == "079"].iloc[0]
    ax.annotate("Madrid capital", (mad["indice_necesidad"], mad["cobertura_2022"]), xytext=(8, 8),
                textcoords="offset points", fontsize=7.5, color=INK2)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 26)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Índice de necesidad 2024 (0-100)")
    ax.set_ylabel("Bonos 2022 concedidos por cada 1.000 jóvenes")
    dot = lambda c: Line2D([], [], marker="o", linestyle="", markersize=7, color=c)  # noqa: E731
    ax.legend([dot(SLOT1), dot(AXIS)], ["Necesidad alta y cobertura por debajo de la media", "Resto de municipios"],
              loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK2)
    fig.suptitle("Municipios infraatendidos: mucha necesidad y poco Bono", x=0.01, ha="left", fontsize=12.5,
                 fontweight="bold")
    note(fig, SOURCE + " Tamaño del punto: jóvenes de 20 a 34 años (2024).\nCon nombre, los infraatendidos con "
                       "2.000 jóvenes o más; la lista completa está en resultados/infraatendidos.json.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(FIG / "cuadrante_necesidad_cobertura.png", dpi=200)
    plt.close(fig)
    cols = ["ine", "municipio", "indice_necesidad", "cobertura_2022", "bono_aceptadas", "jovenes_20_34_2024"]
    under = d[d["infraatendido"]].sort_values("jovenes_20_34_2024", ascending=False)[cols].round(2)
    return {"coverage_region_per_1000": round(region, 2), "need_cut_top_tercile": round(float(cut), 1),
            "n": len(under), "young_2024": int(under["jovenes_20_34_2024"].sum()),
            "municipalities": under.to_dict("records")}


def allocation_chart(sim):
    terciles = [("baja", "Necesidad baja", ORDINAL[0]), ("media", "Necesidad media", ORDINAL[1]),
                ("alta", "Necesidad alta", ORDINAL[2])]
    high = sim["rules"]["actual_2024_55"]["central"]["pct_young_high_need"]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    h = 0.26
    for j, (k, label, colour) in enumerate(terciles):
        y = np.arange(len(RULES)) + (j - 1) * h
        v = [sim["rules"][r]["central"]["bonos_per_1000_young_by_need"][k] for r in RULES]
        ax.barh(y, v, height=h - 0.04, color=colour, label=label)
        for yi, vi in zip(y, v):
            ax.text(vi + 0.06, yi, es(vi), va="center", fontsize=8, color=INK2)
    ax.set_yticks(range(len(RULES)), list(RULES.values()), color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Bonos por cada 1.000 jóvenes de 20 a 34 años (simulación, 5.300 bonos, β central)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=8.5, labelcolor=INK2)
    fig.suptitle("Con el mismo dinero, el reparto entre tercios casi no cambia, salvo si se pesa más la necesidad",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    note(fig, "Simulación propia (scripts/simulador.py): demanda del Bono 2022 por municipio, β del contraste "
              f"preregistrado y 31,8 M€.\nTercios de municipios por el índice de necesidad 2024: el alto reúne al "
              f"{es(high, 0)} % de los jóvenes (Madrid capital incluida).\nCon cupos, el tope no cambia el reparto: "
              "solo cuánta gente pide cada bono.")
    fig.tight_layout(rect=(0, 0.08, 1, 0.97))
    fig.savefig(FIG / "reparto_por_necesidad.png", dpi=200)
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(INTERIM / "municipios_2024.csv", dtype={"ine": str})
    t["cobertura_2022"] = 1000 * t["bono_aceptadas"] / t["jovenes_20_34_2022"].where(t["jovenes_20_34_2022"] > 0)
    sim = json.loads((ROOT / "resultados" / "simulador_reparto.json").read_text(encoding="utf-8"))
    shapes = boundaries()
    missing = sorted(set(t["ine"]) ^ set(shapes))
    print(f"boundaries: {len(shapes)} municipalities | not matched: {missing}")
    print("geojson features:", geojson(shapes, INTERIM / "municipios_wgs84.geojson"))
    gap_chart(sim["gap_above_cap"])
    need_coverage_map(t, shapes)
    under = quadrant(t)
    (ROOT / "resultados" / "infraatendidos.json").write_text(
        json.dumps(under, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print("underserved:", under["n"], "municipalities,", under["young_2024"], "young people | region coverage",
          under["coverage_region_per_1000"], "| named:", [m["municipio"] for m in under["municipalities"][:12]])
    allocation_chart(sim)
    print("figures:", sorted(p.name for p in FIG.glob("*.png")))


if __name__ == "__main__":
    main()

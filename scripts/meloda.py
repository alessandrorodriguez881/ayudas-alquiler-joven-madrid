"""MELODA 5 reusability score (spain.meloda.org public API, CC BY 4.0) of every portal dataset we use.
Writes data/MELODA.md and data/interim/meloda.json.   Usage:  python -P scripts/meloda.py
"""
import datetime
import json
import pathlib
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM, RAW, ROOT  # noqa: E402

API = "https://spain.meloda.org/api/v1/datasets?"


def search(title):
    params = {"portal_id": "comunidad_madrid", "q": " ".join(title.split()[:8]), "page_size": 50}
    req = urllib.request.Request(API + urllib.parse.urlencode(params), headers={"User-Agent": "datamad-2026-research"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["data"]


def main():
    rows = []
    for folder in sorted(p for p in RAW.iterdir() if (p / "metadata.json").exists() and p.name != "serpavi_mivau"):
        meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        hit = next((d for d in search(meta["title"]) if d["url"].rstrip("/").endswith("/" + meta["name"])), None)
        m = (hit or {}).get("meloda") or {}
        rows.append({"dataset": meta["name"], "titulo": meta["title"], "meloda_total": m.get("total"),
                     "nivel": m.get("reusability"), **{k: v for k, v in m.items() if k.startswith("d")}})
        print(rows[-1], flush=True)
    (INTERIM / "meloda.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    dims = ["d1_license", "d2_access", "d3_format", "d4_standard", "d5_geo", "d6_frequency"]  # API field names
    md = [f"# Nota MELODA 5 de nuestros datasets del portal ({datetime.date.today():%d-%m-%Y})", "",
          "Fuente: API pública de [spain.meloda.org](https://spain.meloda.org) (datos CC BY 4.0), evaluación del 1-nov-2026. "
          "Escala 0-49; dimensiones: licencia (0-3), acceso (0-3), formato (0-3), estandarización (0-4), geolocalización (0-3) y "
          "frecuencia de actualización (0-5). Media del portal de la Comunidad: 18,1.", "",
          "| Dataset | Nota | Nivel | " + " | ".join(d.split("_", 1)[1] for d in dims) + " |",
          "|---|---|---|" + "---|" * len(dims)]
    md += [f"| {r['titulo']} | {r['meloda_total']} | {r['nivel']} | " + " | ".join(str(r.get(d, '')) for d in dims) + " |"
           for r in sorted(rows, key=lambda r: -(r["meloda_total"] or 0))]
    (ROOT / "data" / "MELODA.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("written data/MELODA.md")


if __name__ == "__main__":
    main()

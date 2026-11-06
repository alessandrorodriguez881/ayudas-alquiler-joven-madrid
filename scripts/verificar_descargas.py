"""Check that every downloaded file is still a faithful copy of the official source (idea from the 5-Nov training:
'verify your downloads'). For each CKAN dataset in data/raw/: rows in our CSV vs the DataStore total of the API,
and SHA-256 of our file vs a fresh download of the same resource. For SERPAVI: MD5 and the server's size and date.
Nothing in data/raw/ is overwritten: if the portal has published a newer file, it is only reported.
Writes data/VERIFICACION.md.   Usage:  python -P scripts/verificar_descargas.py
"""
import datetime
import hashlib
import io
import json
import pathlib
import sys
import urllib.parse
import urllib.request

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import RAW, ROOT, leer_csv  # noqa: E402

API = "https://datos.comunidad.madrid/api/3/action/"


def get(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "datamad-2026-research"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read(), dict(r.headers)


def ckan(action, **params):
    return json.loads(get(API + action + "?" + urllib.parse.urlencode(params))[0])["result"]


def table(src):
    return leer_csv(src, dtype=str)


def content_diff(ours, fresh):
    """Rows only in one of the two files, ignoring row order and byte-level formatting (like the trainer's
    comparar_json.py 'normalised' mode)."""
    a = set(map(tuple, ours.fillna("").to_numpy()))
    rows_b = list(map(tuple, fresh.fillna("").to_numpy()))
    only_b, only_a = set(rows_b) - a, a - set(rows_b)
    new = fresh[[r in only_b for r in rows_b]]
    years = sorted(new["Año"].unique()) if "Año" in new.columns else []
    return len(only_b), len(only_a), years


def check_ckan(folder):
    meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    local = next(folder.glob("*.csv"))
    sha_local = hashlib.sha256(local.read_bytes()).hexdigest()
    pkg = ckan("package_show", id=meta["name"])
    res = next(r for r in pkg["resources"] if (r.get("format") or "").upper() == "CSV")
    api_total = None
    if res.get("datastore_active"):
        api_total = ckan("datastore_search", resource_id=res["id"], limit=0)["total"]
    raw_portal = get(res["url"])[0]
    ours = table(local)
    n = len(ours)
    if hashlib.sha256(raw_portal).hexdigest() == sha_local:
        status = "✅ idéntico al portal (byte a byte)"
    else:
        added, removed, years = content_diff(ours, table(io.BytesIO(raw_portal)))
        if added == removed == 0:
            status = "✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes)"
        else:
            status = (f"🔄 el portal tiene datos nuevos: +{added} / −{removed} filas"
                      + (f" (años de las filas nuevas: {', '.join(map(str, years))})" if years else ""))
    if api_total is not None and api_total != n:
        status += f" · la API DataStore da {api_total} filas"
    return {"dataset": meta["name"], "filas_nuestras": n, "filas_api": api_total if api_total is not None else "sin DataStore",
            "sha256": sha_local[:12], "estado": status}


def check_serpavi(folder):
    meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    local = next(folder.glob("*.xlsx"))
    md5 = hashlib.md5(local.read_bytes()).hexdigest()
    _, head = get(meta["file_url"], method="HEAD")
    same_size = int(head.get("Content-Length", -1)) == local.stat().st_size
    status = "✅ idéntico (MD5 y tamaño)" if md5 == meta["md5"] and same_size else "🔄 cambió en el servidor o en local"
    return {"dataset": meta["name"], "filas_nuestras": "Excel (varias hojas)", "filas_api": "—", "sha256": f"md5 {md5[:12]}",
            "estado": f"{status} · servidor: {head.get('Last-Modified', '?')}"}


def main():
    out = []
    for folder in sorted(p for p in RAW.iterdir() if (p / "metadata.json").exists()):
        try:
            out.append(check_serpavi(folder) if folder.name == "serpavi_mivau" else check_ckan(folder))
        except Exception as e:  # network or portal error: report it, do not stop
            out.append({"dataset": folder.name, "filas_nuestras": "?", "filas_api": "?", "sha256": "?", "estado": f"❓ error: {e}"})
        print(out[-1], flush=True)
    df = pd.DataFrame(out)
    md = [f"# Verificación de las descargas ({datetime.date.today():%d-%m-%Y})", "",
          "Generado por `scripts/verificar_descargas.py`. Compara cada fichero de `data/raw/` con el portal oficial: "
          "filas frente al total de la API DataStore y huella SHA-256 frente a una descarga nueva. No sobrescribe nada.", "",
          "| Dataset | Filas (nuestras) | Filas (API) | Huella | Estado |", "|---|---|---|---|---|"]
    md += [f"| `{r.dataset}` | {r.filas_nuestras} | {r.filas_api} | `{r.sha256}` | {r.estado} |" for r in df.itertuples()]
    (ROOT / "data" / "VERIFICACION.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nwritten data/VERIFICACION.md ({len(df)} datasets)")


if __name__ == "__main__":
    main()

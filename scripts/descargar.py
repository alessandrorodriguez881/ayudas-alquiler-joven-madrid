"""Download the open datasets used by the DataMad 2026 project from the Comunidad de Madrid CKAN portal.

Each dataset goes to data/raw/<dataset_id>/datos.csv together with its metadata (metadata.json: title, licence, source
URL and the file's original name). Only CSV resources are downloaded; files over MAX_MB are skipped and reported.
Usage:  python scripts/descargar.py [--destino=data/raw_YYYY-MM-DD] [dataset_id ...]   (no ids = all of DATASETS)
        --destino keeps the frozen snapshot in data/raw untouched (the preregistered test reads that one)
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request

API = "https://datos.comunidad.madrid/api/3/action/package_show?id="
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MAX_MB = 60
DATASETS = [
    # housing aid (what we evaluate)
    "spacm_bono_alquiler_joven_2022",
    "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos",
    # rents
    "1934258",   # average monthly rent by postcode, Madrid city
    "1934261",   # average rental days by postcode, Madrid city
    "1934430",   # rental price index by district (base 2015)
    "1934246",   # rental yield and prices
    # income
    "irpf_indicador_renta",            # gross disposable income per municipality
    "irpf_declaraciones_por_tramo",    # IRPF returns by tax-base bracket per municipality
    # labour market
    "paro_registrado_edad_municipio",  # registered unemployment by age and municipality
    "302038",                          # total registered unemployment, municipalities
    # population
    "poblacion_censada_por_edad_nacionalidad_y_sexo",
    "grado_juventud_por_edad",
    # added 27-Oct (missing data from PLAN.md)
    "alquiler_medio_mensual_viviendas_arrendadas_valor_catastral_municipios_mas_20000",  # average rent, municipalities > 20k
    "1934445",                                       # rental price index, municipalities > 10k (base 2015)
    "censo_2021_viviendas_familiares_por_tenencia",  # 2021 census: households by tenure (rented) per municipality
    # added 6-Nov
    "1914500",  # Plan Alquila, young rental pool: regional totals 2012-2025 (context only)
]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "datamad-2026-research"}), timeout=120) as r:
        return r.read()


def main():
    args = sys.argv[1:]
    raw = ROOT / args.pop(0).split("=", 1)[1] if args and args[0].startswith("--destino=") else RAW
    raw.mkdir(parents=True, exist_ok=True)
    summary = []
    for ds in args or DATASETS:
        try:
            meta = json.loads(get(API + urllib.parse.quote(ds)))["result"]
        except Exception as e:  # dataset id not found, network error…
            summary.append(f"{ds}: METADATA ERROR {e}")
            continue
        out = raw / ds
        out.mkdir(exist_ok=True)
        keep = {k: meta.get(k) for k in ("name", "title", "notes", "license_title", "license_url", "metadata_modified", "url")}
        keep["portal_url"] = f"https://datos.comunidad.madrid/dataset/{meta.get('name')}"
        keep["resources"] = [{k: r.get(k) for k in ("name", "format", "url", "size", "last_modified")} for r in meta.get("resources", [])]
        (out / "metadata.json").write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
        n_csv = 0
        for res in meta.get("resources", []):
            if (res.get("format") or "").upper() != "CSV":
                continue
            n_csv += 1
            size = res.get("size") or 0
            if size and size > MAX_MB * 2**20:
                summary.append(f"{ds}: skipped {res['url']} ({size / 2**20:.0f} MB)")
                continue
            # Short fixed name: the portal's names reach 100 characters and, inside the folder, passed the 260-character
            # limit of Windows when cloning or unzipping the repository. The original name and URL stay in metadata.json
            fname = out / ("datos.csv" if n_csv == 1 else f"datos_{n_csv}.csv")
            try:
                data = get(res["url"])
                fname.write_bytes(data)
                summary.append(f"{ds}: {fname.name} {len(data) / 1024:.0f} KB | {meta.get('title')}")
            except Exception as e:
                summary.append(f"{ds}: DOWNLOAD ERROR {res['url']} {e}")
    print("\n".join(summary))


if __name__ == "__main__":
    main()

"""Madrid city's 21 districts for «¿Dónde me llega?» (app/app_pages/donde.py). The municipal map draws Madrid as one
piece, but its rents go from Puente de Vallecas to Chamberí, so the app shows the share of rents under the cap district
by district.

  data/interim/distritos_madrid_wgs84.geojson   the 21 boundaries in WGS84; "ine" = municipality + district, from
                                                '07901' (Centro) to '07921' (Barajas), the end of SERPAVI's CUDIS
                                                (2807901 ... 2807921); "nombre" = the district's name
Rents: SERPAVI's 'Distritos' sheet, already in data/interim/serpavi_madrid_distritos.csv (preparar_datos.py). Each
district takes Madrid's caps, because the caps are set per municipality.
Boundaries: the shapefile of the municipal map (graficos.py), «Municipios y Distritos de Madrid (2020)» of the Comunidad
de Madrid portal (covid19_tia_muni_y_distritos, CC BY 4.0). Its table is UTF-8.
Usage:  python -P scripts/distritos_madrid.py
"""
import io
import pathlib
import sys
import zipfile

import shapefile  # pyshp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import INTERIM  # noqa: E402
from graficos import GEO_ZIP, boundaries, geojson  # noqa: E402

OUT = INTERIM / "distritos_madrid_wgs84.geojson"


def districts():
    """Madrid's district polygons (UTM 30N) and names, keyed '07901' ... '07921'."""
    boundaries()  # downloads the shapefile the first time
    z = zipfile.ZipFile(GEO_ZIP)
    base = "municipios_y_distritos_madrid"
    r = shapefile.Reader(**{k: io.BytesIO(z.read(f"{base}.{k}")) for k in ("shp", "shx", "dbf")}, encoding="utf-8")
    shapes, names = {}, {}
    for sr in r.iterShapeRecords():
        code = sr.record["codigo_geo"]  # '079601': Madrid (079), district 01; municipalities have 4 digits
        if code.startswith("0796") and len(code) == 6:
            key = "079" + code[-2:]
            shapes.setdefault(key, []).append(sr.shape)
            names[key] = sr.record["municipio_"].removeprefix("Madrid-").replace(" - ", "-")  # 'San Blas - Canillejas'
    return shapes, names


def main():
    shapes, names = districts()
    assert sorted(shapes) == [f"079{i:02d}" for i in range(1, 22)], sorted(shapes)
    print("district features:", geojson(shapes, OUT, names))
    for k in sorted(names):
        print(k, names[k])


if __name__ == "__main__":
    main()

"""DCAT-AP-ES record of the project's data (written 8-Nov-2026): data/dcat_ap_es.ttl, validated with the official SHACL
shapes of datos.gob.es (DCAT-AP-ES 1.0.0, github.com/datosgobes/DCAT-AP-ES, CC BY 4.0) -> resultados/validacion_dcat.json.
One catalogue with three datasets: the SQLite database, the indicators by municipality (CSV) and the simulated allocation
(CSV and JSON). Sizes and SHA-1 checksums are those of the committed files, so they match what the download address
serves; the script stops if a file has changes that are not committed.
Choices the norm leaves to the publisher, said here:
  - publisher: the project team, as a foaf:Agent with its own URI; it has no DIR3 code (not a public body). If the
    Comunidad publishes the data, its DIR3 URI goes here
  - the addresses are those of the GitHub repository; they work once the repository is public
  - licence CC BY 4.0, as the portal's data; the SERPAVI columns keep the MIVAU legal notice (said in each description)
  - no dct:format for the SQLite file (the EU file-type list has no SQLite entry): its IANA media type says what it is
Usage:  python -P scripts/ficha_dcat.py   (needs rdflib and pyshacl; downloads the shapes once, at a fixed commit)"""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCAT, DCTERMS as DCT, FOAF, RDF, XSD

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import ROOT  # noqa: E402

OUT = ROOT / "data" / "dcat_ap_es.ttl"
REPO = "https://github.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid"
BLOB, RAWGH = REPO + "/blob/main/", "https://raw.githubusercontent.com/alessandrorodriguez881/ayudas-alquiler-joven-madrid/main/"
SHAPES_COMMIT = "c6ab5330edd33b24350429fc2c17906506f04fa1"  # DCAT-AP-ES main, 22-Sep-2026
# the vocabulary shapes too: the others point at shapes defined there (e.g. the DIR3 organism pattern), and pyshacl
# treats a shape it cannot find as one everything matches
SHAPES = ["shacl_catalog_shape.ttl", "shacl_dataset_shape.ttl", "shacl_distribution_shape.ttl", "shacl_common_shapes.ttl",
          "shacl_mdr-vocabularies.shape.ttl"]
SHAPES_DIR = ROOT / "data" / "raw" / "dcat_ap_es_shacl"
SPDX, VCARD = Namespace("http://spdx.org/rdf/terms#"), Namespace("http://www.w3.org/2006/vcard/ns#")
DCATAP = Namespace("http://data.europa.eu/r5r/")
EU = "http://publications.europa.eu/resource/authority/"
SECTOR = "http://datos.gob.es/kos/sector-publico/sector"
MADRID = URIRef("http://datos.gob.es/recurso/sector-publico/territorio/Autonomia/Comunidad-Madrid")
LICENCE = URIRef(EU + "licence/CC_BY_4_0")
TEAM = URIRef(REPO + "#equipo")
PLACEHOLDER = URIRef("http://datos.gob.es/recurso/sector-publico/org/Organismo/E00000000")  # DIR3 shape, not a body
SERPAVI = ("Las columnas que vienen del SERPAVI (Ministerio de Vivienda y Agenda Urbana) siguen su aviso legal: "
           "reutilización permitida citando la fuente.")
KEYWORDS = ["Bono Alquiler Joven", "alquiler", "jóvenes", "vivienda", "Plan Estatal de Vivienda 2026-2030", "SERPAVI",
            "municipios", "Comunidad de Madrid"]
DATASETS = [
    ("base-de-datos", "Bono Alquiler Joven y alquiler por municipio: base de datos del proyecto",
     "Todo lo que usa el proyecto, por municipio de la Comunidad de Madrid, en un solo fichero SQLite: población, renta, "
     "paro, hogares de alquiler e índice de necesidad; cada convocatoria del Bono Alquiler Joven, de las Ayudas al "
     "alquiler para jóvenes y del Plan Estatal de Vivienda 2026-2030 con su tope en cada municipio; solicitudes por "
     "programa y año; alquiler del SERPAVI de 2011 a 2024, por municipio y en los 21 distritos de Madrid capital; y el "
     "reparto simulado con cada regla. Con diccionario de "
     "cada columna. La crea scripts/base_datos.py.", ("2011-01-01", "2024-12-31"),
     [("data/bono_alquiler_joven.sqlite", "SQLite", None, "application/vnd.sqlite3")]),
    ("indicadores-municipios-2024", "Indicadores por municipio de la Comunidad de Madrid, 2024",
     "Una fila por municipio (179): topes del Bono Alquiler Joven 2022 y 2024, población, renta, paro juvenil, hogares de "
     "alquiler, alquiler del SERPAVI de 2023 y 2024, parte del alquiler por encima de cada tope e índice de necesidad. "
     "La crea scripts/necesidad_2024.py.", ("2021-01-01", "2024-12-31"),
     [("data/interim/municipios_2024.csv", "CSV", "CSV", "text/csv")]),
    ("reparto-simulado", "Reparto simulado del Bono Alquiler Joven con distintos topes y criterios",
     "Solicitudes esperadas y bonos por municipio con la regla de hoy, el Plan Estatal 2026-2030 y la propuesta del "
     "proyecto (presupuesto fijo de 31,8 millones de euros), y el resumen de cada regla. Es una simulación con supuestos "
     "escritos en scripts/simulador.py, no una predicción.", ("2022-01-01", "2024-12-31"),
     [("data/interim/simulador_municipios.csv", "CSV", "CSV", "text/csv"),
      ("resultados/simulador_reparto.json", "JSON", "JSON", "application/json")]),
]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


def committed(path):
    """Bytes of the committed file (what the download address serves); stops if the working copy differs."""
    blob = git("cat-file", "blob", f"HEAD:{path}")
    assert (ROOT / path).read_bytes() == blob, f"{path} tiene cambios sin commit: haz commit antes de la ficha"
    return blob


def dates(path):
    first = git("log", "--diff-filter=A", "--format=%cs", "--", path).decode().split()[-1]
    return first, git("log", "-1", "--format=%cs", "--", path).decode().strip()


def lit_date(d):
    return Literal(d, datatype=XSD.date)


def build():
    g = Graph()
    for p, ns in [("dcat", DCAT), ("dcatap", DCATAP), ("dct", DCT), ("foaf", FOAF), ("spdx", SPDX), ("vcard", VCARD),
                  ("xsd", XSD)]:
        g.bind(p, ns)
    cat = URIRef(REPO + "#catalogo")
    today = datetime.date.today().isoformat()
    g.add((TEAM, RDF.type, FOAF.Agent))
    g.add((TEAM, FOAF.name, Literal("Equipo del proyecto «¿Llegan las ayudas al alquiler a quien más las necesita?» "
                                    "(DataMad 2026)", lang="es")))
    g.add((cat, RDF.type, DCAT.Catalog))
    g.add((cat, DCT.title, Literal("Datos del proyecto sobre el Bono Alquiler Joven en la Comunidad de Madrid", lang="es")))
    g.add((cat, DCT.description, Literal("Datos abiertos, agregados por municipio, para estudiar si los topes de las ayudas "
                                         "al alquiler para jóvenes llegan a quien más las necesita, y para el estudio de "
                                         "la oferta de alquiler que pide el art. 135 del Plan Estatal de Vivienda "
                                         "2026-2030. Se rehacen con un comando desde los datos de origen.", lang="es")))
    g.add((cat, DCT.publisher, TEAM))
    g.add((cat, FOAF.homepage, URIRef(REPO)))
    g.add((cat, DCAT.themeTaxonomy, URIRef(SECTOR)))
    g.add((cat, DCT.issued, lit_date("2026-11-08")))
    g.add((cat, DCT.modified, lit_date(today)))
    g.add((cat, DCT.language, URIRef(EU + "language/SPA")))
    g.add((cat, DCT.license, LICENCE))
    g.add((cat, DCT.spatial, MADRID))
    for slug, title, desc, (start, end), files in DATASETS:
        ds = URIRef(f"{REPO}#{slug}")
        g.add((cat, DCAT.dataset, ds))
        g.add((ds, RDF.type, DCAT.Dataset))
        g.add((ds, DCT.title, Literal(title, lang="es")))
        g.add((ds, DCT.description, Literal(desc + " " + SERPAVI, lang="es")))
        g.add((ds, DCT.publisher, TEAM))
        g.add((ds, DCAT.theme, URIRef(SECTOR + "/vivienda")))
        for k in KEYWORDS:
            g.add((ds, DCAT.keyword, Literal(k, lang="es")))
        g.add((ds, DCT.spatial, MADRID))
        period = BNode()
        g.add((ds, DCT.temporal, period))
        g.add((period, RDF.type, DCT.PeriodOfTime))
        g.add((period, DCAT.startDate, lit_date(start)))
        g.add((period, DCAT.endDate, lit_date(end)))
        g.add((ds, DCT.language, URIRef(EU + "language/SPA")))
        g.add((ds, DCT.accrualPeriodicity, URIRef(EU + "frequency/ANNUAL")))
        g.add((ds, DCT.accessRights, URIRef(EU + "access-right/PUBLIC")))
        g.add((ds, DCAT.landingPage, URIRef(REPO)))
        contact = BNode()
        g.add((ds, DCAT.contactPoint, contact))
        g.add((contact, RDF.type, VCARD.Organization))
        g.add((contact, VCARD.fn, Literal("Equipo del proyecto (DataMad 2026)", lang="es")))
        g.add((contact, VCARD["organization-name"], Literal("Equipo del proyecto (DataMad 2026)", lang="es")))
        g.add((contact, VCARD.hasURL, URIRef(REPO + "/issues")))  # no e-mail or phone: no personal data here
        issued = []
        for path, label, fmt, media in files:
            data = committed(path)
            first, last = dates(path)
            issued.append(first)
            dist = URIRef(f"{REPO}#{slug}-{label.lower()}")
            g.add((ds, DCAT.distribution, dist))
            g.add((dist, RDF.type, DCAT.Distribution))
            g.add((dist, DCT.title, Literal(f"{title} ({label})", lang="es")))
            g.add((dist, DCT.description, Literal(f"Fichero {path} del repositorio. {SERPAVI}", lang="es")))
            g.add((dist, DCAT.accessURL, URIRef(BLOB + path)))
            g.add((dist, DCAT.downloadURL, URIRef(RAWGH + path)))
            if fmt:
                g.add((dist, DCT.format, URIRef(EU + "file-type/" + fmt)))
            g.add((dist, DCAT.mediaType, URIRef("https://www.iana.org/assignments/media-types/" + media)))
            g.add((dist, DCT.license, LICENCE))
            g.add((dist, DCATAP.availability, URIRef(EU + "planned-availability/STABLE")))
            g.add((dist, DCAT.byteSize, Literal(len(data), datatype=XSD.nonNegativeInteger)))
            check = BNode()
            g.add((dist, SPDX.checksum, check))
            g.add((check, RDF.type, SPDX.Checksum))
            g.add((check, SPDX.algorithm, SPDX.checksumAlgorithm_sha1))
            g.add((check, SPDX.checksumValue, Literal(hashlib.sha1(data).hexdigest(), datatype=XSD.hexBinary)))
            g.add((dist, DCT.issued, lit_date(first)))
            g.add((dist, DCT.modified, lit_date(last)))
            if path.endswith(".sqlite"):
                g.add((dist, DCT.conformsTo, URIRef(BLOB + "data/DICCIONARIO_BASE_DE_DATOS.md")))
        g.add((ds, DCT.issued, lit_date(min(issued))))
        g.add((ds, DCT.modified, lit_date(max(dates(p)[1] for p, *_ in files))))
    return g


def shapes():
    SHAPES_DIR.mkdir(parents=True, exist_ok=True)
    meta = SHAPES_DIR / "metadata.json"
    for name in SHAPES:
        f = SHAPES_DIR / name
        if not f.exists():
            url = f"https://raw.githubusercontent.com/datosgobes/DCAT-AP-ES/{SHAPES_COMMIT}/shacl/1.0.0/{name}"
            f.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    meta.write_text(json.dumps({
        "name": "dcat_ap_es_shacl", "title": "Plantillas SHACL de DCAT-AP-ES 1.0.0 (datos.gob.es)",
        "source": f"https://github.com/datosgobes/DCAT-AP-ES/tree/{SHAPES_COMMIT}/shacl/1.0.0", "license": "CC BY 4.0",
        # MD5 with LF line ends, as published: a clone with core.autocrlf=true checks the files out with CRLF
        "files": {n: hashlib.md5((SHAPES_DIR / n).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for n in SHAPES}},
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    sg = Graph()
    for name in SHAPES:
        sg.parse(SHAPES_DIR / name, format="turtle")
    return sg


def main():
    from pyshacl import validate  # only needed here
    g = build()
    OUT.write_text(g.serialize(format="turtle"), encoding="utf-8")
    conforms, report, text = validate(Graph().parse(OUT, format="turtle"), shacl_graph=shapes(), inference="none",
                                      advanced=True, allow_warnings=True)
    sh = Namespace("http://www.w3.org/ns/shacl#")
    found = {}
    for r in report.subjects(RDF.type, sh.ValidationResult):
        sev = str(report.value(r, sh.resultSeverity)).rsplit("#", 1)[-1]
        msgs = [m for m in report.objects(r, sh.resultMessage) if getattr(m, "language", None) in ("es", None)]
        node = report.value(r, sh.focusNode)  # blank nodes get a new id each run: a fixed label keeps the file stable
        found.setdefault(sev, []).append({"nodo": "nodo en blanco" if isinstance(node, BNode) else str(node),
                                          "propiedad": str(report.value(r, sh.resultPath)),
                                          "mensaje": str(msgs[0]) if msgs else ""})
    found = {k: sorted(v, key=lambda x: (x["nodo"], x["propiedad"], x["mensaje"])) for k, v in found.items()}
    # the same record with a placeholder DIR3 code as publisher: does anything else fail?
    swap = Graph()
    for s, p, o in g:
        swap.add((PLACEHOLDER if s == TEAM else s, p, PLACEHOLDER if o == TEAM else o))
    only_publisher = validate(swap, shacl_graph=shapes(), inference="none", advanced=True, allow_warnings=True)[0]
    out = {"fichero": OUT.relative_to(ROOT).as_posix(), "plantillas": f"DCAT-AP-ES 1.0.0, commit {SHAPES_COMMIT[:7]}",
           "cumple": bool(conforms), "cumple_con_un_publicador_dir3_de_ejemplo": bool(only_publisher),
           "triples": len(g), **{k: v for k, v in sorted(found.items())}}
    (ROOT / "resultados" / "validacion_dcat.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                               encoding="utf-8")
    print("cumple:", conforms, "| con un publicador DIR3 de ejemplo:", only_publisher, "| triples:", len(g), "|",
          {k: len(v) for k, v in found.items()})


if __name__ == "__main__":
    main()

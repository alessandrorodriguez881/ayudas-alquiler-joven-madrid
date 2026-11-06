"""Which municipalities had the 900 EUR rent cap (instead of 600) in each official call, read from the calls themselves.
Output: data/interim/topes_900_convocatorias.csv, one row per municipality of the Comunidad de Madrid (179).
  - Bono Alquiler Joven 2022: Annex II of the Acuerdo of 14-Sep-2022 (the 29 names in comun.CAP900)
  - Ayudas al alquiler, programa de jóvenes 2022, 2023, 2024 and 2025: Annex I of each call (BDNS full text)
  - Bono Alquiler Joven 2024: Annex II of the Acuerdo of 26-Dec-2024 (certificate in BDNS 805618)
The PDFs are downloaded from the BDNS API into docs_oficiales/ when missing and checked by MD5.
Usage:  python -P scripts/topes_convocatorias.py   (run scripts/codigos_municipios.py first)
"""
import hashlib
import pathlib
import re
import sys
import unicodedata
import urllib.request

import pandas as pd
import pypdf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # python -P drops the script folder
from comun import CAP900, INTERIM, ROOT  # noqa: E402

DOCS = ROOT / "docs_oficiales"
BDNS_DOC = "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos?idDocumento="
# column -> (BDNS call, BDNS document id, file name, MD5, expected number of 900 EUR municipalities)
CALLS = {
    "ayudas_2022": (654786, 804712, "BDNS_654786_convocatoria_ayudas_alquiler_jovenes_2022.pdf", "4862c65f6f47da691294509a9756702d", 29),
    "ayudas_2023": (721190, 963957, "BDNS_721190_convocatoria_ayudas_alquiler_jovenes_2023.pdf", "4763566415618964cc0a9f6cb16b3344", 29),
    "ayudas_2024": (793423, 1150270, "BDNS_793423_convocatoria_ayudas_alquiler_jovenes_2024.pdf", "4f10f497e15fe7b28c7cd34610f67492", 55),
    "bono_2024": (805618, 1505247, "BDNS_805618_certificado_ACG_bono_2024.pdf", "e4ec7a352bb13a1dc015e77ca9ade822", 55),
    "ayudas_2025": (864406, 1342309, "BDNS_864406_convocatoria_ayudas_alquiler_jovenes_2025.pdf", "b300d8279a3975179487ef046593c3a8", 55),
}
ARTS = ("el", "la", "los", "las")
TYPOS = {"carmarmadeesteruelas": "camarmadeesteruelas",  # spelling in the 2024-2025 annexes
         "paracuellosdeljarama": "paracuellosdejarama"}


def fold(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()


def key(name):
    """Article-free, space-free key. PDF text is often letter-spaced ('Al c a l á  d e  He n a r e s')."""
    return "".join(w for w in re.sub(r"[(),.\-]", " ", fold(name)).split() if w not in ARTS)


def keys_of_extracted(name):
    """Candidate keys for a name read from a PDF: word-based first, then with a leading/trailing article cut off."""
    s = re.sub(r"[(),.\-\s]", "", fold(name))
    out = [key(name), s]
    out += [s[len(a):] for a in ARTS if s.startswith(a)] + [s[:-len(a)] for a in ARTS if s.endswith(a)]
    return [TYPOS.get(k, k) for k in out]


def pdf_text(fname, doc_id, md5):
    path = DOCS / fname
    if not path.exists():
        req = urllib.request.Request(BDNS_DOC + str(doc_id), headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    got = hashlib.md5(path.read_bytes()).hexdigest()
    if got != md5:
        sys.exit(f"{fname}: MD5 {got}, expected {md5} (the document changed: check it by hand)")
    return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(path).pages)


def names_900(text):
    """Rows 'Municipio 900 euros 450 euros' of the annex (digits may come split: '90 0 euros')."""
    return [re.sub(r"\s+", " ", m.group(1)).strip()
            for m in re.finditer(r"^\s*(.+?)\s*9\s*0\s*0\s*euros\s+4\s*5\s*0\s*euros", text, re.M | re.I)]


def main():
    t = pd.read_csv(INTERIM / "codigos_municipios.csv", dtype={"ine": str, "ine5": str})
    t = t[["ine", "ine5", "nombre_estadistica_cm"]].copy()
    lookup = {}
    for n, ine in zip(t["nombre_estadistica_cm"], t["ine"]):
        # also keep inner articles, since letter-spaced text loses word boundaries ('...delosreyes')
        lookup.update({key(n): ine, re.sub(r"[(),.\-\s]", "", fold(n)): ine})
    cap900 = {"bono_2022": {lookup[key(n)] for n in CAP900}}
    for col, (_, doc_id, fname, md5, expected) in CALLS.items():
        found, missing = set(), []
        for n in names_900(pdf_text(fname, doc_id, md5)):
            ine = next((lookup[k] for k in keys_of_extracted(n) if k in lookup), None)
            found.add(ine) if ine else missing.append(n)
        if missing or len(found) != expected:
            sys.exit(f"{col}: {len(found)} matched (expected {expected}); unmatched: {missing}")
        cap900[col] = found
    order = ["bono_2022", "ayudas_2022", "ayudas_2023", "ayudas_2024", "bono_2024", "ayudas_2025"]
    for col in order:
        t[f"tope_{col}"] = t["ine"].map(lambda i, s=cap900[col]: 900 if i in s else 600)
    t["sube_a_900_en_2024"] = (t["tope_ayudas_2023"] == 600) & (t["tope_ayudas_2024"] == 900)
    t.to_csv(INTERIM / "topes_900_convocatorias.csv", index=False)
    print({c: len(cap900[c]) for c in order}, "| suben de 600 a 900 en 2024:", int(t["sube_a_900_en_2024"].sum()))
    print("Bono 2024 = Ayudas 2024 = Ayudas 2025:", cap900["bono_2024"] == cap900["ayudas_2024"] == cap900["ayudas_2025"],
          "| 2022 = 2023 = Bono 2022:", cap900["ayudas_2022"] == cap900["ayudas_2023"] == cap900["bono_2022"])


if __name__ == "__main__":
    main()

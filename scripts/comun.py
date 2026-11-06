"""Shared helpers for the DataMad 2026 scripts (paths, name matching, rent caps, log-normal share above a cap)."""
import math
import pathlib
import re
import unicodedata

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
# Annex II of the Acuerdo del Consejo de Gobierno of 14-Sep-2022 (cap 900 EUR flat / 450 EUR room); 600 EUR elsewhere
CAP900 = ["Alcalá de Henares", "Alcobendas", "Alcorcón", "Algete", "Arroyomolinos", "Boadilla del Monte", "Getafe",
          "Collado Villalba", "Coslada", "Fuenlabrada", "Galapagar", "Las Rozas de Madrid", "Leganés", "Madrid",
          "Majadahonda", "Móstoles", "Parla", "Pinto", "Pozuelo de Alarcón", "Rivas-Vaciamadrid",
          "San Fernando de Henares", "San Sebastián de los Reyes", "Torrejón de Ardoz", "Torrelodones", "Tres Cantos",
          "Valdemoro", "Villanueva de la Cañada", "Villanueva del Pardillo", "Villaviciosa de Odón"]


def leer_csv(src, **kw):
    """Read a portal CSV whatever its encoding: files downloaded on 21-Oct are Latin-1, and since early November the
    portal serves UTF-8 with BOM. Accepts a path or a BytesIO."""
    for enc in ("utf-8-sig", "latin-1"):
        try:
            if hasattr(src, "seek"):
                src.seek(0)
            return pd.read_csv(src, sep=";", encoding=enc, low_memory=False, **kw)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"cannot decode {src}")


def norm(name):
    """'Rozas de Madrid, Las' / 'Las Rozas de Madrid' / 'Rivas Vaciamadrid' → same key."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    words = re.sub(r"[(),.\-]", " ", s).split()
    arts = {"el", "la", "los", "las"}
    return " ".join([w for w in words if w not in arts] + sorted(w for w in words if w in arts))


CAP900_KEYS = {norm(n) for n in CAP900}


def cm_to_ine(code):
    """Comunidad de Madrid statistics code (INE code * 10 + check digit) → 3-digit INE code ('002')."""
    return f"{int(code) // 10:03d}"


def share_above(cap, p25, p75):
    """Share of rents above the cap, assuming log-normal rents fitted on the 25th and 75th percentiles."""
    if not (p25 and p75 and p25 > 0 and p75 > p25) or any(map(np.isnan, (p25, p75))):
        return np.nan
    mu, sigma = (math.log(p25) + math.log(p75)) / 2, (math.log(p75) - math.log(p25)) / (2 * 0.6745)
    return 1 - 0.5 * (1 + math.erf((math.log(cap) - mu) / (sigma * math.sqrt(2))))

"""Quick structural look at every downloaded CSV: separator, encoding, shape, columns and a few rows.
Usage:  python scripts/explorar.py [dataset_id ...]
"""
import pathlib
import sys

import pandas as pd

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"


def read(path):
    for enc in ("utf-8-sig", "latin-1"):
        for sep in (";", ","):
            try:
                df = pd.read_csv(path, sep=sep, encoding=enc, low_memory=False)
                if df.shape[1] > 1:
                    return df, sep, enc
            except Exception:
                continue
    raise ValueError(f"cannot parse {path}")


wanted = set(sys.argv[1:])
for d in sorted(RAW.iterdir()):
    if wanted and d.name not in wanted:
        continue
    for f in sorted(d.glob("*.csv")):
        df, sep, enc = read(f)
        print(f"\n=== {d.name} | {f.name[:70]} | sep '{sep}' {enc} | {df.shape[0]} rows x {df.shape[1]} cols")
        print("columns:", list(df.columns)[:25])
        with pd.option_context("display.width", 200, "display.max_columns", 12, "display.max_colwidth", 30):
            print(df.head(4).to_string())
        for c in df.columns[:8]:
            if df[c].dtype == object and df[c].nunique() < 40:
                print(f"   {c}: {df[c].nunique()} values e.g. {sorted(map(str, df[c].dropna().unique()))[:12]}")

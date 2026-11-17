"""After `python scripts/rehacer_todo.py` on another system: every tracked text file that changed has to say the same, with
numbers equal up to a relative tolerance of 1e-9 (Linux and Windows can differ in the last decimal, about 1e-16).
The figures (PNG) do not count: their pixels depend on the fonts. The SQLite database is compared table by table.
Exit code 1 if anything differs more than that.  Run:  python scripts/comparar_con_tolerancia.py   (used by GitHub, comprobar.yml)"""
import math
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL, ABS = 1e-9, 1e-12
NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=REL, abs_tol=ABS)


def same_text(old, new):
    """Same text outside the numbers, and every number close."""
    if NUM.sub("#", old) != NUM.sub("#", new):
        return False
    return all(close(a, b) for a, b in zip(NUM.findall(old), NUM.findall(new)))


def rows(path):
    con = sqlite3.connect(path)
    try:
        return {t: con.execute(f'SELECT * FROM "{t}"').fetchall() for (t,) in
                con.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").fetchall()}
    finally:
        con.close()


def same_value(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return a is not None and b is not None and close(a, b)
    return a == b


def same_db(old_bytes, path):
    with tempfile.TemporaryDirectory() as d:
        old_path = Path(d) / "antes.sqlite"
        old_path.write_bytes(old_bytes)
        a, b = rows(old_path), rows(path)
    if a.keys() != b.keys():
        return False
    stamp = lambda t, r: t == "metadatos" and r[0] in ("creada", "commit")  # noqa: E731  (change on every build)
    for t in a:
        ra = [r for r in a[t] if not stamp(t, r)]
        rb = [r for r in b[t] if not stamp(t, r)]
        if len(ra) != len(rb) or not all(len(x) == len(y) and all(map(same_value, x, y)) for x, y in zip(ra, rb)):
            return False
    return True


def main():
    git("update-index", "-q", "--refresh")
    changed = [f for f in git("diff", "--name-only").decode().split() if not f.endswith(".png")]
    bad = []
    for f in changed:
        old = git("show", f"HEAD:{f}")
        if f.endswith(".sqlite"):
            ok = same_db(old, ROOT / f)
        else:
            ok = same_text(old.decode("utf-8"), (ROOT / f).read_bytes().decode("utf-8").replace("\r\n", "\n"))
        print("igual con tolerancia" if ok else "DISTINTO", f)
        if not ok:
            bad.append(f)
    print(f"{len(changed)} ficheros con cambios; {len(bad)} distintos más allá de {REL:g} (relativo).")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

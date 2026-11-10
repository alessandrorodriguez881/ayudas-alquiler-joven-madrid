"""Rebuild every result of the project with one command, in the order of «Cómo repetirlo» in the README.

Run:  python scripts/rehacer_todo.py               stops at the first step that fails and shows its error
      python scripts/rehacer_todo.py --comprobar   also lists, with git, the tracked files whose content changed

It downloads nothing: it starts from the CSV files in data/raw/ and the SERPAVI cut in data/interim/. Two steps are left
out on purpose, as the README explains: reading the official PDF files (not in the repository; their result is in
data/interim/topes_900_convocatorias.csv) and the synthetic power simulations (about 13 minutes; results in resultados/).
"""
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
STEPS = [
    "scripts/preparar_datos.py",            # table of 159 municipalities
    "scripts/potencia_umbral.py",           # power table of the preregistration, from the saved simulations
    "scripts/contraste.py",                 # the preregistered test
    "scripts/exploratorio_topes_falsos.py",
    "scripts/necesidad_2024.py",            # 2024 table and need index
    "scripts/requisito_ingresos.py",
    "scripts/habitaciones.py",
    "scripts/panel_ayudas.py",
    "scripts/validacion_fuera_muestra.py",
    "scripts/simulador.py",                 # allocation of the aid under each rule
    "scripts/probar_reglas.py",             # the calculator's rules against hand-made cases
    "scripts/distritos_madrid.py",
    "scripts/base_datos.py",                # SQLite database and its dictionary
    "scripts/ficha_dcat.py",                # DCAT-AP-ES file, validated with SHACL
    "servidor_mcp/probar_servidor.py",      # starts the MCP server and tries its tools
    "scripts/graficos.py",                  # figures and the map of the app
    "scripts/validar_serpavi.py",
    "scripts/incidencias_portal.py",
    "scripts/estudio_art135.py",            # base of the art. 135 study
    "app/probar_app.py",                    # every page of the app, without a browser
]


def changed_files():
    """Tracked files whose content differs from the last commit (git), or None if git is not available."""
    try:
        subprocess.run(["git", "update-index", "-q", "--refresh"], cwd=ROOT, capture_output=True)
        out = subprocess.run(["git", "diff", "--name-only"], cwd=ROOT, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.split()


def main():
    env = {**os.environ, "PYTHONUTF8": "1"}  # Windows: the scripts print «−» and «€» into a pipe
    start = time.time()
    for i, step in enumerate(STEPS, 1):
        t = time.time()
        print(f"[{i:2}/{len(STEPS)}] {step} …", end=" ", flush=True)
        done = subprocess.run([sys.executable, step], cwd=ROOT, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        if done.returncode:
            print("FAILED\n" + done.stdout[-3000:] + "\n" + done.stderr[-5000:])
            sys.exit(f"Stopped at {step} (exit code {done.returncode}).")
        print(f"ok ({time.time() - t:.0f} s)", flush=True)
    print(f"\nAll {len(STEPS)} steps ok in {(time.time() - start) / 60:.1f} min.")
    if "--comprobar" in sys.argv[1:]:
        changed = changed_files()
        if changed is None:
            print("git is not available: nothing to compare.")
        elif changed:
            print(f"{len(changed)} tracked files changed:\n  " + "\n  ".join(changed))
        else:
            print("No tracked file changed: the results in the repository are the ones the code gives.")


if __name__ == "__main__":
    main()

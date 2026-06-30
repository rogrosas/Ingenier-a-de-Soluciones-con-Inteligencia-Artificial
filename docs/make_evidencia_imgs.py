"""
Genera imágenes de evidencia tipo "captura de consola" a partir de la salida
REAL de los componentes (pipeline, pruebas, seguridad, RAG). Se incrustan como
anexo de evidencias en el informe.

Salida: dashboard/charts/ev_01_pipeline.png, ev_02_pruebas.png, ev_03_seg_rag.png
Uso:  python docs/make_evidencia_imgs.py
"""

from __future__ import annotations

import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS = os.path.join(ROOT, "dashboard", "charts")
os.makedirs(CHARTS, exist_ok=True)

BG = "#0c0c0c"
FG = "#d4d4d4"
GREEN = "#3ad900"
CYAN = "#4fc1ff"
AMBER = "#e8a33d"
RED = "#f44747"
TITLEBAR = "#2d2d2d"


def _run(args: list[str]) -> str:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout or "") + (p.stderr or "")


def _color(linea: str) -> str:
    s = linea
    if "PASSED" in s or "passed" in s or s.strip().startswith("✔") or "EVIDENCIA COMPLETA" in s:
        return GREEN
    if s.lstrip().startswith("▶") or "MÉTRICAS" in s or s.strip().startswith("PREGUNTA") \
       or "Fuentes combinadas" in s or s.strip().startswith("==="):
        return CYAN
    if "ERROR" in s or "FAILED" in s or "Traceback" in s:
        return RED
    if "[RUT" in s or "[EMAIL]" in s or "[TARJETA]" in s or "prompt_injection" in s:
        return AMBER
    return FG


def render(lineas: list[str], outpath: str, titulo: str, fontsize: float = 11.0):
    lineas = [l.rstrip("\n") for l in lineas]
    n = len(lineas)
    # Geometría: ancho fijo amplio, alto según nº de líneas
    fig_w = 11.0
    fig_h = max(2.2, 0.30 + n * (fontsize / 58.0) + 0.55)
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=140)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

    # Barra de título estilo terminal
    bar_h = 0.5 / fig_h
    ax.add_patch(plt.Rectangle((0, 1 - bar_h), 1, bar_h, color=TITLEBAR, zorder=1))
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        ax.add_patch(plt.Circle((0.012 + i * 0.016, 1 - bar_h / 2), 0.005, color=c, zorder=2))
    ax.text(0.5, 1 - bar_h / 2, titulo, ha="center", va="center",
            color="#cccccc", fontsize=fontsize - 1, family="monospace", zorder=2)

    # Líneas de texto
    y0 = 1 - bar_h - 0.02
    dy = (y0 - 0.02) / max(1, n)
    for i, linea in enumerate(lineas):
        ax.text(0.012, y0 - i * dy, linea, ha="left", va="top",
                color=_color(linea), fontsize=fontsize, family="monospace", zorder=2)

    fig.savefig(outpath, facecolor=BG, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return outpath


def _pick(texto: str, desde: str | None, hasta: str | None, max_lineas: int) -> list[str]:
    lineas = texto.splitlines()
    if desde:
        for i, l in enumerate(lineas):
            if desde in l:
                lineas = lineas[i:]; break
    if hasta:
        for i, l in enumerate(lineas):
            if hasta in l:
                lineas = lineas[: i + 1]; break
    # quita líneas vacías de relleno excesivas
    return lineas[:max_lineas]


def main():
    print("▶ Ejecutando componentes para capturar salida real…")

    # EV1 — Pipeline + métricas
    out_metrics = _run(["-m", "observability.metrics"])
    ev1 = ["C:\\...\\Banco-Digital-Chile>  python -m observability.metrics", ""]
    ev1 += _pick(out_metrics, "MÉTRICAS DE OBSERVABILIDAD", "Pasos medios por tarea", 16)
    render(ev1, os.path.join(CHARTS, "ev_01_pipeline.png"),
           "Símbolo del sistema — pipeline de observabilidad", fontsize=11)

    # EV2 — Pruebas (pytest)
    out_tests = _run(["-m", "pytest", "tests/", "-v", "--no-header", "-p", "no:cacheprovider"])
    ev2 = ["C:\\...\\Banco-Digital-Chile>  python -m pytest tests/ -v", ""]
    ev2 += _pick(out_tests, "test_guardrails", "passed", 30)
    render(ev2, os.path.join(CHARTS, "ev_02_pruebas.png"),
           "Símbolo del sistema — 22 pruebas (pytest)", fontsize=10)

    # EV3 — Seguridad + RAG
    out_sec = _run(["-m", "security.guardrails"])
    out_rag = _run(["-m", "rag.rag_pipeline"])
    ev3 = ["C:\\...\\Banco-Digital-Chile>  python -m security.guardrails", ""]
    ev3 += _pick(out_sec, "IN :", None, 12)
    ev3 += ["", "C:\\...\\Banco-Digital-Chile>  python -m rag.rag_pipeline", ""]
    ev3 += [l for l in _pick(out_rag, "Base:", None, 16)
            if "RuntimeWarning" not in l and "sys.modules" not in l and "execution of" not in l]
    render(ev3, os.path.join(CHARTS, "ev_03_seg_rag.png"),
           "Símbolo del sistema — seguridad y RAG", fontsize=10)

    print("✔ Evidencias generadas:")
    for f in ("ev_01_pipeline.png", "ev_02_pruebas.png", "ev_03_seg_rag.png"):
        print("   →", os.path.join("dashboard", "charts", f))


if __name__ == "__main__":
    main()

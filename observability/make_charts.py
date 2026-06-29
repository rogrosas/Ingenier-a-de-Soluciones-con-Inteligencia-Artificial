"""
Generación de Gráficos del Dashboard — Banco Digital Chile (IL3.1 / EP3)
========================================================================
Renderiza, a partir de las métricas, las visualizaciones que (a) se incrustan
como evidencia en los informes Word y (b) replican los visuales del dashboard
de Power BI. Salida: PNG en dashboard/charts/.

Uso:
    python -m observability.make_charts
"""

from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from observability import metrics as M
from observability.analyze_traces import anomalias_temporales

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(_ROOT, "dashboard", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# Paleta corporativa sobria
AZUL = "#1f4e79"
AZUL_CLARO = "#5b9bd5"
ROJO = "#c0392b"
VERDE = "#2e7d32"
GRIS = "#7f7f7f"
NARANJA = "#e67e22"

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 130,
})


def _save(fig, nombre):
    ruta = os.path.join(CHARTS_DIR, nombre)
    fig.tight_layout()
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)
    return ruta


def chart_precision_escenario(df):
    esc = M.por_escenario(df).drop(index="seguridad_injection", errors="ignore")
    esc = esc.sort_values("precision_exito")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    colores = [ROJO if v < 0.7 else (NARANJA if v < 0.9 else VERDE)
               for v in esc["precision_exito"]]
    ax.barh(esc.index, esc["precision_exito"] * 100, color=colores)
    for i, v in enumerate(esc["precision_exito"] * 100):
        ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9)
    ax.set_xlim(0, 105)
    ax.axvline(90, color=GRIS, ls="--", lw=1)
    ax.set_xlabel("Tasa de éxito (%)")
    ax.set_title("Precisión por escenario  (umbral objetivo 90%)")
    return _save(fig, "01_precision_por_escenario.png")


def chart_latencia_escenario(df):
    cuellos = M.por_escenario(df).drop(index="seguridad_injection", errors="ignore")
    cuellos = cuellos.sort_values("latencia_p95_ms")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.barh(cuellos.index, cuellos["latencia_p95_ms"], color=AZUL)
    ax.barh(cuellos.index, cuellos["latencia_media_ms"], color=AZUL_CLARO)
    for i, v in enumerate(cuellos["latencia_p95_ms"]):
        ax.text(v + 200, i, f"{v/1000:.1f}s", va="center", fontsize=9)
    ax.set_xlabel("Latencia (ms)")
    ax.set_title("Latencia p95 (azul) vs media (celeste) por escenario")
    ax.legend(["p95", "media"], loc="lower right", frameon=False)
    return _save(fig, "02_latencia_por_escenario.png")


def chart_serie_temporal(df):
    serie = anomalias_temporales(M.serie_diaria(df))
    fig, ax1 = plt.subplots(figsize=(7.5, 3.6))
    x = [str(d)[5:] for d in serie["fecha"]]
    ax1.plot(x, serie["latencia_p95_ms"], color=AZUL, marker="o", ms=4, label="Latencia p95")
    ax1.set_ylabel("Latencia p95 (ms)", color=AZUL)
    ax1.tick_params(axis="y", labelcolor=AZUL)
    ax1.tick_params(axis="x", rotation=60, labelsize=7)

    ax2 = ax1.twinx()
    ax2.plot(x, serie["tasa_error"] * 100, color=ROJO, marker="s", ms=4, label="Tasa de error")
    ax2.set_ylabel("Tasa de error (%)", color=ROJO)
    ax2.tick_params(axis="y", labelcolor=ROJO)
    ax2.spines["top"].set_visible(False)

    # Marca el día de incidente
    anom = serie[serie["anomalia"]]
    for _, r in anom.iterrows():
        idx = list(serie["fecha"]).index(r["fecha"])
        ax1.axvspan(idx - 0.4, idx + 0.4, color=ROJO, alpha=0.12)
        ax1.annotate("Incidente", (idx, r["latencia_p95_ms"]),
                     textcoords="offset points", xytext=(0, 8),
                     ha="center", color=ROJO, fontsize=8, fontweight="bold")
    ax1.set_title("Evolución diaria: latencia p95 y tasa de error")
    return _save(fig, "03_serie_temporal_incidente.png")


def chart_errores(df):
    err = M.errores(df)
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar(err["error_type"], err["n"], color=NARANJA)
    for i, (n, p) in enumerate(zip(err["n"], err["pct"])):
        ax.text(i, n + 0.2, f"{n}\n({p}%)", ha="center", fontsize=8)
    ax.set_ylabel("Nº de ocurrencias")
    ax.set_title("Distribución de errores por tipo")
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    return _save(fig, "04_distribucion_errores.png")


def chart_recursos(df):
    esc = M.por_escenario(df).drop(index="seguridad_injection", errors="ignore")
    esc = esc.sort_values("tokens_medio")
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.barh(esc.index, esc["tokens_medio"], color=VERDE)
    for i, v in enumerate(esc["tokens_medio"]):
        ax.text(v + 20, i, f"{int(v)}", va="center", fontsize=9)
    ax.set_xlabel("Tokens promedio por interacción")
    ax.set_title("Uso de recursos: tokens promedio por escenario")
    return _save(fig, "05_uso_recursos_tokens.png")


def chart_seguridad(df):
    sec = M.seguridad(df)
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    vals = [sec["bloqueados"], sec["bypasses"]]
    labels = [f"Bloqueados\n({sec['bloqueados']})", f"No bloqueados\n({sec['bypasses']})"]
    ax.pie(vals, labels=labels, colors=[VERDE, ROJO], autopct="%1.0f%%",
           startangle=90, wedgeprops={"width": 0.42})
    ax.set_title(f"Prompt-injection: tasa de bloqueo {sec['tasa_bloqueo']*100:.0f}%")
    return _save(fig, "06_seguridad_injection.png")


def generar_todos():
    df = M.load_df()
    rutas = [
        chart_precision_escenario(df),
        chart_latencia_escenario(df),
        chart_serie_temporal(df),
        chart_errores(df),
        chart_recursos(df),
        chart_seguridad(df),
    ]
    return rutas


if __name__ == "__main__":
    rutas = generar_todos()
    print("✔ Gráficos generados:")
    for r in rutas:
        print("  →", os.path.relpath(r, _ROOT))

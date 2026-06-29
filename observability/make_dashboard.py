"""
Captura del Dashboard Integrado — Banco Digital Chile (IL3.1 / EP3)
===================================================================
Compone, en una sola imagen tipo panel, los KPIs y los gráficos clave del
dashboard de monitoreo. Sirve como "captura del dashboard" (evidencia visual)
para los informes y replica el layout del tablero de Power BI.

Requiere que make_charts haya generado los PNG. Salida:
    dashboard/charts/07_dashboard_panel.png

Uso:
    python -m observability.make_dashboard
"""

from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec

from observability import metrics as M

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS = os.path.join(_ROOT, "dashboard", "charts")
OUT = os.path.join(CHARTS, "07_dashboard_panel.png")

AZUL = "#1f4e79"
VERDE = "#2e7d32"
ROJO = "#c0392b"
NARANJA = "#e67e22"


def _kpi(ax, titulo, valor, color):
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.02, 0.08), 0.96, 0.84, transform=ax.transAxes,
                               facecolor="white", edgecolor=color, linewidth=2,
                               zorder=0))
    ax.text(0.5, 0.62, valor, ha="center", va="center", fontsize=17,
            fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.26, titulo, ha="center", va="center", fontsize=8.5,
            color="#333333", transform=ax.transAxes)


def _img(ax, nombre):
    ax.axis("off")
    ruta = os.path.join(CHARTS, nombre)
    if os.path.exists(ruta):
        ax.imshow(mpimg.imread(ruta))


def build():
    df = M.load_df()
    g = M.global_metrics(df)
    sec = M.seguridad(df)

    fig = plt.figure(figsize=(12, 9), facecolor="#f4f6f9")
    gs = GridSpec(4, 4, figure=fig, height_ratios=[0.5, 0.9, 2.4, 2.4],
                  hspace=0.28, wspace=0.12, left=0.03, right=0.97, top=0.95, bottom=0.03)

    # Barra de título
    axt = fig.add_subplot(gs[0, :]); axt.axis("off")
    axt.add_patch(plt.Rectangle((0, 0), 1, 1, transform=axt.transAxes,
                                facecolor=AZUL, zorder=0))
    axt.text(0.01, 0.5, "Dashboard de Monitoreo — Agente “Banco Digital Chile”",
             ha="left", va="center", fontsize=15, fontweight="bold", color="white",
             transform=axt.transAxes)
    axt.text(0.99, 0.5, f"{g['interacciones_totales']} interacciones · 14 días",
             ha="right", va="center", fontsize=10, color="#cfe0f2", transform=axt.transAxes)

    # KPIs
    kpis = [
        ("Precisión (éxito)", f"{g['precision_exito']*100:.1f}%", VERDE),
        ("Tasa de error", f"{g['tasa_error']*100:.1f}%", NARANJA),
        ("Latencia p95", f"{g['latencia_p95_ms']/1000:.1f} s", AZUL),
        ("Bloqueo injection", f"{sec['tasa_bloqueo']*100:.0f}%", ROJO),
    ]
    for i, (t, v, c) in enumerate(kpis):
        _kpi(fig.add_subplot(gs[1, i]), t, v, c)

    # Gráficos (2x2): latencia, serie temporal, errores, seguridad
    _img(fig.add_subplot(gs[2, 0:2]), "02_latencia_por_escenario.png")
    _img(fig.add_subplot(gs[2, 2:4]), "03_serie_temporal_incidente.png")
    _img(fig.add_subplot(gs[3, 0:2]), "01_precision_por_escenario.png")
    _img(fig.add_subplot(gs[3, 2:3]), "04_distribucion_errores.png")
    _img(fig.add_subplot(gs[3, 3:4]), "06_seguridad_injection.png")

    fig.savefig(OUT, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print("✔ Panel de dashboard:", os.path.relpath(build(), _ROOT))

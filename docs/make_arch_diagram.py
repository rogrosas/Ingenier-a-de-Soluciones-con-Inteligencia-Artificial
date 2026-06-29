"""
Diagrama de arquitectura de la solución (PNG) para el Informe Final Transversal.
Dibuja las capas: Seguridad → Agente (LLM+RAG+Tools+Memoria+Planificación) →
Orquestación → Observabilidad. Salida: dashboard/charts/00_arquitectura.png
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dashboard", "charts", "00_arquitectura.png")

AZUL = "#1f4e79"
AZUL2 = "#2e6da4"
CELESTE = "#d6e4f0"
VERDE = "#2e7d32"
VERDE_BG = "#e3f2e4"
NARANJA = "#e67e22"
NAR_BG = "#fdf0e3"
GRIS_BG = "#eef1f5"


def caja(ax, x, y, w, h, titulo, sub="", fc=CELESTE, ec=AZUL, fs=10, tc=AZUL):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                         linewidth=1.4, edgecolor=ec, facecolor=fc)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.26, titulo, ha="center", va="top",
            fontsize=fs, fontweight="bold", color=tc)
    if sub:
        ax.text(x + w / 2, y + h - 0.58, sub, ha="center", va="top",
                fontsize=fs - 1.5, color="#333333")


def flecha(ax, x1, y1, x2, y2, texto="", color=AZUL):
    ar = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                         linewidth=1.6, color=color)
    ax.add_patch(ar)
    if texto:
        ax.text((x1 + x2) / 2 + 0.15, (y1 + y2) / 2, texto, fontsize=7.5,
                color=color, style="italic", ha="left", va="center")


def build():
    fig, ax = plt.subplots(figsize=(9.2, 7.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 12); ax.axis("off")

    ax.text(6, 11.6, "Arquitectura de la Solución — Agente “Banco Digital Chile”",
            ha="center", fontsize=13, fontweight="bold", color=AZUL)

    # Cliente
    caja(ax, 4.5, 10.4, 3, 0.8, "Cliente / Canal de atención", fc="#ffffff", fs=10)

    # Seguridad
    caja(ax, 2.5, 9.0, 7, 0.95, "Capa de Seguridad y Uso Responsable",
         "Enmascaramiento PII · Anti prompt-injection · Rate-limit · Auditoría (hash-chain)",
         fc=NAR_BG, ec=NARANJA, tc=NARANJA, fs=10)

    # Agente principal (contenedor)
    caja(ax, 0.6, 3.7, 10.8, 4.9, "Agente Principal — LangChain AgentExecutor (ReAct)  +  LLM gpt-4o",
         "", fc=GRIS_BG, ec=AZUL, fs=10.5)

    # Sub-bloques dentro del agente
    caja(ax, 1.0, 6.5, 5.0, 1.45, "Diseño LLM + RAG  (RA1)",
         "Prompt engineering (zero/few-shot, CoT)\nPipeline RAG sobre base de productos y políticas",
         fc=CELESTE, fs=9.5)
    caja(ax, 6.2, 6.5, 5.0, 1.45, "Memoria  (RA2)",
         "Corto plazo: ventana k=5\nLargo plazo: JSON persistente por RUT",
         fc=CELESTE, fs=9.5)

    caja(ax, 1.0, 4.9, 5.0, 1.35, "Herramientas (consulta/escritura/razonamiento)",
         "saldo · transferencia · crédito · reclamo · producto",
         fc="#ffffff", fs=9)
    caja(ax, 6.2, 4.9, 5.0, 1.35, "Planificación y Orquestación  (RA2)",
         "Plan-and-Execute · CrewAI (4 agentes:\nGerente, Analista, Asesor, Operaciones)",
         fc="#ffffff", fs=9)

    # Observabilidad
    caja(ax, 0.6, 1.9, 10.8, 1.4, "Capa de Observabilidad, Trazabilidad y Métricas  (RA3)",
         "Tracer → logs JSONL → métricas (precisión/latencia/consistencia) → análisis de "
         "trazabilidad → Dashboard Power BI",
         fc=VERDE_BG, ec=VERDE, tc=VERDE, fs=10)

    # Flechas verticales
    flecha(ax, 6, 10.4, 6, 9.95, "consulta")
    flecha(ax, 6, 9.0, 6, 8.6, "texto saneado")
    flecha(ax, 6, 3.7, 6, 3.3, "cada paso instrumentado")
    # respuesta de regreso
    flecha(ax, 9.6, 9.0, 9.6, 10.4, "respuesta", color=VERDE)

    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print("✔ Diagrama:", os.path.relpath(build(), ROOT))

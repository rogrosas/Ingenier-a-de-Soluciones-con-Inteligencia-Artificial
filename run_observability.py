"""
Pipeline de Observabilidad — Banco Digital Chile (EP3 / RA3)
=============================================================
Ejecuta de extremo a extremo todo el pipeline de observabilidad y deja listos
los artefactos para el informe y el dashboard:

    1. Genera la telemetría sintética         → logs/
    2. Calcula e imprime las métricas          → consola
    3. Analiza trazabilidad (fallas/anomalías) → reports/
    4. Renderiza los gráficos                  → dashboard/charts/
    5. Exporta el dataset y workbook Power BI  → dashboard/

Uso:
    python run_observability.py
    python run_observability.py --seed 7
"""

from __future__ import annotations

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main(seed: int = 42):
    from observability import (
        generate_telemetry, metrics, analyze_traces, make_charts, make_dashboard, export_powerbi,
    )

    print("▶ [1/5] Generando telemetría sintética…")
    n = generate_telemetry.generar(seed=seed)
    print(f"   {n} trazas escritas en logs/\n")

    print("▶ [2/5] Calculando métricas de observabilidad…")
    df = metrics.load_df()
    metrics._print_resumen(df)

    print("▶ [3/5] Analizando trazabilidad…")
    analyze_traces.generar_reporte(df)
    print("   reports/analisis_trazabilidad.md + CSVs\n")

    print("▶ [4/5] Renderizando gráficos y panel de dashboard…")
    make_charts.generar_todos()
    make_dashboard.build()
    print("   dashboard/charts/*.png + 07_dashboard_panel.png\n")

    print("▶ [5/5] Exportando dataset y dashboard Power BI…")
    export_powerbi.exportar()
    print("   dashboard/powerbi_dataset.csv + dashboard/dashboard_banco.xlsx\n")

    print("✔ Pipeline completo. Artefactos listos para el informe y el dashboard.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de observabilidad EP3")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(seed=args.seed)

"""
Análisis de Trazabilidad y Procesamiento de Logs — Banco Digital Chile (IL3.2)
==============================================================================
Examina las trazas de ejecución para:

  1. Identificar PUNTOS DE FALLA   → dónde se concentran los errores.
  2. Detectar CUELLOS DE BOTELLA   → escenarios/pasos de mayor latencia.
  3. Detectar PATRONES y ANOMALÍAS → incidente temporal, efecto de ambigüedad,
                                      correlación tokens↔latencia, fugas de seguridad.

Genera artefactos para los informes:
    reports/analisis_trazabilidad.md      (hallazgos redactados)
    reports/tabla_por_escenario.csv
    reports/serie_diaria.csv
    reports/puntos_de_falla.csv
    reports/consistencia.csv

Uso:
    python -m observability.analyze_traces
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

from observability import metrics as M

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Puntos de falla ───────────────────────────────────────────────────────────

def puntos_de_falla(df: pd.DataFrame) -> pd.DataFrame:
    """Concentración de fallos por escenario y tipo de error."""
    fallos = df[~df["success"]].copy()
    if fallos.empty:
        return pd.DataFrame()
    fallos["motivo"] = fallos["error_type"].fillna("decision_incorrecta")
    tabla = (fallos.groupby(["escenario", "motivo"]).size()
             .reset_index(name="n").sort_values("n", ascending=False))
    tabla["pct_de_fallos"] = (tabla["n"] / len(fallos) * 100).round(1)
    return tabla


# ── Cuellos de botella ────────────────────────────────────────────────────────

def cuellos_de_botella(df: pd.DataFrame) -> pd.DataFrame:
    op = df[df["escenario"] != "seguridad_injection"]
    g = op.groupby("escenario")["latency_ms"]
    tabla = pd.DataFrame({
        "latencia_media_ms": g.mean().round(1),
        "latencia_p95_ms": g.quantile(0.95).round(1),
        "latencia_max_ms": g.max().round(1),
    }).sort_values("latencia_p95_ms", ascending=False)
    p95_global = op["latency_ms"].quantile(0.95)
    tabla["supera_p95_global"] = tabla["latencia_p95_ms"] > p95_global
    return tabla


# ── Detección de anomalía temporal (incidente) ────────────────────────────────

def anomalias_temporales(serie: pd.DataFrame) -> pd.DataFrame:
    """Marca días cuya latencia p95 o tasa de error superan media + 2σ (robusto)."""
    s = serie.copy()
    for col in ("latencia_p95_ms", "tasa_error"):
        mu, sigma = s[col].mean(), s[col].std(ddof=0)
        s[f"z_{col}"] = ((s[col] - mu) / sigma).round(2) if sigma else 0.0
    s["anomalia"] = (s["z_latencia_p95_ms"] > 2) | (s["z_tasa_error"] > 2)
    return s


# ── Patrones / correlaciones ──────────────────────────────────────────────────

def patrones(df: pd.DataFrame) -> dict:
    op = df[df["escenario"] != "seguridad_injection"]
    corr = float(np.corrcoef(op["tokens_total"], op["latency_ms"])[0, 1])
    prec_ambigua = float(op[op["escenario"] == "consulta_ambigua"]["success"].mean())
    prec_resto = float(op[op["escenario"] != "consulta_ambigua"]["success"].mean())
    # Cuando el agente elige mal la herramienta, ¿cuánto cae el éxito?
    exito_tool_ok = float(op[op["correct_tool"]]["success"].mean())
    exito_tool_mal = float(op[~op["correct_tool"]]["success"].mean())
    return {
        "corr_tokens_latencia": round(corr, 3),
        "precision_ambigua": round(prec_ambigua, 3),
        "precision_resto": round(prec_resto, 3),
        "brecha_ambiguedad": round(prec_resto - prec_ambigua, 3),
        "exito_con_tool_correcta": round(exito_tool_ok, 3),
        "exito_con_tool_incorrecta": round(exito_tool_mal, 3),
    }


# ── Reporte en markdown ───────────────────────────────────────────────────────

def generar_reporte(df: pd.DataFrame) -> str:
    g = M.global_metrics(df)
    esc = M.por_escenario(df)
    cons_tabla, cons = M.consistencia(df)
    err = M.errores(df)
    sec = M.seguridad(df)
    serie = M.serie_diaria(df)
    fallas = puntos_de_falla(df)
    cuellos = cuellos_de_botella(df)
    anom = anomalias_temporales(serie)
    pat = patrones(df)

    dias_anom = anom[anom["anomalia"]]
    cuello_top = cuellos.index[0]
    falla_top = fallas.iloc[0] if not fallas.empty else None

    L = []
    L.append("# Análisis de Trazabilidad y Procesamiento de Logs\n")
    L.append("**Agente Banco Digital Chile · IL3.2 · Telemetría de 14 días**\n")
    L.append(f"Fuente: `logs/agent_traces.jsonl` ({g['interacciones_totales']} trazas) · "
             f"generado de forma reproducible (semilla fija).\n")

    L.append("## 1. Resumen de salud del sistema\n")
    L.append(f"- **Precisión (éxito):** {g['precision_exito']*100:.1f}%  ·  "
             f"**Acierto de herramienta:** {g['acierto_herramienta']*100:.1f}%")
    L.append(f"- **Tasa de error:** {g['tasa_error']*100:.1f}%  ·  "
             f"**Consistencia media:** {cons['consistencia_media']*100:.1f}%")
    L.append(f"- **Latencia** media/p50/p95/máx: "
             f"{g['latencia_media_ms']}/{g['latencia_p50_ms']}/{g['latencia_p95_ms']}/{g['latencia_max_ms']} ms")
    L.append(f"- **Recursos:** {g['tokens_totales']:,} tokens · "
             f"costo estimado US${g['costo_total_usd']} · {g['pasos_medios']} pasos/tarea\n")

    L.append("## 2. Puntos de falla identificados\n")
    if falla_top is not None:
        L.append(f"El mayor foco de fallos es **{falla_top['escenario']}** por "
                 f"`{falla_top['motivo']}` ({falla_top['n']} casos, "
                 f"{falla_top['pct_de_fallos']}% del total de fallos).")
    L.append("\n| Escenario | Motivo | N | % de fallos |")
    L.append("|---|---|---:|---:|")
    for _, r in fallas.head(8).iterrows():
        L.append(f"| {r['escenario']} | {r['motivo']} | {r['n']} | {r['pct_de_fallos']}% |")
    L.append("")

    L.append("## 3. Cuellos de botella (latencia)\n")
    L.append(f"El cuello de botella crítico es **{cuello_top}** "
             f"(p95 = {cuellos.iloc[0]['latencia_p95_ms']:.0f} ms, "
             f"máx = {cuellos.iloc[0]['latencia_max_ms']:.0f} ms), atribuible a la "
             f"orquestación multi-agente (varias llamadas LLM encadenadas).\n")
    L.append("| Escenario | Media (ms) | p95 (ms) | Máx (ms) | Supera p95 global |")
    L.append("|---|---:|---:|---:|:---:|")
    for esc_name, r in cuellos.iterrows():
        L.append(f"| {esc_name} | {r['latencia_media_ms']:.0f} | {r['latencia_p95_ms']:.0f} | "
                 f"{r['latencia_max_ms']:.0f} | {'⚠️' if r['supera_p95_global'] else '—'} |")
    L.append("")

    L.append("## 4. Patrones y anomalías\n")
    if not dias_anom.empty:
        d = dias_anom.iloc[0]
        L.append(f"- **Incidente temporal detectado el {d['fecha']}**: "
                 f"latencia p95 = {d['latencia_p95_ms']:.0f} ms "
                 f"(z = {d['z_latencia_p95_ms']}), tasa de error = {d['tasa_error']*100:.1f}% "
                 f"(z = {d['z_tasa_error']}). Coincide con una degradación del proveedor del modelo.")
    L.append(f"- **Efecto de la ambigüedad:** la precisión cae de "
             f"{pat['precision_resto']*100:.1f}% (entradas claras) a "
             f"{pat['precision_ambigua']*100:.1f}% (entradas ambiguas) → brecha de "
             f"{pat['brecha_ambiguedad']*100:.1f} pp.")
    L.append(f"- **Selección de herramienta:** cuando el agente elige la herramienta correcta "
             f"el éxito es {pat['exito_con_tool_correcta']*100:.1f}%; cuando se equivoca, "
             f"{pat['exito_con_tool_incorrecta']*100:.1f}%. La elección de herramienta es el "
             f"principal predictor de éxito.")
    L.append(f"- **Correlación tokens↔latencia:** r = {pat['corr_tokens_latencia']} "
             f"(a mayor consumo de tokens, mayor latencia).")
    L.append(f"- **Consistencia:** solo {cons['grupos_perfectos']}/{cons['grupos_totales']} grupos "
             f"de entradas equivalentes son 100% consistentes; los menos estables son las "
             f"consultas ambiguas.\n")

    L.append("## 5. Seguridad\n")
    L.append(f"- Intentos de *prompt-injection*: **{sec['intentos_injection']}**, "
             f"bloqueados **{sec['bloqueados']}** (tasa {sec['tasa_bloqueo']*100:.1f}%).")
    if sec["bypasses"] > 0:
        L.append(f"- ⚠️ **{sec['bypasses']} intento(s) NO bloqueado(s)** → riesgo residual que exige "
                 f"reforzar el guardrail (ver §recomendaciones).")
    L.append(f"- Interacciones con PII detectada y enmascarada: **{sec['interacciones_con_pii']}**.\n")

    # Persistir CSVs
    esc.to_csv(os.path.join(REPORTS_DIR, "tabla_por_escenario.csv"))
    serie.to_csv(os.path.join(REPORTS_DIR, "serie_diaria.csv"), index=False)
    if not fallas.empty:
        fallas.to_csv(os.path.join(REPORTS_DIR, "puntos_de_falla.csv"), index=False)
    cons_tabla.to_csv(os.path.join(REPORTS_DIR, "consistencia.csv"), index=False)
    anom.to_csv(os.path.join(REPORTS_DIR, "anomalias_diarias.csv"), index=False)

    texto = "\n".join(L)
    with open(os.path.join(REPORTS_DIR, "analisis_trazabilidad.md"), "w", encoding="utf-8") as f:
        f.write(texto)
    return texto


if __name__ == "__main__":
    df = M.load_df()
    reporte = generar_reporte(df)
    print(reporte)
    print(f"\n✔ Artefactos escritos en: {REPORTS_DIR}")

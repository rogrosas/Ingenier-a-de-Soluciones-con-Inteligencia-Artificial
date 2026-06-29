"""
Métricas de Observabilidad — Banco Digital Chile (IL3.1)
========================================================
Calcula, a partir de las trazas JSONL, las métricas exigidas por la rúbrica:

    Precisión        → tasa de éxito (success) y acierto de herramienta
    Latencia         → media, p50, p95, máx (global y por escenario)
    Consistencia     → estabilidad de la decisión ante entradas equivalentes
    Frecuencia error → tasa de error y desglose por tipo
    Uso de recursos  → tokens, costo estimado y nº de pasos

Diseñado para usarse como librería (devuelve DataFrames) y como CLI
(`python -m observability.metrics`) que imprime un resumen ejecutivo.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from observability.instrumentation import load_traces

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ── Carga ─────────────────────────────────────────────────────────────────────

def load_df(path: str | None = None) -> pd.DataFrame:
    """Carga las trazas como DataFrame con columnas derivadas (fecha, hora)."""
    registros = load_traces(path) if path else load_traces()
    if not registros:
        raise FileNotFoundError(
            "No hay trazas. Ejecuta primero: python -m observability.generate_telemetry"
        )
    df = pd.DataFrame(registros)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["fecha"] = df["timestamp"].dt.date
    df["hora"] = df["timestamp"].dt.hour
    df["n_tools"] = df["tools_called"].apply(len)
    return df


# ── Métricas globales ─────────────────────────────────────────────────────────

def global_metrics(df: pd.DataFrame) -> dict:
    """Diccionario de KPIs globales del agente."""
    operativos = df[df["escenario"] != "seguridad_injection"]
    lat = operativos["latency_ms"]
    return {
        "interacciones_totales": int(len(df)),
        "interacciones_operativas": int(len(operativos)),
        "precision_exito": round(float(operativos["success"].mean()), 4),
        "acierto_herramienta": round(float(operativos["correct_tool"].mean()), 4),
        "tasa_error": round(float((operativos["error_type"].notna()).mean()), 4),
        "latencia_media_ms": round(float(lat.mean()), 1),
        "latencia_p50_ms": round(float(lat.quantile(0.50)), 1),
        "latencia_p95_ms": round(float(lat.quantile(0.95)), 1),
        "latencia_max_ms": round(float(lat.max()), 1),
        "tokens_totales": int(df["tokens_total"].sum()),
        "tokens_media": round(float(df["tokens_total"].mean()), 1),
        "costo_total_usd": round(float(df["cost_usd"].sum()), 4),
        "costo_medio_usd": round(float(df["cost_usd"].mean()), 5),
        "pasos_medios": round(float(operativos["n_steps"].mean()), 2),
    }


# ── Métricas por escenario ────────────────────────────────────────────────────

def por_escenario(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("escenario")
    tabla = pd.DataFrame({
        "n": g.size(),
        "precision_exito": g["success"].mean().round(3),
        "acierto_herramienta": g["correct_tool"].mean().round(3),
        "tasa_error": g["error_type"].apply(lambda s: s.notna().mean()).round(3),
        "latencia_media_ms": g["latency_ms"].mean().round(1),
        "latencia_p95_ms": g["latency_ms"].quantile(0.95).round(1),
        "tokens_medio": g["tokens_total"].mean().round(0),
        "costo_usd": g["cost_usd"].sum().round(4),
    })
    return tabla.sort_values("latencia_p95_ms", ascending=False)


# ── Consistencia ──────────────────────────────────────────────────────────────

def consistencia(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Mide estabilidad ante entradas EQUIVALENTES (mismo escenario+variante).
    - consistencia_decision: fracción de runs del grupo que coinciden con la
      decisión modal (success ∧ correct_tool). 1.0 = totalmente consistente.
    - cv_latencia: coeficiente de variación de la latencia (dispersión relativa).
    """
    op = df[df["escenario"] != "seguridad_injection"].copy()
    op["decision_ok"] = op["success"] & op["correct_tool"]

    filas = []
    for (esc, var), grupo in op.groupby(["escenario", "variante"]):
        n = len(grupo)
        modal = grupo["decision_ok"].mode()
        modal_val = bool(modal.iloc[0]) if not modal.empty else True
        consist = float((grupo["decision_ok"] == modal_val).mean())
        cv = float(grupo["latency_ms"].std(ddof=0) / grupo["latency_ms"].mean()) if grupo["latency_ms"].mean() else 0.0
        filas.append({
            "escenario": esc, "variante": var, "n": n,
            "consistencia_decision": round(consist, 3),
            "cv_latencia": round(cv, 3),
        })
    tabla = pd.DataFrame(filas)
    resumen = {
        "consistencia_media": round(float(tabla["consistencia_decision"].mean()), 4),
        "grupos_perfectos": int((tabla["consistencia_decision"] == 1.0).sum()),
        "grupos_totales": int(len(tabla)),
        "cv_latencia_medio": round(float(tabla["cv_latencia"].mean()), 4),
    }
    return tabla.sort_values("consistencia_decision"), resumen


# ── Errores ───────────────────────────────────────────────────────────────────

def errores(df: pd.DataFrame) -> pd.DataFrame:
    err = df[df["error_type"].notna()]
    if err.empty:
        return pd.DataFrame(columns=["error_type", "n", "pct"])
    tabla = (err.groupby("error_type").size()
             .reset_index(name="n").sort_values("n", ascending=False))
    tabla["pct"] = (tabla["n"] / len(df) * 100).round(2)
    return tabla


# ── Seguridad ─────────────────────────────────────────────────────────────────

def seguridad(df: pd.DataFrame) -> dict:
    sec = df[df["escenario"] == "seguridad_injection"]
    pii = df["pii_detected"].sum()
    bypass = int((~sec["injection_blocked"]).sum()) if not sec.empty else 0
    return {
        "intentos_injection": int(len(sec)),
        "bloqueados": int(sec["injection_blocked"].sum()) if not sec.empty else 0,
        "tasa_bloqueo": round(float(sec["injection_blocked"].mean()), 3) if not sec.empty else 0.0,
        "bypasses": bypass,
        "interacciones_con_pii": int(pii),
    }


# ── Serie temporal diaria (para detección de incidentes) ──────────────────────

def serie_diaria(df: pd.DataFrame) -> pd.DataFrame:
    op = df[df["escenario"] != "seguridad_injection"]
    g = op.groupby("fecha")
    return pd.DataFrame({
        "n": g.size(),
        "precision_exito": g["success"].mean().round(3),
        "tasa_error": g["error_type"].apply(lambda s: s.notna().mean()).round(3),
        "latencia_media_ms": g["latency_ms"].mean().round(1),
        "latencia_p95_ms": g["latency_ms"].quantile(0.95).round(1),
        "tokens": g["tokens_total"].sum(),
    }).reset_index()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_resumen(df: pd.DataFrame) -> None:
    g = global_metrics(df)
    print("\n" + "=" * 64)
    print("  MÉTRICAS DE OBSERVABILIDAD — Banco Digital Chile")
    print("=" * 64)
    print(f"Interacciones totales      : {g['interacciones_totales']}")
    print(f"Precisión (tasa de éxito)  : {g['precision_exito']*100:.1f}%")
    print(f"Acierto de herramienta     : {g['acierto_herramienta']*100:.1f}%")
    print(f"Tasa de error              : {g['tasa_error']*100:.1f}%")
    print(f"Latencia media / p50 / p95 : {g['latencia_media_ms']} / {g['latencia_p50_ms']} / {g['latencia_p95_ms']} ms")
    print(f"Latencia máxima            : {g['latencia_max_ms']} ms")
    print(f"Tokens totales / medio     : {g['tokens_totales']:,} / {g['tokens_media']}")
    print(f"Costo estimado total       : US${g['costo_total_usd']}")
    print(f"Pasos medios por tarea     : {g['pasos_medios']}")

    print("\n── Por escenario " + "─" * 47)
    print(por_escenario(df).to_string())

    _, cons = consistencia(df)
    print("\n── Consistencia " + "─" * 48)
    print(f"Consistencia media         : {cons['consistencia_media']*100:.1f}%")
    print(f"Grupos perfectos           : {cons['grupos_perfectos']}/{cons['grupos_totales']}")
    print(f"CV de latencia medio       : {cons['cv_latencia_medio']}")

    print("\n── Errores " + "─" * 53)
    print(errores(df).to_string(index=False))

    print("\n── Seguridad " + "─" * 51)
    for k, v in seguridad(df).items():
        print(f"{k:28s}: {v}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    _print_resumen(load_df())

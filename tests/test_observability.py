"""Pruebas de la capa de observabilidad (instrumentación + métricas + trazabilidad)."""

import pytest

from observability import generate_telemetry, metrics
from observability.instrumentation import Tracer, load_traces
from observability.analyze_traces import patrones, anomalias_temporales, puntos_de_falla


@pytest.fixture(scope="module")
def df():
    # Telemetría reproducible (semilla fija) compartida por las pruebas.
    generate_telemetry.generar(seed=42)
    return metrics.load_df()


def test_tracer_genera_traza_con_pii_enmascarada():
    tr = Tracer(escenario="consulta_saldo", variante="v1", intent="consultar_saldo",
                expected_tool="consultar_saldo", input_text="Mi RUT es 12.345.678-9")
    with tr.step("consultar_saldo"):
        pass
    traza = tr.finish(output_text="Saldo $2.450.000", success=True, correct_tool=True)
    assert "12.345.678-9" not in traza.input_text
    assert traza.latency_ms > 0
    assert traza.n_steps == 1


def test_telemetria_reproducible(df):
    assert len(df) > 500
    # Misma semilla → mismo número de trazas
    assert len(load_traces()) == len(df)


def test_metricas_globales_en_rango(df):
    g = metrics.global_metrics(df)
    assert 0 <= g["precision_exito"] <= 1
    assert 0 <= g["tasa_error"] <= 1
    assert g["latencia_p95_ms"] >= g["latencia_p50_ms"]
    assert g["tokens_totales"] > 0


def test_consistencia(df):
    tabla, resumen = metrics.consistencia(df)
    assert 0 <= resumen["consistencia_media"] <= 1
    assert resumen["grupos_totales"] > 0


def test_seguridad_detecta_intentos(df):
    sec = metrics.seguridad(df)
    assert sec["intentos_injection"] > 0
    assert 0 <= sec["tasa_bloqueo"] <= 1


def test_patrones_brecha_ambiguedad(df):
    pat = patrones(df)
    # Las entradas ambiguas deben tener menor precisión que el resto.
    assert pat["precision_ambigua"] < pat["precision_resto"]


def test_anomalia_temporal_detectada(df):
    anom = anomalias_temporales(metrics.serie_diaria(df))
    assert anom["anomalia"].sum() >= 1  # el incidente inyectado se detecta


def test_puntos_de_falla(df):
    fallas = puntos_de_falla(df)
    assert not fallas.empty
    assert {"escenario", "motivo", "n"}.issubset(fallas.columns)

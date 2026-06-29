"""
Generador del Informe EP3 (Word) — Implementación de Observabilidad
====================================================================
Construye el informe técnico de la Evaluación Parcial N°3 (≤5 páginas),
leyendo las MÉTRICAS REALES del pipeline de observabilidad para que las cifras
del documento coincidan exactamente con los artefactos generados.

Uso:
    python -m observability.run_observability   # (genera datos y gráficos)
    python docs/build_ep3.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docs._docx_helpers import (
    ROOT, nuevo_documento, bloque_titulo, set_page_numbers,
    h1, h2, parrafo, rico, vinneta, numerada, tabla, figura, caja, salto_pagina,
)
from observability import metrics as M
from observability.analyze_traces import patrones, anomalias_temporales, puntos_de_falla

AUTORES = "Roger Rosas · Rodrigo Santis · Edgardo Gutiérrez"
FECHA = "Junio 2025"
ENTREGA = os.path.join(ROOT, "entrega"); os.makedirs(ENTREGA, exist_ok=True)
SALIDA = os.path.join(ENTREGA, "EP3_Observabilidad_BancoDigitalChile.docx")


def pct(x): return f"{x*100:.1f}%"


def build():
    df = M.load_df()
    g = M.global_metrics(df)
    esc = M.por_escenario(df)
    _, cons = M.consistencia(df)
    err = M.errores(df)
    sec = M.seguridad(df)
    serie = M.serie_diaria(df)
    anom = anomalias_temporales(serie)
    pat = patrones(df)
    fallas = puntos_de_falla(df)

    doc = nuevo_documento()
    set_page_numbers(doc, "EP3 · Observabilidad · Banco Digital Chile · ISY0101")

    bloque_titulo(
        doc,
        titulo="Implementación de Observabilidad",
        subtitulo="Agente conversacional “Banco Digital Chile”",
        sigla="ISY0101 · Ingeniería de Soluciones con IA",
        autores=AUTORES, fecha=FECHA,
        ponderacion="Evaluación Parcial N°3 · 35%",
    )

    # ── 1. Contexto ───────────────────────────────────────────────────────────
    h1(doc, "1. Contexto y alcance")
    parrafo(doc,
        "Este informe documenta la tercera fase del proyecto: la incorporación de "
        "observabilidad, trazabilidad y seguridad al agente bancario desarrollado en "
        "las evaluaciones previas. El agente —construido con LangChain (ciclo ReAct) y "
        "CrewAI para orquestación multi-agente— resuelve tareas de banca digital "
        "(consulta de saldo, transferencias, simulación de créditos, reclamos e "
        "información de productos) mediante cinco herramientas, memoria de corto y "
        "largo plazo y planificación multi-etapa.")
    rico(doc, [
        ("Para medir su comportamiento en producción se instrumentó cada interacción con "
         "un ", False),
        ("tracer", True),
        (" que emite trazas estructuradas en formato JSONL "
         "(", False),
        ("logs/agent_traces.jsonl", True),
        (") más un log legible (", False),
        ("logs/agent.log", True),
        ("). Sobre esa telemetría —", False),
        (f"{g['interacciones_totales']} interacciones simuladas de forma reproducible "
         "durante 14 días de operación", True),
        ("— se calculan las métricas, se analizan los registros y se construye el "
         "dashboard de monitoreo.", False),
    ])

    # ── 2. Métricas (IE1, IE2) ────────────────────────────────────────────────
    h1(doc, "2. Implementación de métricas de observabilidad")
    parrafo(doc,
        "Se implementaron cinco métricas relevantes, agrupadas en las dos dimensiones "
        "exigidas: calidad de las respuestas y eficiencia operacional.")
    vinneta(doc, [
        [("Precisión: ", True), ("tasa de éxito de la tarea y acierto en la selección de "
         "herramienta respecto a una verdad de referencia (ground truth).", False)],
        [("Consistencia: ", True), ("estabilidad de la decisión ante entradas equivalentes "
         "(mismo escenario y variante ejecutados múltiples veces).", False)],
        [("Frecuencia de errores: ", True), ("proporción y tipo de fallos (timeout, "
         "rate-limit, parsing, validación, E/S).", False)],
        [("Latencia: ", True), ("tiempo de respuesta extremo a extremo (media, p50, p95, máx).", False)],
        [("Uso de recursos: ", True), ("tokens consumidos, costo estimado y número de pasos "
         "por tarea.", False)],
    ])

    caja(doc, "KPIs globales del agente (14 días · "
              f"{g['interacciones_totales']} interacciones)",
        f"Precisión (éxito): {pct(g['precision_exito'])}   ·   "
        f"Acierto de herramienta: {pct(g['acierto_herramienta'])}   ·   "
        f"Consistencia: {pct(cons['consistencia_media'])}   ·   "
        f"Tasa de error: {pct(g['tasa_error'])}\n"
        f"Latencia media/p95/máx: {g['latencia_media_ms']:.0f} / {g['latencia_p95_ms']:.0f} / "
        f"{g['latencia_max_ms']:.0f} ms   ·   "
        f"Tokens: {g['tokens_totales']:,}   ·   Costo estimado: US${g['costo_total_usd']:.2f}")

    parrafo(doc, "El desglose por escenario revela un comportamiento heterogéneo:", space_after=4)
    filas = []
    nombres = {
        "consulta_saldo": "Consulta de saldo", "info_producto": "Info. de producto",
        "simulacion_credito": "Simulación crédito", "transferencia": "Transferencia",
        "registro_reclamo": "Registro reclamo", "multiagente_credito": "Multi-agente crédito",
        "consulta_ambigua": "Consulta ambigua", "seguridad_injection": "Intento injection",
    }
    for nombre, r in esc.iterrows():
        filas.append([
            nombres.get(nombre, nombre), int(r["n"]),
            pct(r["precision_exito"]), pct(r["acierto_herramienta"]),
            pct(r["tasa_error"]), f"{r['latencia_p95_ms']:.0f}",
            f"{int(r['tokens_medio'])}",
        ])
    tabla(doc,
        ["Escenario", "N", "Precisión", "Acierto herr.", "Tasa error", "Latencia p95 (ms)", "Tokens medio"],
        filas, anchos=[1.7, 0.5, 0.85, 0.95, 0.85, 1.25, 0.95], size=8.5,
        fuente_resaltar_col0=True)

    figura(doc, "02_latencia_por_escenario.png",
           "Figura 1. Latencia p95 vs. media por escenario. La orquestación multi-agente "
           "concentra la latencia del sistema.", width=5.6)

    # ── 3. Trazabilidad (IE3, IE4) ────────────────────────────────────────────
    h1(doc, "3. Análisis de registros y trazabilidad")
    falla_top = fallas.iloc[0]
    cuello = esc.index[0]
    rico(doc, [
        ("El procesamiento de los logs (módulo ", False), ("analyze_traces", True),
        (") examina cada evento para localizar puntos de falla, cuellos de botella y "
         "anomalías. Los hallazgos principales son:", False),
    ])
    dia_anom = anom[anom["anomalia"]]
    items = [
        [("Punto de falla dominante: ", True),
         (f"el escenario «{nombres.get(falla_top['escenario'], falla_top['escenario'])}» "
          f"por {falla_top['motivo'].replace('_',' ')} concentra el "
          f"{falla_top['pct_de_fallos']:.0f}% de los fallos.", False)],
        [("Cuello de botella: ", True),
         (f"«{nombres.get(cuello, cuello)}» con p95 de {esc.iloc[0]['latencia_p95_ms']:.0f} ms, "
          "por las múltiples llamadas LLM encadenadas de la orquestación.", False)],
        [("Predictor de éxito: ", True),
         (f"cuando el agente elige la herramienta correcta el éxito es "
          f"{pct(pat['exito_con_tool_correcta'])}; cuando se equivoca, "
          f"{pct(pat['exito_con_tool_incorrecta'])}. La selección de herramienta es el "
          "factor decisivo.", False)],
        [("Efecto de la ambigüedad: ", True),
         (f"ante entradas claras la precisión es {pct(pat['precision_resto'])}, pero cae a "
          f"{pct(pat['precision_ambigua'])} con entradas ambiguas (brecha de "
          f"{pat['brecha_ambiguedad']*100:.0f} pp).", False)],
        [("Correlación recursos–latencia: ", True),
         (f"r = {pat['corr_tokens_latencia']} entre tokens y latencia.", False)],
    ]
    if not dia_anom.empty:
        d = dia_anom.iloc[0]
        items.insert(0, [
            ("Anomalía temporal: ", True),
            (f"el {d['fecha']} se detectó un incidente (latencia p95 {d['latencia_p95_ms']:.0f} ms, "
             f"z={d['z_latencia_p95_ms']}; error {pct(d['tasa_error'])}, z={d['z_tasa_error']}), "
             "compatible con una degradación del proveedor del modelo.", False)],
        )
    vinneta(doc, items)

    figura(doc, "03_serie_temporal_incidente.png",
           "Figura 2. Evolución diaria de latencia p95 y tasa de error; el área sombreada "
           "marca el incidente detectado automáticamente.", width=6.0)

    parrafo(doc, "Distribución de errores registrados:", space_after=4)
    tabla(doc, ["Tipo de error", "Ocurrencias", "% del total"],
          [[r["error_type"].replace("_", " "), int(r["n"]), f"{r['pct']}%"]
           for _, r in err.iterrows()],
          anchos=[2.6, 1.4, 1.4], size=9)

    # ── 4. Dashboard (IE5, IE8) ───────────────────────────────────────────────
    h1(doc, "4. Dashboard de monitoreo")
    rico(doc, [
        ("Se construyó el dashboard en ", False), ("Power BI", True),
        (", alimentado por la tabla de hechos ", False), ("dashboard/powerbi_dataset.csv", True),
        (" (una fila por interacción) con medidas DAX para precisión, latencia p95, tasa de "
         "error, tokens y tasa de bloqueo de seguridad (guía en ", False),
        ("dashboard/GUIA_POWERBI.md", True),
        ("). Como vista rápida reproducible se incluye además el libro ", False),
        ("dashboard/dashboard_banco.xlsx", True),
        (" con KPIs y gráficos nativos. El tablero integra: tarjetas de KPI, precisión y "
         "latencia por escenario, evolución temporal con marca de incidente, distribución de "
         "errores, uso de recursos y panel de seguridad, con segmentadores por escenario y "
         "fecha.", False),
    ])
    figura(doc, "07_dashboard_panel.png",
           "Figura 3. Captura del dashboard de monitoreo integrado (KPIs + visualizaciones).",
           width=6.4)

    # ── 5. Seguridad (IE6) ────────────────────────────────────────────────────
    h1(doc, "5. Seguridad y uso responsable")
    parrafo(doc,
        "Se integró una capa transversal de seguridad (security/guardrails.py) alineada con "
        "la Ley 19.628 sobre datos personales, la normativa de ciberseguridad de la CMF y el "
        "OWASP Top 10 for LLM Applications:")
    vinneta(doc, [
        [("Privacidad por diseño: ", True), ("enmascaramiento de PII (RUT, tarjeta, correo, "
         "teléfono) antes de logs y prompts; los RUT conservan solo 3 dígitos para trazar sin "
         "exponer el dato.", False)],
        [("Defensa ante prompt-injection: ", True), ("detección por patrones de intentos de "
         "ignorar instrucciones, revelar el system prompt u operar sin confirmación (OWASP LLM01).", False)],
        [("Rate limiting y validación de entrada: ", True), ("control de abuso y saneamiento.", False)],
        [("Auditoría con integridad: ", True), ("bitácora con encadenamiento de hash (no-repudio).", False)],
        [("Confirmación humana: ", True), ("toda transferencia requiere validación explícita.", False)],
    ])
    rico(doc, [
        ("Sobre la telemetría se registraron ", False),
        (f"{sec['intentos_injection']} intentos de prompt-injection, de los cuales se bloqueó "
         f"el {pct(sec['tasa_bloqueo'])}", True),
        (f". Persisten {sec['bypasses']} casos no bloqueados (riesgo residual) y se enmascaró "
         f"PII en {sec['interacciones_con_pii']} interacciones (ver panel de seguridad en la "
         "Figura 3).", False),
    ])

    # ── 6. Recomendaciones (IE7) ──────────────────────────────────────────────
    h1(doc, "6. Recomendaciones de optimización")
    parrafo(doc,
        "Cada recomendación se fundamenta en las métricas y la trazabilidad anteriores, "
        "priorizadas por impacto en sostenibilidad y escalabilidad:")
    numerada(doc, [
        [("Desambiguación de intención (precisión). ", True),
         (f"La brecha de {pat['brecha_ambiguedad']*100:.0f} pp en entradas ambiguas justifica "
          "añadir una capa de clarificación (repreguntar) y few-shot de enrutamiento. "
          "Es la mejora de mayor impacto en la precisión global.", False)],
        [("Optimización del cuello de botella multi-agente (latencia/recursos). ", True),
         ("Ejecutar en paralelo a los especialistas independientes, cachear respuestas de "
          "productos y usar un modelo más liviano para sub-tareas reduce la latencia p95 y el "
          "consumo de tokens (escalabilidad y costo).", False)],
        [("Resiliencia ante incidentes (disponibilidad). ", True),
         ("Implementar reintentos con backoff, timeouts y un modelo de respaldo (fallback) "
          "mitiga episodios como el incidente detectado y reduce timeouts y rate-limits.", False)],
        [("Refuerzo del guardrail de seguridad. ", True),
         (f"Los {sec['bypasses']} bypasses exigen complementar la heurística con un clasificador "
          "LLM dedicado y canary tokens para acercar el bloqueo al 100%.", False)],
        [("Monitoreo continuo con alertas. ", True),
         ("Definir umbrales (p95 > p95 histórico + 2σ, error > 10%) que disparen alertas "
          "automáticas sobre el dashboard, habilitando observabilidad proactiva.", False)],
    ])

    # ── 7. Referencias ────────────────────────────────────────────────────────
    h1(doc, "7. Referencias")
    refs = [
        "Biblioteca Duoc UC. (2024). Guía para el uso de inteligencia artificial. https://bibliotecas.duoc.cl/ia",
        "Comisión para el Mercado Financiero. (2020). Recopilación Actualizada de Normas, Cap. 20-7: Gestión de la ciberseguridad. CMF Chile.",
        "Ley N°19.628. Sobre protección de la vida privada. Biblioteca del Congreso Nacional de Chile.",
        "OWASP Foundation. (2023). OWASP Top 10 for Large Language Model Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "Yao, S., et al. (2022). ReAct: Synergizing reasoning and acting in language models. arXiv:2210.03629.",
    ]
    for r in refs:
        p = doc.add_paragraph(r)
        p.paragraph_format.left_indent = __import__("docx").shared.Inches(0.3)
        p.paragraph_format.first_line_indent = __import__("docx").shared.Inches(-0.3)
        p.runs[0].font.size = __import__("docx").shared.Pt(8.5)
        p.paragraph_format.space_after = __import__("docx").shared.Pt(3)

    parrafo(doc,
        "Repositorio con código fuente, README de ejecución, telemetría, dashboard, bocetos "
        "de diseño (diagrama de arquitectura) y evidencia de pruebas de software "
        "(22 pruebas automatizadas con pytest, reports/evidencia_pruebas.txt): "
        "github.com/rogrosas/Ingenier-a-de-Soluciones-con-Inteligencia-Artificial. "
        "Toda la telemetría es reproducible con «python run_observability.py».",
        size=8.5, italic=True)

    doc.save(SALIDA)
    return SALIDA


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ruta = build()
    print(f"✔ Informe EP3 generado: {os.path.relpath(ruta, ROOT)}")

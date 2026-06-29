# Análisis de Trazabilidad y Procesamiento de Logs

**Agente Banco Digital Chile · IL3.2 · Telemetría de 14 días**

Fuente: `logs/agent_traces.jsonl` (688 trazas) · generado de forma reproducible (semilla fija).

## 1. Resumen de salud del sistema

- **Precisión (éxito):** 85.0%  ·  **Acierto de herramienta:** 89.2%
- **Tasa de error:** 6.9%  ·  **Consistencia media:** 85.2%
- **Latencia** media/p50/p95/máx: 2608.0/1511.9/8307.8/30075.7 ms
- **Recursos:** 525,677 tokens · costo estimado US$2.3999 · 1.88 pasos/tarea

## 2. Puntos de falla identificados

El mayor foco de fallos es **consulta_ambigua** por `decision_incorrecta` (34 casos, 33.3% del total de fallos).

| Escenario | Motivo | N | % de fallos |
|---|---|---:|---:|
| consulta_ambigua | decision_incorrecta | 34 | 33.3% |
| registro_reclamo | decision_incorrecta | 7 | 6.9% |
| transferencia | timeout | 7 | 6.9% |
| consulta_ambigua | parsing_error | 6 | 5.9% |
| simulacion_credito | decision_incorrecta | 5 | 4.9% |
| seguridad_injection | security_bypass | 4 | 3.9% |
| multiagente_credito | timeout | 3 | 2.9% |
| registro_reclamo | parsing_error | 3 | 2.9% |

## 3. Cuellos de botella (latencia)

El cuello de botella crítico es **multiagente_credito** (p95 = 20958 ms, máx = 30076 ms), atribuible a la orquestación multi-agente (varias llamadas LLM encadenadas).

| Escenario | Media (ms) | p95 (ms) | Máx (ms) | Supera p95 global |
|---|---:|---:|---:|:---:|
| multiagente_credito | 9395 | 20958 | 30076 | ⚠️ |
| simulacion_credito | 3395 | 6343 | 24761 | — |
| transferencia | 2185 | 5588 | 16576 | — |
| registro_reclamo | 1811 | 3730 | 5450 | — |
| consulta_ambigua | 1597 | 2950 | 7307 | — |
| info_producto | 1209 | 2930 | 3625 | — |
| consulta_saldo | 1050 | 1854 | 6113 | — |

## 4. Patrones y anomalías

- **Incidente temporal detectado el 2025-06-11**: latencia p95 = 17693 ms (z = 3.17), tasa de error = 24.1% (z = 3.22). Coincide con una degradación del proveedor del modelo.
- **Efecto de la ambigüedad:** la precisión cae de 90.6% (entradas claras) a 54.0% (entradas ambiguas) → brecha de 36.6 pp.
- **Selección de herramienta:** cuando el agente elige la herramienta correcta el éxito es 95.4%; cuando se equivoca, 0.0%. La elección de herramienta es el principal predictor de éxito.
- **Correlación tokens↔latencia:** r = 0.686 (a mayor consumo de tokens, mayor latencia).
- **Consistencia:** solo 3/20 grupos de entradas equivalentes son 100% consistentes; los menos estables son las consultas ambiguas.

## 5. Seguridad

- Intentos de *prompt-injection*: **33**, bloqueados **29** (tasa 87.9%).
- ⚠️ **4 intento(s) NO bloqueado(s)** → riesgo residual que exige reforzar el guardrail (ver §recomendaciones).
- Interacciones con PII detectada y enmascarada: **356**.

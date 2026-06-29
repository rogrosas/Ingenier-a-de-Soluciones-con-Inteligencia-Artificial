# Guía del Dashboard de Monitoreo — Power BI

**Agente "Banco Digital Chile" · EP3 · IL3.1**

Este dashboard visualiza el comportamiento del agente según las métricas de
observabilidad. Hay **dos formas** de revisarlo:

1. **Vista rápida (sin instalar nada):** abre
   [`dashboard_banco.xlsx`](dashboard_banco.xlsx) → hojas `KPIs`, `PorEscenario`,
   `SerieDiaria`, `Errores` con gráficos nativos ya incrustados.
2. **Dashboard interactivo en Power BI Desktop:** importa
   [`powerbi_dataset.csv`](powerbi_dataset.csv) (tabla de hechos, 1 fila por
   interacción) siguiendo los pasos de abajo.

---

## 1. Importar los datos

1. Power BI Desktop → **Inicio › Obtener datos › Texto/CSV** →
   selecciona `powerbi_dataset.csv` (codificación UTF-8).
2. **Transformar datos** y verificar tipos:
   - `timestamp` → Fecha/hora · `fecha` → Fecha · `hora` → Número entero
   - `latency_ms`, `tokens_total`, `cost_usd` → Número decimal
   - `success`, `correct_tool`, `pii_detected`, `injection_blocked` → Verdadero/Falso
3. **Cerrar y aplicar**.

> La tabla ya viene "tidy" (un hecho por fila). Para un modelo estrella opcional,
> crea dimensiones `Dim_Escenario` y `Dim_Fecha` con *Nueva tabla* y relaciónalas
> por `escenario` y `fecha`.

---

## 2. Medidas DAX

Crea estas medidas (**Modelado › Nueva medida**):

```DAX
Interacciones        = COUNTROWS('powerbi_dataset')

Precision Exito %    = DIVIDE ( SUM('powerbi_dataset'[exito_int]), [Interacciones] )

Acierto Herramienta %=
    DIVIDE (
        CALCULATE ( [Interacciones], 'powerbi_dataset'[correct_tool] = TRUE() ),
        [Interacciones]
    )

Tasa Error %         = DIVIDE ( SUM('powerbi_dataset'[error_int]), [Interacciones] )

Latencia Media (ms)  = AVERAGE ('powerbi_dataset'[latency_ms])

Latencia p95 (ms)    =
    PERCENTILE.INCL ( 'powerbi_dataset'[latency_ms], 0.95 )

Tokens Totales       = SUM ('powerbi_dataset'[tokens_total])

Costo Total USD      = SUM ('powerbi_dataset'[cost_usd])

Injection Bloqueo %  =
    VAR ataques =
        CALCULATE ( [Interacciones], 'powerbi_dataset'[escenario] = "seguridad_injection" )
    VAR bloqueados =
        CALCULATE ( [Interacciones],
            'powerbi_dataset'[escenario] = "seguridad_injection",
            'powerbi_dataset'[injection_blocked] = TRUE() )
    RETURN DIVIDE ( bloqueados, ataques )
```

---

## 3. Visuales recomendados (replican `charts/`)

| Visual | Tipo | Campos |
|---|---|---|
| **Tarjetas KPI** | Tarjeta | `Precision Exito %`, `Tasa Error %`, `Latencia p95 (ms)`, `Costo Total USD` |
| **Precisión por escenario** | Barras horizontales | Eje: `escenario` · Valor: `Precision Exito %` |
| **Latencia p95 por escenario** | Barras horizontales | Eje: `escenario` · Valor: `Latencia p95 (ms)` |
| **Evolución diaria** | Líneas (doble eje) | Eje: `fecha` · Valores: `Latencia p95 (ms)`, `Tasa Error %` |
| **Distribución de errores** | Anillo / Treemap | Leyenda: `error_type` · Valor: `Interacciones` |
| **Uso de recursos** | Barras | Eje: `escenario` · Valor: `Tokens Totales` |
| **Seguridad** | Tarjeta + Anillo | `Injection Bloqueo %`; leyenda `injection_blocked` |
| **Segmentadores** | Slicer | `escenario`, `fecha`, `error_type` |

**Formato condicional sugerido:** en "Precisión por escenario", colorear en rojo
los valores < 70% (resalta `consulta_ambigua`) y marcar el día de incidente en la
línea temporal.

---

## 4. Lectura del dashboard (qué buscar)

- El **incidente del día 10** (≈ 2025-06-11) aparece como pico simultáneo de
  latencia p95 y tasa de error.
- **`multiagente_credito`** domina la latencia p95 → cuello de botella.
- **`consulta_ambigua`** hunde la precisión global → oportunidad de mejora.
- La **tasa de bloqueo de injection < 100%** evidencia un riesgo de seguridad
  residual.

> Los datos se regeneran con `python -m observability.export_powerbi` tras
> ejecutar `python -m observability.generate_telemetry`.

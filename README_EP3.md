# EP3 + EFT — Observabilidad, Trazabilidad y Seguridad

**ISY0101 · Ingeniería de Soluciones con IA · Agente "Banco Digital Chile"**
**Autores:** Roger Rosas · Rodrigo Santis · Edgardo Gutiérrez

Esta entrega cubre **conjuntamente** la Evaluación Parcial 3 (Implementación de
Observabilidad, 35%) y la Evaluación Final Transversal (consolidación del
proyecto, 40%), sobre el agente bancario desarrollado en EP1/EP2.

---

## 1. Qué se entrega

Todos los **documentos entregables** están en la carpeta [`entrega/`](entrega/).

| Entregable | Archivo | Evaluación |
|---|---|---|
| **Informe integral consolidado** | [`entrega/Informe_Completo_BancoDigitalChile.docx`](entrega/Informe_Completo_BancoDigitalChile.docx) | EP3 + EFT |
| Informe de observabilidad (≤5 págs) | [`entrega/EP3_Observabilidad_BancoDigitalChile.docx`](entrega/EP3_Observabilidad_BancoDigitalChile.docx) | EP3 |
| Informe final transversal | [`entrega/EFT_Informe_Final_BancoDigitalChile.docx`](entrega/EFT_Informe_Final_BancoDigitalChile.docx) | EFT |
| **Presentación de defensa (.pptx)** | [`entrega/EFT_Presentacion_Defensa.pptx`](entrega/EFT_Presentacion_Defensa.pptx) | EFT |
| **Guion de la presentación** | [`entrega/GUION_PRESENTACION_EFT.docx`](entrega/GUION_PRESENTACION_EFT.docx) | EFT |
| Notebook ejecutable (Colab) | [`entrega/EFT_Notebook_BancoDigitalChile.ipynb`](entrega/EFT_Notebook_BancoDigitalChile.ipynb) | EFT |
| Guía de estudio de defensa | [`entrega/GUION_DEFENSA_EFT.md`](entrega/GUION_DEFENSA_EFT.md) | EFT |
| Dashboard Power BI (dataset + guía) | [`dashboard/`](dashboard/) | EP3 |
| Telemetría / logs | [`logs/`](logs/) | EP3 |
| Análisis de trazabilidad + CSVs | [`reports/`](reports/) | EP3 |

---

## 2. Estructura del código (nuevo en RA3)

```
observability/
  instrumentation.py     # Tracer → trazas JSONL + agent.log (PII enmascarada)
  generate_telemetry.py  # Batería reproducible de 14 días con fallos inyectados
  metrics.py             # Precisión, latencia, consistencia, errores, recursos
  analyze_traces.py      # Puntos de falla, cuellos de botella, anomalías
  make_charts.py         # Gráficos PNG del dashboard
  export_powerbi.py      # Dataset CSV + workbook Excel para Power BI
security/
  guardrails.py          # PII masking, anti-injection, rate-limit, auditoría
  policies.md            # Protocolos de seguridad y consideraciones éticas
rag/
  knowledge_base.py      # Base de conocimiento: fuentes internas + externas
  rag_pipeline.py        # Recuperación TF-IDF (chunking → vectorizar → top-k)
tests/                   # 22 pruebas (pytest): guardrails, observabilidad, RAG
run_observability.py     # Pipeline completo en un solo comando
dashboard/
  powerbi_dataset.csv    # Tabla de hechos para Power BI
  dashboard_banco.xlsx   # Vista rápida con gráficos nativos
  GUIA_POWERBI.md        # Guía de armado + medidas DAX
  charts/                # Figuras usadas en los informes
```

---

## 3. Instalación

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

Para la **demo del agente en vivo** (opcional) copia `.env.example` a `.env` y
define `GITHUB_TOKEN` y `GITHUB_BASE_URL`. La capa de observabilidad **no**
requiere credenciales.

---

## 4. Cómo ejecutar

### Pipeline completo (recomendado) — un solo comando

```bash
python run_observability.py
```

Genera la telemetría, calcula las métricas, analiza la trazabilidad, renderiza
los gráficos y exporta el dataset/dashboard de Power BI. Es **reproducible**
(semilla fija): cualquier evaluador obtiene los mismos resultados.

### Paso a paso

```bash
python -m observability.generate_telemetry     # 1. telemetría → logs/
python -m observability.metrics                 # 2. métricas (consola)
python -m observability.analyze_traces          # 3. trazabilidad → reports/
python -m observability.make_charts             # 4. gráficos → dashboard/charts/
python -m observability.export_powerbi          # 5. dataset + xlsx → dashboard/
python -m observability.make_dashboard          # panel integrado del dashboard
python -m security.guardrails                   # demo de seguridad
python -m rag.rag_pipeline                       # demo de recuperación RAG
```

### Pruebas de software (evidencia)

```bash
python -m pytest tests/ -v        # 22 pruebas (evidencia en reports/evidencia_pruebas.txt)
```

### Ver el dashboard

- **Rápido:** abre `dashboard/dashboard_banco.xlsx` (hojas KPIs, PorEscenario,
  SerieDiaria, Errores con gráficos).
- **Power BI:** importa `dashboard/powerbi_dataset.csv` siguiendo
  `dashboard/GUIA_POWERBI.md` (incluye las medidas DAX y los visuales).

### Regenerar los informes Word (opcional)

```bash
python docs/make_arch_diagram.py        # diagrama de arquitectura
python docs/build_ep3.py                 # informe EP3
python docs/build_eft.py                 # informe EFT
python docs/build_informe_completo.py    # informe integral consolidado
python docs/build_notebook.py            # notebook ejecutable
python docs/build_presentacion.py        # presentación .pptx de defensa
python docs/build_guion.py               # guion de la presentación
```

---

## 5. Mapa rúbrica → evidencia

**EP3**

| IE | Evidencia |
|---|---|
| IE1–IE2 (métricas) | `observability/metrics.py`, tabla por escenario, figs 1 |
| IE3–IE4 (trazabilidad, patrones) | `observability/analyze_traces.py`, `reports/analisis_trazabilidad.md` |
| IE5, IE8 (dashboard, informe visual) | `dashboard/`, informe EP3 con figuras |
| IE6 (seguridad) | `security/guardrails.py`, `security/policies.md` |
| IE7 (recomendaciones) | §6 del informe EP3 |

**EFT** (Encargo): IE1–IE4 (diseño LLM/RAG), IE5–IE8 (agente funcional),
IE9–IE12 (observabilidad/seguridad/mejoras) — todos cubiertos en
`EFT_Informe_Final_BancoDigitalChile.docx` y en el notebook.

---

## 6. Reproducibilidad

Toda la telemetría es **sintética y determinista** (semilla 42). Se eligió este
enfoque para que la evaluación sea reproducible sin consumir cuota de API ni
exponer datos reales, manteniendo la **misma instrumentación** que usaría una
ejecución en producción. Cambia la semilla con `--seed` para explorar otros
escenarios.

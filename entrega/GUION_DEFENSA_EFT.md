# Guion de Defensa Individual — EFT

**Agente "Banco Digital Chile" · ISY0101 · 10 minutos por estudiante**

> Formato: reunión ejecutiva simulada. El/la docente representa a la dirección
> de la organización. Debes **fundamentar** decisiones, **demostrar** el sistema
> y **reflexionar** críticamente. Las respuestas deben ser tuyas: usa este guion
> para preparar, no para leer.

---

## Distribución del tiempo (10 min)

| Bloque | Tiempo | Contenido | IE |
|---|---|---|---|
| 1. Síntesis del caso y la solución | ~2 min | Problema, propuesta y por qué es adecuada | IE1, IE4, IE8 |
| 2. Demostración del agente y arquitectura | ~3 min | Demo en vivo + componentes y flujos | IE5, IE6, IE7 |
| 3. Observabilidad, mejoras y ética | ~3 min | Métricas, hallazgos, mejoras y dilemas | IE9, IE11, IE12 |
| 4. Cierre y fundamentación | ~2 min | Decisiones clave con evidencia | IE13–IE15 |

---

## Bloque 1 — Síntesis del caso y la solución (2 min)

**Idea fuerza:** "Banco Digital Chile recibe alto volumen de consultas
repetitivas y operaciones sensibles; la atención humana no escala y un chatbot
de reglas no comprende lenguaje natural ni ejecuta acciones."

Puntos a cubrir:
- Problema y por qué importa (costo, tiempos de espera, errores).
- Solución: agente conversacional que **consulta, opera y razona** con LLM + RAG,
  memoria, planificación y orquestación multi-agente.
- Por qué es adecuada: automatiza el flujo de extremo a extremo manteniendo
  contexto, trazabilidad y seguridad.

---

## Bloque 2 — Demostración del agente y su arquitectura (3 min)

**Demo sugerida (prepara el entorno antes):**
1. Consulta de saldo con RUT (memoria de corto plazo recuerda el dato).
2. Simulación de crédito multi-etapa (planificación Plan-and-Execute).
3. Mostrar el `dashboard_banco.xlsx` / Power BI con las métricas.

Explica la arquitectura por capas (apóyate en la Figura 1 del informe):
- **Seguridad de entrada** → **Agente LangChain (ReAct) + LLM** →
  **Herramientas / RAG / Memoria / Orquestación CrewAI** →
  **Observabilidad de salida**.

Prepárate para preguntas técnicas: ¿por qué LangChain y CrewAI?, ¿cómo funciona
la memoria k=5?, ¿qué hace el ciclo ReAct?

---

## Bloque 3 — Observabilidad, mejoras y reflexión ética (3 min)

Presenta los resultados (cifras reales del informe):
- Precisión 85.0% · latencia media 2.608 ms · p95 8.308 ms · error 6.9%.
- **Cuello de botella:** orquestación multi-agente (p95 ≈ 21 s).
- **Anomalía detectada:** incidente del 2025-06-11 (latencia y error z ≈ 3).
- **Hallazgo clave:** la selección de herramienta predice el éxito; las consultas
  ambiguas hunden la precisión (brecha ≈ 37 pp).

Mejoras propuestas: desambiguación de intención, paralelizar especialistas,
reintentos con *fallback*, reforzar el guardrail (hubo *bypasses* de injection).

Reflexión ética (en tus palabras): privacidad de datos (Ley 19.628 — PII
enmascarada), confirmación humana en transferencias, riesgo de sesgo en
recomendaciones y dependencia del proveedor del modelo.

---

## Bloque 4 — Cierre y fundamentación (2 min)

Cierra conectando cada decisión con evidencia: "Elegimos X porque las métricas
mostraron Y". Usa lenguaje técnico preciso y responde con seguridad.

---

## Preguntas frecuentes del docente (prepara respuestas propias)

- ¿Cómo medirías si una mejora realmente funcionó? (comparar métricas antes/después).
- ¿Qué harías si el modelo se cae en producción? (timeouts, reintentos, fallback).
- ¿Cómo evitas que el agente filtre datos personales? (enmascaramiento + auditoría).
- ¿Cuál fue el mayor desafío técnico y cómo lo resolviste?
- ¿Qué límite tiene tu solución y cómo escalarías a 10× el tráfico?

> Recuerda: la **claridad, la evidencia y la autocrítica** puntúan más que la
> perfección técnica. Practica la demo al menos una vez de principio a fin.

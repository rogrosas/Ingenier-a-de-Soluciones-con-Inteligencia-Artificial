"""
Instrumentación de Observabilidad — Banco Digital Chile (EP3 / RA3)
====================================================================
Capa de observabilidad que envuelve cualquier ejecución del agente bancario y
emite *trazas estructuradas* (una por interacción) más un log legible.

Cada traza registra todo lo necesario para calcular las métricas exigidas por
IL3.1 / IL3.2:

    Precisión        → success, correct_tool (vs. ground truth)
    Latencia         → latency_ms (total) y duración por paso
    Consistencia     → escenario + variante (agrupa ejecuciones equivalentes)
    Frecuencia error → error.type
    Uso de recursos  → tokens_total, n_steps, cost_usd

Decisiones de diseño:
  - Formato JSONL (un objeto JSON por línea): apto para streaming, fácil de
    parsear con pandas y de ingestar en Power BI / un stack ELK.
  - Toda la PII (RUT, montos, texto del cliente) se enmascara ANTES de escribir
    al disco, reutilizando `security.guardrails`. La observabilidad nunca debe
    convertirse en una fuga de datos personales (Ley 19.628).
  - El `Tracer` funciona como context manager para medir un paso individual y
    como wrapper de alto nivel (`instrument`) para una interacción completa.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

# La instrumentación depende de la capa de seguridad para no filtrar PII en logs.
try:
    from security.guardrails import mask_pii
except Exception:  # pragma: no cover - permite usar el módulo de forma aislada
    def mask_pii(texto: str) -> str:  # type: ignore
        return texto


# ── Rutas de salida ───────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

TRACES_FILE = os.path.join(LOG_DIR, "agent_traces.jsonl")
TEXT_LOG_FILE = os.path.join(LOG_DIR, "agent.log")

# Precio referencial (gpt-4o, GitHub Models) para estimar costo. USD por 1k tokens.
PRECIO_INPUT_1K = 0.0025
PRECIO_OUTPUT_1K = 0.0100


# ── Logger de texto (trazabilidad legible por humanos) ────────────────────────

def _build_text_logger() -> logging.Logger:
    logger = logging.getLogger("banco.agente")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    fh = logging.FileHandler(TEXT_LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


text_log = _build_text_logger()


# ── Esquema de la traza ───────────────────────────────────────────────────────

@dataclass
class ToolCall:
    """Registro de una invocación de herramienta dentro de una interacción."""
    nombre: str
    duracion_ms: float
    ok: bool
    args: str = ""          # ya enmascarado
    error: Optional[str] = None


@dataclass
class Trace:
    """Traza estructurada de una interacción completa agente↔cliente."""
    trace_id: str
    session_id: str
    timestamp: str
    escenario: str                  # familia de escenario (clave de consistencia)
    variante: str                   # variante de input dentro del escenario
    intent: str                     # intención detectada / esperada
    canal: str = "chat"
    modelo: str = "gpt-4o"
    input_text: str = ""            # enmascarado
    output_text: str = ""           # enmascarado
    expected_tool: Optional[str] = None
    tools_called: list = field(default_factory=list)
    n_steps: int = 0
    latency_ms: float = 0.0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    success: bool = True            # ¿resolvió correctamente la tarea?
    correct_tool: bool = True       # ¿usó la herramienta esperada?
    error_type: Optional[str] = None
    error_msg: Optional[str] = None
    # Señales de seguridad asociadas a la interacción
    pii_detected: bool = False
    injection_blocked: bool = False
    masked_fields: int = 0

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def _estimar_costo(tokens_prompt: int, tokens_completion: int) -> float:
    return round(
        tokens_prompt / 1000 * PRECIO_INPUT_1K
        + tokens_completion / 1000 * PRECIO_OUTPUT_1K,
        6,
    )


# ── Tracer ────────────────────────────────────────────────────────────────────

class Tracer:
    """
    Acumula la información de UNA interacción y la persiste como traza.

    Uso típico:
        tr = Tracer(escenario="consulta_saldo", variante="v1",
                    intent="consultar_saldo", expected_tool="consultar_saldo",
                    input_text=entrada)
        with tr.step("consultar_saldo") as step:
            resultado = consultar_saldo.invoke(...)
        tr.set_usage(tokens_prompt=320, tokens_completion=110)
        tr.finish(output_text=resultado, success=True, correct_tool=True)
    """

    def __init__(
        self,
        escenario: str,
        variante: str,
        intent: str,
        expected_tool: Optional[str] = None,
        input_text: str = "",
        session_id: Optional[str] = None,
        modelo: str = "gpt-4o",
        canal: str = "chat",
    ):
        self._t0 = time.perf_counter()
        self.trace = Trace(
            trace_id=str(uuid.uuid4())[:8],
            session_id=session_id or str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(timespec="seconds"),
            escenario=escenario,
            variante=variante,
            intent=intent,
            expected_tool=expected_tool,
            input_text=mask_pii(input_text),
            modelo=modelo,
            canal=canal,
        )
        text_log.info(
            f"[{self.trace.trace_id}] INICIO escenario={escenario} "
            f"intent={intent} input='{self.trace.input_text}'"
        )

    @contextmanager
    def step(self, nombre: str, args: str = ""):
        """Mide la duración de un paso/herramienta y lo agrega a la traza."""
        t0 = time.perf_counter()
        call = ToolCall(nombre=nombre, duracion_ms=0.0, ok=True, args=mask_pii(args))
        try:
            yield call
        except Exception as e:  # registra el fallo de la herramienta
            call.ok = False
            call.error = f"{type(e).__name__}: {e}"
            text_log.error(f"[{self.trace.trace_id}] TOOL_ERROR {nombre} → {call.error}")
            raise
        finally:
            call.duracion_ms = round((time.perf_counter() - t0) * 1000, 2)
            self.trace.tools_called.append(asdict(call))
            self.trace.n_steps += 1
            text_log.info(
                f"[{self.trace.trace_id}] TOOL {nombre} "
                f"ok={call.ok} dur={call.duracion_ms}ms"
            )

    def set_usage(self, tokens_prompt: int, tokens_completion: int) -> None:
        self.trace.tokens_prompt = tokens_prompt
        self.trace.tokens_completion = tokens_completion
        self.trace.tokens_total = tokens_prompt + tokens_completion
        self.trace.cost_usd = _estimar_costo(tokens_prompt, tokens_completion)

    def set_security(self, pii_detected: bool, injection_blocked: bool, masked_fields: int) -> None:
        self.trace.pii_detected = pii_detected
        self.trace.injection_blocked = injection_blocked
        self.trace.masked_fields = masked_fields

    def finish(
        self,
        output_text: str = "",
        success: bool = True,
        correct_tool: bool = True,
        error_type: Optional[str] = None,
        error_msg: Optional[str] = None,
    ) -> Trace:
        self.trace.latency_ms = round((time.perf_counter() - self._t0) * 1000, 2)
        self.trace.output_text = mask_pii(output_text)
        self.trace.success = success
        self.trace.correct_tool = correct_tool
        self.trace.error_type = error_type
        self.trace.error_msg = error_msg
        _persist(self.trace)
        nivel = text_log.info if success else text_log.warning
        nivel(
            f"[{self.trace.trace_id}] FIN success={success} correct_tool={correct_tool} "
            f"latency={self.trace.latency_ms}ms tokens={self.trace.tokens_total} "
            f"error={error_type or '-'}"
        )
        return self.trace


def _persist(trace: Trace) -> None:
    with open(TRACES_FILE, "a", encoding="utf-8") as f:
        f.write(trace.to_jsonl() + "\n")


def reset_logs() -> None:
    """Limpia las trazas previas (útil antes de regenerar la telemetría)."""
    global text_log
    # Cierra los handlers ANTES de borrar (Windows bloquea archivos abiertos).
    for h in list(text_log.handlers):
        text_log.removeHandler(h)
        h.close()
    for path in (TRACES_FILE, TEXT_LOG_FILE):
        if os.path.exists(path):
            os.remove(path)
    text_log = _build_text_logger()


def load_traces(path: str = TRACES_FILE) -> list[dict[str, Any]]:
    """Carga todas las trazas JSONL como lista de dicts."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

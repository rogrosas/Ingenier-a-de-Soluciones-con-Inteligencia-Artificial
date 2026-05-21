"""
Sistema de Memoria del Agente Bancario
=======================================
Implementa dos capas de memoria:

  Corto plazo  → ConversationBufferWindowMemory (últimas k interacciones)
                 Permite seguir el hilo de la conversación activa.

  Largo plazo  → JSON persistente en disco
                 Retiene información clave del cliente entre sesiones:
                 preferencias, incidentes previos, productos consultados.
"""

import json
import os
from datetime import datetime
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
)

_LT_FILE = os.path.join(os.path.dirname(__file__), "long_term_memory.json")


# ── Memoria a Corto Plazo ─────────────────────────────────────────────────────

def create_buffer_memory() -> ConversationBufferMemory:
    """
    Memoria completa: guarda TODA la conversación actual.
    Útil para sesiones cortas donde cada detalle importa.
    """
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)


def create_window_memory(k: int = 5) -> ConversationBufferWindowMemory:
    """
    Memoria de ventana: guarda las últimas k interacciones.
    Equilibrio entre contexto y eficiencia de tokens. Valor por defecto k=5.
    """
    return ConversationBufferWindowMemory(
        k=k, memory_key="chat_history", return_messages=True
    )


def create_summary_memory(llm) -> ConversationSummaryMemory:
    """
    Memoria por resumen: comprime conversaciones largas usando el LLM.
    Ideal para sesiones extensas; ahorra tokens manteniendo el contexto general.
    """
    return ConversationSummaryMemory(
        llm=llm, memory_key="chat_history", return_messages=True
    )


# ── Memoria a Largo Plazo (persistente) ──────────────────────────────────────

def save_long_term(rut: str, clave: str, valor) -> None:
    """
    Persiste información del cliente en disco para recuperarla en sesiones futuras.

    Args:
        rut   : Identificador único del cliente.
        clave : Etiqueta descriptiva (ej. 'producto_consultado', 'reclamo_previo').
        valor : Dato a guardar (string, número o dict).
    """
    datos = _cargar_archivo()
    if rut not in datos:
        datos[rut] = {}
    datos[rut][clave] = {"valor": valor, "timestamp": datetime.now().isoformat()}
    _guardar_archivo(datos)


def load_long_term(rut: str) -> dict:
    """
    Carga el perfil de memoria de largo plazo de un cliente.

    Returns:
        dict con claves/valores guardados en sesiones anteriores,
        o dict vacío si es la primera sesión.
    """
    datos = _cargar_archivo()
    return datos.get(rut, {})


def get_client_context_str(rut: str) -> str:
    """
    Genera un bloque de texto con el historial del cliente para inyectar
    en el system prompt y dar continuidad entre sesiones.
    """
    memoria = load_long_term(rut)
    if not memoria:
        return ""

    lineas = [f"[Historial previo del cliente RUT {rut}]"]
    for clave, entrada in memoria.items():
        ts = entrada["timestamp"][:10]
        lineas.append(f"  • {clave}: {entrada['valor']}  (registrado: {ts})")
    return "\n".join(lineas)


def chat(query: str, memory, agent_executor) -> str:
    """
    Función helper que:
      1. Carga el historial de la memoria de corto plazo.
      2. Invoca al agente con el historial actual.
      3. Guarda el nuevo par pregunta/respuesta en la memoria.

    Permite reutilizar cualquier tipo de memoria (buffer, window, summary)
    con la misma interfaz.
    """
    historial = memory.load_memory_variables({})["chat_history"]
    respuesta = agent_executor.invoke({"input": query, "chat_history": historial})
    memory.save_context({"input": query}, {"output": respuesta["output"]})
    return respuesta["output"]


# ── Helpers internos ──────────────────────────────────────────────────────────

def _cargar_archivo() -> dict:
    if os.path.exists(_LT_FILE):
        with open(_LT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _guardar_archivo(datos: dict) -> None:
    with open(_LT_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

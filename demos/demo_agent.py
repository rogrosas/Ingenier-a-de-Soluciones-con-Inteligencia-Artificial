"""
Demo del Agente Bancario - Cuatro Escenarios
==============================================
Demuestra las capacidades del agente cubriendo todos los IE de la rúbrica:

  Escenario 1  → Consulta de saldo + memoria de corto plazo (IE1, IE3)
  Escenario 2  → Simulación de crédito multi-paso (IE5, IE6)
  Escenario 3  → Reclamo con memoria de largo plazo entre sesiones (IE3, IE4)
  Escenario 4  → Transferencia con toma de decisión adaptativa (IE6)

Ejecución:
    python demos/demo_agent.py
    python demos/demo_agent.py --escenario 2
"""

import os
import sys
import argparse

# Permite ejecutar desde cualquier directorio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.tools import (
    consultar_saldo,
    realizar_transferencia,
    calcular_cuota_credito,
    registrar_reclamo,
    buscar_producto_bancario,
)
from agent.memory import (
    create_window_memory,
    create_summary_memory,
    save_long_term,
    get_client_context_str,
    chat,
)

TOOLS = [
    consultar_saldo,
    realizar_transferencia,
    calcular_cuota_credito,
    registrar_reclamo,
    buscar_producto_bancario,
]


# ── Helper ────────────────────────────────────────────────────────────────────

def build_executor(system_msg: str, llm) -> AgentExecutor:
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
    )


def get_llm():
    return ChatOpenAI(
        model="gpt-4o",
        openai_api_base=os.environ.get("GITHUB_BASE_URL"),
        openai_api_key=os.environ.get("GITHUB_TOKEN"),
        temperature=0,
    )


def titulo(texto: str):
    sep = "=" * 62
    print(f"\n{sep}\n{texto}\n{sep}")


def turno(query: str, memory, executor):
    print(f"\n  Cliente   : {query}")
    resp = chat(query, memory, executor)
    print(f"  Asistente : {resp}")


# ── Escenario 1: Consulta + Memoria de Corto Plazo ───────────────────────────

def escenario_1():
    titulo("ESCENARIO 1 — Consulta de Saldo y Memoria a Corto Plazo")
    print("Objetivo: verificar que el agente recuerda respuestas previas dentro")
    print("de la misma sesión usando ConversationBufferWindowMemory.\n")

    llm = get_llm()
    memory = create_window_memory(k=5)
    executor = build_executor(
        "Eres un asistente bancario de Banco Digital Chile. "
        "Responde de forma profesional y concisa.",
        llm,
    )

    conversacion = [
        "Hola, quiero consultar mi saldo. Mi RUT es 12345678-9.",
        "¿Qué productos tengo contratados?",
        "¿Cuánto tenía en mi cuenta según lo que me dijiste recién?",  # Prueba de memoria
    ]
    for msg in conversacion:
        turno(msg, memory, executor)

    print("\n[IE3] Memoria a corto plazo verificada: el agente recordó el saldo sin repetir la consulta.")


# ── Escenario 2: Planificación Multi-Etapa (Crédito) ─────────────────────────

def escenario_2():
    titulo("ESCENARIO 2 — Planificación Multi-Etapa: Solicitud de Crédito")
    print("Objetivo: el agente planifica internamente los pasos para evaluar")
    print("un crédito (información → cálculo → comparativa → decisión).\n")

    llm = get_llm()
    memory = create_window_memory(k=5)
    executor = build_executor(
        "Eres un asesor de créditos de Banco Digital Chile. "
        "Cuando el cliente solicite información sobre créditos, primero explica "
        "las condiciones generales y luego realiza los cálculos solicitados. "
        "Compara opciones cuando sea útil.",
        llm,
    )

    conversacion = [
        "Quiero solicitar un crédito de consumo. ¿Qué información necesito saber?",
        "Me interesan $3.000.000. ¿Cuánto pagaría a 24 meses?",
        "¿Y si lo extiendo a 36 meses? ¿Cuánto ahorro en cuota mensual?",  # Adaptación
        "Bien, ¿cuáles son los requisitos para aplicar?",
    ]
    for msg in conversacion:
        turno(msg, memory, executor)

    print("\n[IE5+IE6] El agente secuenció los pasos y adaptó la respuesta al cambio de plazo.")


# ── Escenario 3: Reclamo con Memoria de Largo Plazo ──────────────────────────

def escenario_3():
    titulo("ESCENARIO 3 — Reclamo con Continuidad entre Sesiones (Memoria LP)")
    print("Objetivo: el agente recupera el historial de sesiones anteriores")
    print("para dar continuidad sin que el cliente repita su situación.\n")

    RUT = "98765432-1"

    # Simular que en una sesión anterior se guardó un incidente
    save_long_term(RUT, "incidente_previo", "Cobro duplicado en noviembre 2024 — resuelto ticket RC20241112-8821")
    save_long_term(RUT, "preferencia_contacto", "correo electrónico")

    contexto = get_client_context_str(RUT)
    print(f"[Memoria LP cargada para {RUT}]\n{contexto}\n")

    llm = get_llm()
    memory = create_window_memory(k=5)
    executor = build_executor(
        f"Eres un agente de atención al cliente de Banco Digital Chile. "
        f"Usa el historial previo del cliente para dar continuidad.\n\n{contexto}",
        llm,
    )

    conversacion = [
        "Buen día, soy Carlos Pérez, RUT 98765432-1. Tengo un problema con mi cuenta.",
        "Me están cobrando $25.000 por un servicio que no reconozco.",
        "Quiero hacer un reclamo formal por cobro indebido.",
    ]
    for msg in conversacion:
        turno(msg, memory, executor)

    print("\n[IE3+IE4] Memoria LP recuperada y usada para contextualizar la atención.")


# ── Escenario 4: Transferencia con Toma de Decisión Adaptativa ───────────────

def escenario_4():
    titulo("ESCENARIO 4 — Transferencia y Decisión Adaptativa ante Condiciones")
    print("Objetivo: el agente verifica saldo, solicita confirmación y ajusta")
    print("su comportamiento si el saldo es insuficiente.\n")

    llm = get_llm()
    memory = create_window_memory(k=5)
    executor = build_executor(
        "Eres un agente bancario de Banco Digital Chile. "
        "Para transferencias: (1) verifica el saldo, (2) confirma los datos, "
        "(3) ejecuta solo si el cliente confirma. Si el saldo es insuficiente, "
        "propón alternativas (transferir un monto menor, abrir línea de crédito).",
        llm,
    )

    conversacion = [
        "Quiero transferir $200.000 desde mi cuenta RUT 12345678-9 a la cuenta 98765432-1.",
        "Sí, confirmo la transferencia.",
        "Ahora quiero transferir $3.000.000 adicionales desde la misma cuenta.",  # Saldo insuficiente → adaptación
        "¿Cuánto tengo disponible ahora?",
    ]
    for msg in conversacion:
        turno(msg, memory, executor)

    print("\n[IE6] Decisión adaptativa: el agente detectó saldo insuficiente y ofreció alternativas.")


# ── Entrypoint ────────────────────────────────────────────────────────────────

ESCENARIOS = {
    "1": escenario_1,
    "2": escenario_2,
    "3": escenario_3,
    "4": escenario_4,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo del Agente Bancario EP2")
    parser.add_argument(
        "--escenario",
        choices=["1", "2", "3", "4", "todos"],
        default="todos",
        help="Escenario a ejecutar (default: todos)",
    )
    args = parser.parse_args()

    print("BANCO DIGITAL CHILE — Demo EP2: Agente Funcional con Memoria y Planificación")
    print("Frameworks: LangChain + GitHub Models API\n")

    if args.escenario == "todos":
        for fn in ESCENARIOS.values():
            fn()
    else:
        ESCENARIOS[args.escenario]()

    print("\n" + "=" * 62)
    print("Demo completado. Archivos generados:")
    print("  • EP2/agent/reclamos.json         (reclamos registrados)")
    print("  • EP2/agent/long_term_memory.json  (memoria persistente)")
    print("=" * 62)

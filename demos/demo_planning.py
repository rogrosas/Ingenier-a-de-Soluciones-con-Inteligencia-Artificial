"""
Demo de Planificación Explícita y Orquestación Multi-Agente
=============================================================
Demuestra dos conceptos avanzados del módulo IL2.3:

  Plan-and-Execute  → El agente genera un plan textual completo ANTES de actuar.
                      Supera las limitaciones del ReAct puro para tareas multi-etapa.

  Multi-Agente       → Invoca crew_orchestration.py con modo secuencial para mostrar
                       cómo el sistema se adapta cuando la complejidad requiere
                       especialistas dedicados.

Ejecución:
    python demos/demo_planning.py
    python demos/demo_planning.py --modo multiagente
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.tools import (
    consultar_saldo,
    calcular_cuota_credito,
    buscar_producto_bancario,
    registrar_reclamo,
)
from agent.memory import create_window_memory, chat

TOOLS = [consultar_saldo, calcular_cuota_credito, buscar_producto_bancario, registrar_reclamo]


# ── Helper ────────────────────────────────────────────────────────────────────

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


# ── Plan-and-Execute ──────────────────────────────────────────────────────────

PLANNING_SYSTEM = """Eres un asesor bancario senior de Banco Digital Chile con capacidad de PLANIFICACIÓN.

Ante solicitudes complejas (múltiples pasos), sigue este protocolo:

PASO 1 — PLAN
  Antes de usar cualquier herramienta, redacta un plan explícito:
  "Plan: 1) [acción] → 2) [acción] → 3) [acción]"

PASO 2 — EJECUCIÓN
  Ejecuta cada paso del plan usando las herramientas disponibles.
  Si un resultado cambia las condiciones, adapta los pasos restantes.

PASO 3 — RESUMEN
  Consolida todos los resultados en una respuesta clara y orientada al cliente.

Herramientas disponibles: consultar_saldo, calcular_cuota_credito,
buscar_producto_bancario, registrar_reclamo.
"""


def demo_plan_and_execute():
    titulo("DEMO PLAN-AND-EXECUTE — Evaluación de Crédito Hipotecario")
    print("El agente genera un plan explícito antes de ejecutar herramientas.")
    print("Solicitud compleja: verificar cuenta + calcular dos plazos + listar requisitos.\n")

    llm = get_llm()
    memory = create_window_memory(k=5)

    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNING_SYSTEM),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, TOOLS, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8,
    )

    solicitud = (
        "Soy Ana Torres, RUT 11223344-5. Necesito evaluar si puedo pedir un crédito "
        "hipotecario de $80.000.000. Por favor revisa mi cuenta, calcula la cuota "
        "a 20 años y también a 15 años para comparar, y dime los requisitos."
    )
    print(f"  Cliente : {solicitud}")
    resp = chat(solicitud, memory, executor)
    print(f"\n  Respuesta:\n{resp}")

    # Condición cambiante: cliente reduce el monto
    print("\n" + "-" * 62)
    print("ADAPTACIÓN — Cliente cambia las condiciones del crédito")
    print("-" * 62)
    ajuste = "En realidad prefiero $60.000.000. ¿Cómo cambia la cuota a 20 años?"
    print(f"\n  Cliente : {ajuste}")
    resp2 = chat(ajuste, memory, executor)
    print(f"\n  Respuesta:\n{resp2}")

    print("\n[IE5+IE6] Plan explícito generado; el agente se adaptó al cambio de condiciones.")


# ── Demo Multi-Agente ─────────────────────────────────────────────────────────

def demo_multiagente():
    titulo("DEMO MULTI-AGENTE — Orquestación Secuencial CrewAI")
    print("Se invoca el equipo de agentes especializados para una solicitud compleja.\n")

    try:
        from orchestration.crew_orchestration import run_sequential
    except ImportError:
        print("Error importando crew_orchestration. Verifica que crewai esté instalado.")
        return

    solicitud = (
        "Tengo RUT 12345678-9 y quiero solicitar un crédito de consumo de $8.000.000 "
        "a 48 meses para financiar equipo de computación para mi empresa. "
        "¿Es viable y qué pasos debo seguir?"
    )
    datos = {"rut": "12345678-9", "nombre": "María González", "saldo": 2_450_000}

    resultado = run_sequential(solicitud, datos)

    print("\n[IL2.3] Orquestación secuencial: Analista → Asesor → Operaciones → Manager")
    print("[IE5]   Planificación descompuesta en tareas especializadas.")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo de Planificación y Orquestación")
    parser.add_argument(
        "--modo",
        choices=["planning", "multiagente", "todos"],
        default="todos",
        help="Modo de demo (default: todos)",
    )
    args = parser.parse_args()

    print("BANCO DIGITAL CHILE — Demo EP2: Planificación y Orquestación")
    print("Frameworks: LangChain (Plan-and-Execute) + CrewAI (Multi-Agente)\n")

    if args.modo in ("planning", "todos"):
        demo_plan_and_execute()

    if args.modo in ("multiagente", "todos"):
        demo_multiagente()

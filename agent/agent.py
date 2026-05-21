"""
Agente Principal - Banco Digital Chile
========================================
Agente conversacional que integra:
  - 5 herramientas bancarias (consulta, escritura, razonamiento)
  - Memoria a corto plazo (ConversationBufferWindowMemory)
  - Memoria a largo plazo (JSON persistente)
  - Ciclo ReAct gestionado por AgentExecutor de LangChain

Uso rápido:
    python agent.py
    python agent.py --rut 12345678-9
"""

import os
import argparse
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools import (
    consultar_saldo,
    realizar_transferencia,
    calcular_cuota_credito,
    registrar_reclamo,
    buscar_producto_bancario,
)
from memory import (
    create_window_memory,
    save_long_term,
    get_client_context_str,
    chat,
)


# ── Configuración del LLM ─────────────────────────────────────────────────────

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o",
        openai_api_base=os.environ.get("GITHUB_BASE_URL"),
        openai_api_key=os.environ.get("GITHUB_TOKEN"),
        temperature=0,
    )


# ── Construcción del agente ───────────────────────────────────────────────────

TOOLS = [
    consultar_saldo,
    realizar_transferencia,
    calcular_cuota_credito,
    registrar_reclamo,
    buscar_producto_bancario,
]

_BASE_SYSTEM = """Eres un asistente bancario inteligente de Banco Digital Chile.
Ayudas a los clientes con: consultas de saldo, transferencias, créditos, reclamos
e información de productos bancarios.

Reglas:
1. Para mostrar saldo o información sensible, solicita el RUT si no lo tienes.
2. Para transferencias, confirma los datos (origen, destino, monto) antes de ejecutar.
3. Para reclamos, solicita una descripción clara del problema.
4. Explica los resultados en lenguaje simple y profesional.
5. Ante solicitudes complejas, planifica los pasos antes de usar herramientas.

{contexto_cliente}"""


def build_agent_executor(llm, system_prompt: str) -> AgentExecutor:
    """Construye el AgentExecutor con el prompt personalizado para el cliente."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=6,
    )


# ── Sesión interactiva ────────────────────────────────────────────────────────

def run_session(rut_cliente: str | None = None):
    """
    Ejecuta una sesión conversacional con el agente bancario.

    Si se proporciona un RUT:
      - Carga el contexto de sesiones anteriores (largo plazo)
      - Persiste datos relevantes al cerrar la sesión
    La memoria a corto plazo (últimas 5 interacciones) se gestiona automáticamente.
    """
    llm = get_llm()

    # Recuperar contexto de largo plazo
    contexto = ""
    if rut_cliente:
        contexto = get_client_context_str(rut_cliente)
        if contexto:
            print(f"\n[Memoria recuperada para RUT {rut_cliente}]")
            print(contexto)

    system_prompt = _BASE_SYSTEM.format(contexto_cliente=contexto)
    agent_executor = build_agent_executor(llm, system_prompt)
    memory = create_window_memory(k=5)

    print("\n" + "=" * 62)
    print("   BANCO DIGITAL CHILE  –  Asistente Virtual (EP2)")
    print("=" * 62)
    print("Escribe 'salir' para terminar la sesión.\n")

    while True:
        entrada = input("Cliente: ").strip()
        if not entrada:
            continue
        if entrada.lower() in ("salir", "exit", "quit"):
            print("\nAsistente: Gracias por contactar a Banco Digital Chile. ¡Hasta pronto!\n")
            # Guardar en largo plazo que el cliente usó el asistente
            if rut_cliente:
                save_long_term(rut_cliente, "ultima_sesion", f"sesión activa {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}")
            break

        try:
            respuesta = chat(entrada, memory, agent_executor)
            print(f"\nAsistente: {respuesta}\n")
        except Exception as e:
            print(f"\nAsistente: Disculpe, ocurrió un error. Por favor intente de nuevo. ({e})\n")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Agente Bancario - Banco Digital Chile")
    parser.add_argument("--rut", default=None, help="RUT del cliente (ej: 12345678-9)")
    args = parser.parse_args()

    run_session(rut_cliente=args.rut)

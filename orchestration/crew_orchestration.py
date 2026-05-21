"""
Orquestación Multi-Agente con CrewAI - Banco Digital Chile
============================================================
Implementa dos estrategias de orquestación descritas en IL2.3:

  Secuencial   → Investigador → Analista → Asesor → Redactor
                 Flujo lineal predecible; cada tarea alimenta a la siguiente.

  Jerárquico   → Manager delega dinámicamente a Analista, Asesor u Operaciones
                 Mayor flexibilidad; el manager replanifica si algo falla.

Uso:
    python crew_orchestration.py
    python crew_orchestration.py --modo jerarquico
"""

import os
import argparse
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI


# ── LLM compartido ────────────────────────────────────────────────────────────

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o",
        openai_api_base=os.environ.get("GITHUB_BASE_URL"),
        openai_api_key=os.environ.get("GITHUB_TOKEN"),
        temperature=0,
    )


# ── Agentes especializados ────────────────────────────────────────────────────

def build_agents(llm):
    manager = Agent(
        role="Gerente de Atención al Cliente",
        goal=(
            "Coordinar y planificar la resolución completa de la solicitud del cliente, "
            "asegurando que todos los aspectos financieros, de productos y operacionales "
            "sean evaluados antes de emitir una respuesta definitiva."
        ),
        backstory=(
            "Eres gerente senior de Banco Digital Chile con 15 años de experiencia. "
            "Tu fortaleza es delegar al especialista correcto, sintetizar los análisis "
            "y comunicar soluciones claras al cliente."
        ),
        verbose=True,
        allow_delegation=True,
        llm=llm,
    )

    analista = Agent(
        role="Analista Financiero",
        goal=(
            "Evaluar la situación financiera del cliente, calcular métricas clave "
            "(cuotas, tasas, capacidad de pago) y determinar la viabilidad del crédito."
        ),
        backstory=(
            "Eres analista de riesgos con especialización en créditos. "
            "Dominas las fórmulas de amortización francesa y los modelos de scoring "
            "del banco. Tus informes son precisos y siempre incluyen números concretos."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    asesor = Agent(
        role="Asesor de Productos Bancarios",
        goal=(
            "Recomendar los productos más adecuados para el cliente según su perfil, "
            "necesidades y situación financiera evaluada por el analista."
        ),
        backstory=(
            "Conoces en detalle todos los productos de Banco Digital Chile: "
            "créditos de consumo, hipotecarios, cuentas corriente y de ahorro. "
            "Eres experto en hacer match entre necesidades del cliente y oferta bancaria."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    operaciones = Agent(
        role="Especialista en Operaciones",
        goal=(
            "Verificar la viabilidad operacional de la solicitud, identificar "
            "posibles impedimentos regulatorios y definir el proceso de implementación."
        ),
        backstory=(
            "Conoces los procesos internos y la normativa de la CMF aplicable al banco. "
            "Tu rol es asegurar que cualquier solución propuesta sea ejecutable "
            "dentro del marco regulatorio y en los tiempos comprometidos."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    return manager, analista, asesor, operaciones


# ── Tareas ────────────────────────────────────────────────────────────────────

def build_tasks(solicitud: str, datos_cliente: dict, manager, analista, asesor, operaciones):
    ctx = ""
    if datos_cliente:
        ctx = f"\nDatos del cliente: {datos_cliente}"

    tarea_analisis = Task(
        description=(
            f"Analiza financieramente la siguiente solicitud:\n'{solicitud}'{ctx}\n\n"
            "Debes:\n"
            "1. Identificar los aspectos financieros relevantes.\n"
            "2. Calcular métricas concretas (cuota mensual, total intereses, tasa mensual).\n"
            "3. Evaluar si el cliente cumple los requisitos financieros.\n"
            "4. Identificar riesgos o restricciones."
        ),
        agent=analista,
        expected_output=(
            "Informe financiero con: métricas calculadas numéricamente, "
            "evaluación de viabilidad (viable / no viable) y riesgos identificados."
        ),
    )

    tarea_productos = Task(
        description=(
            f"Con base en la solicitud '{solicitud}' y el análisis financiero previo:\n"
            "1. Identifica qué productos del banco son pertinentes.\n"
            "2. Compara opciones si hay más de una (ej. plazo 24 vs 36 meses).\n"
            "3. Emite una recomendación específica con justificación.\n"
            "4. Lista los requisitos y pasos para contratar el producto."
        ),
        agent=asesor,
        context=[tarea_analisis],
        expected_output=(
            "Recomendación de producto con comparativa de opciones, "
            "justificación técnica y lista de pasos a seguir por el cliente."
        ),
    )

    tarea_operaciones = Task(
        description=(
            f"Verifica la viabilidad operacional de la solicitud '{solicitud}':\n"
            "1. Describe los procesos internos involucrados.\n"
            "2. Identifica posibles impedimentos o documentos requeridos.\n"
            "3. Propone el flujo de implementación paso a paso.\n"
            "4. Estima los tiempos de resolución."
        ),
        agent=operaciones,
        context=[tarea_analisis, tarea_productos],
        expected_output=(
            "Plan operacional con: flujo de implementación, documentos requeridos "
            "y tiempos estimados de resolución."
        ),
    )

    tarea_resolucion = Task(
        description=(
            f"Como gerente, consolida los tres informes y redacta la respuesta final al cliente.\n"
            f"Solicitud original: '{solicitud}'\n\n"
            "La respuesta debe incluir:\n"
            "1. Resumen ejecutivo de la solución recomendada.\n"
            "2. Información financiera clave (cuota, tasa, total).\n"
            "3. Próximos pasos concretos y ordenados para el cliente.\n"
            "4. Requisitos y documentación necesaria.\n"
            "5. Tiempo estimado de resolución.\n"
            "Tono: profesional, empático y orientado al cliente."
        ),
        agent=manager,
        context=[tarea_analisis, tarea_productos, tarea_operaciones],
        expected_output=(
            "Respuesta ejecutiva completa para el cliente: resumen, datos financieros, "
            "pasos a seguir, requisitos y tiempos."
        ),
    )

    return tarea_analisis, tarea_productos, tarea_operaciones, tarea_resolucion


# ── Modo Secuencial ───────────────────────────────────────────────────────────

def run_sequential(solicitud: str, datos_cliente: dict = None):
    """
    Proceso secuencial: Analista → Asesor → Operaciones → Manager.
    Orden fijo; el output de cada tarea es contexto de la siguiente.
    """
    llm = get_llm()
    manager, analista, asesor, operaciones = build_agents(llm)
    tareas = build_tasks(solicitud, datos_cliente or {}, manager, analista, asesor, operaciones)

    crew = Crew(
        agents=[analista, asesor, operaciones, manager],
        tasks=list(tareas),
        process=Process.sequential,
        verbose=True,
    )

    print("\n" + "=" * 62)
    print("MODO SECUENCIAL  —  Analista → Asesor → Operaciones → Manager")
    print("=" * 62)
    resultado = crew.kickoff()
    return resultado


# ── Modo Jerárquico ───────────────────────────────────────────────────────────

def run_hierarchical(solicitud: str, datos_cliente: dict = None):
    """
    Proceso jerárquico: Manager planifica y delega dinámicamente.
    Más adaptativo; el manager puede reasignar tareas si algo cambia.
    """
    llm = get_llm()
    manager, analista, asesor, operaciones = build_agents(llm)
    tareas = build_tasks(solicitud, datos_cliente or {}, manager, analista, asesor, operaciones)

    crew = Crew(
        agents=[manager, analista, asesor, operaciones],
        tasks=list(tareas),
        process=Process.hierarchical,
        manager_llm=llm,
        verbose=True,
    )

    print("\n" + "=" * 62)
    print("MODO JERÁRQUICO  —  Manager delega a especialistas")
    print("=" * 62)
    resultado = crew.kickoff()
    return resultado


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Orquestación Multi-Agente CrewAI")
    parser.add_argument(
        "--modo",
        choices=["secuencial", "jerarquico"],
        default="secuencial",
        help="Estrategia de orquestación (default: secuencial)",
    )
    args = parser.parse_args()

    SOLICITUD = (
        "Soy cliente del banco (RUT 12345678-9) y quiero solicitar un crédito de consumo "
        "de $5.000.000 a 36 meses para remodelar mi casa. "
        "¿Cuánto pagaría mensualmente y qué necesito para aplicar?"
    )
    DATOS = {"rut": "12345678-9", "nombre": "María González", "saldo_actual": 2_450_000}

    if args.modo == "secuencial":
        resultado = run_sequential(SOLICITUD, DATOS)
    else:
        resultado = run_hierarchical(SOLICITUD, DATOS)

    print("\n" + "=" * 62)
    print("RESPUESTA FINAL AL CLIENTE:")
    print("=" * 62)
    print(resultado)

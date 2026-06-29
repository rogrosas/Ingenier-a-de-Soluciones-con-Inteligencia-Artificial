"""
Base de Conocimiento del Agente — Banco Digital Chile (RAG, IL1.3 / EFT IE2)
============================================================================
Combina DOS tipos de fuentes para enriquecer las respuestas del modelo:

  • FUENTES INTERNAS  → catálogo de productos y políticas operativas del banco.
  • FUENTES EXTERNAS  → marco normativo y de protección al consumidor financiero
                        (CMF, SERNAC, Ley 19.628). Son extractos divulgativos
                        redactados por el equipo como referencia, no transcripción
                        literal de la norma.

Cada documento declara su `origen` ("interna"/"externa") para evidenciar la
combinación de fuentes exigida por la rúbrica del Informe Final Transversal.
"""

from __future__ import annotations

# Cada entrada: id, origen, fuente, texto
DOCUMENTOS = [
    # ── Fuentes internas (productos y políticas del banco) ────────────────────
    {
        "id": "int-credito-consumo",
        "origen": "interna",
        "fuente": "Catálogo de productos — Banco Digital Chile",
        "texto": (
            "El Crédito de Consumo de Banco Digital Chile tiene una tasa anual de 18%, "
            "plazo máximo de 60 meses y montos entre $500.000 y $50.000.000. Requisitos: "
            "ser cliente del banco, renta mínima de $400.000 y no registrar morosidades."
        ),
    },
    {
        "id": "int-credito-hipotecario",
        "origen": "interna",
        "fuente": "Catálogo de productos — Banco Digital Chile",
        "texto": (
            "El Crédito Hipotecario ofrece una tasa anual de 4,5%, plazo de hasta 300 meses "
            "y montos desde $10.000.000. Requisitos: renta mínima de $800.000, pie mínimo "
            "del 10% y avalúo fiscal aprobado."
        ),
    },
    {
        "id": "int-cuenta-corriente",
        "origen": "interna",
        "fuente": "Catálogo de productos — Banco Digital Chile",
        "texto": (
            "La Cuenta Corriente tiene un costo de mantención mensual de $3.990, permite "
            "sobregiro y tarjeta de crédito. Requisitos: ser mayor de 18 años y renta "
            "demostrable sobre $300.000."
        ),
    },
    {
        "id": "int-politica-transferencias",
        "origen": "interna",
        "fuente": "Política operativa — Banco Digital Chile",
        "texto": (
            "Toda transferencia requiere confirmación explícita del cliente de origen, "
            "destino y monto. El sistema valida saldo suficiente antes de ejecutar y "
            "registra la operación para auditoría. No se ejecutan transferencias automáticas "
            "sin autorización del titular."
        ),
    },
    {
        "id": "int-politica-reclamos",
        "origen": "interna",
        "fuente": "Política de servicio — Banco Digital Chile",
        "texto": (
            "Los reclamos por cobro indebido, bloqueo de tarjeta o error de transferencia "
            "tienen un SLA de respuesta de 24 horas; el resto de los reclamos, 72 horas. "
            "Cada reclamo genera un ticket con número de seguimiento."
        ),
    },
    # ── Fuentes externas (normativa y protección al consumidor) ───────────────
    {
        "id": "ext-cmf-creditos",
        "origen": "externa",
        "fuente": "CMF — Información al cliente bancario (referencia divulgativa)",
        "texto": (
            "La Comisión para el Mercado Financiero exige informar al cliente la Carga Anual "
            "Equivalente (CAE) y el costo total del crédito antes de su contratación, "
            "permitiendo comparar productos de distintas instituciones de forma transparente."
        ),
    },
    {
        "id": "ext-sernac-derechos",
        "origen": "externa",
        "fuente": "SERNAC — Derechos del consumidor financiero (referencia divulgativa)",
        "texto": (
            "El consumidor financiero tiene derecho a información veraz y oportuna, a la "
            "libre elección, y a no ser discriminado arbitrariamente. Las cláusulas abusivas "
            "en contratos de adhesión son nulas según la Ley del Consumidor."
        ),
    },
    {
        "id": "ext-ley-19628",
        "origen": "externa",
        "fuente": "Ley 19.628 sobre protección de datos personales (referencia divulgativa)",
        "texto": (
            "El tratamiento de datos personales como el RUT requiere finalidad legítima y "
            "proporcionalidad. La entidad debe proteger los datos del titular y limitar su uso "
            "al propósito informado, resguardando la privacidad del cliente."
        ),
    },
]

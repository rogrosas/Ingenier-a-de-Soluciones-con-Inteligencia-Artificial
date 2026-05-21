"""
Herramientas del Agente Bancario - Banco Digital Chile
=======================================================
Herramientas de consulta, escritura y razonamiento que el agente
usa de forma autónoma para resolver solicitudes del cliente.
"""

import json
import os
from datetime import datetime
from langchain_core.tools import tool

# ── Base de datos simulada ────────────────────────────────────────────────────

CUENTAS = {
    "12345678-9": {
        "nombre": "María González",
        "saldo": 2_450_000,
        "tipo": "Cuenta Corriente",
        "productos": ["Tarjeta Débito", "Seguro de Vida"],
    },
    "98765432-1": {
        "nombre": "Carlos Pérez",
        "saldo": 850_000,
        "tipo": "Cuenta Vista",
        "productos": ["Tarjeta Prepago"],
    },
    "11223344-5": {
        "nombre": "Ana Torres",
        "saldo": 5_200_000,
        "tipo": "Cuenta Ahorro",
        "productos": ["Tarjeta Débito", "Crédito Hipotecario"],
    },
}

PRODUCTOS_BANCARIOS = {
    "credito_consumo": {
        "nombre": "Crédito de Consumo",
        "tasa_anual": 0.18,
        "plazo_max_meses": 60,
        "monto_min": 500_000,
        "monto_max": 50_000_000,
        "requisitos": ["Ser cliente del banco", "Renta mínima $400.000", "Sin morosidades"],
    },
    "credito_hipotecario": {
        "nombre": "Crédito Hipotecario",
        "tasa_anual": 0.045,
        "plazo_max_meses": 300,
        "monto_min": 10_000_000,
        "monto_max": 500_000_000,
        "requisitos": ["Renta mínima $800.000", "Pie mínimo 10%", "Avalúo fiscal aprobado"],
    },
    "cuenta_corriente": {
        "nombre": "Cuenta Corriente",
        "costo_mantencion_mensual": 3_990,
        "sobregiro_disponible": True,
        "tarjeta_credito": True,
        "requisitos": ["Mayor de 18 años", "Renta demostrable $300.000+"],
    },
    "cuenta_ahorro": {
        "nombre": "Cuenta de Ahorro",
        "costo_mantencion_mensual": 0,
        "tasa_interes_anual": 0.003,
        "requisitos": ["Mayor de 18 años", "Cédula de identidad vigente"],
    },
}


def _fmt(valor: float) -> str:
    return f"${valor:,.0f}".replace(",", ".")


# ── Herramientas ──────────────────────────────────────────────────────────────

@tool
def consultar_saldo(rut: str) -> str:
    """
    Consulta el saldo y la información de cuenta de un cliente dado su RUT.
    Parámetro: rut (str) - RUT del cliente en formato '12345678-9'.
    Retorna saldo disponible, tipo de cuenta y productos contratados.
    Úsala cuando el cliente quiera saber su saldo o productos activos.
    """
    cuenta = CUENTAS.get(rut.strip())
    if not cuenta:
        return (
            f"No se encontró cuenta para el RUT {rut}. "
            "Verifique el número e intente nuevamente."
        )
    productos = ", ".join(cuenta["productos"])
    return (
        f"CONSULTA DE SALDO  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Cliente          : {cuenta['nombre']}\n"
        f"Tipo de Cuenta   : {cuenta['tipo']}\n"
        f"Saldo Disponible : {_fmt(cuenta['saldo'])}\n"
        f"Productos        : {productos}"
    )


@tool
def realizar_transferencia(origen_rut: str, destino_rut: str, monto: float) -> str:
    """
    Realiza una transferencia entre cuentas del banco validando saldo suficiente.
    Parámetros:
      - origen_rut (str): RUT cuenta origen en formato '12345678-9'
      - destino_rut (str): RUT cuenta destino en formato '12345678-9'
      - monto (float): Monto en pesos chilenos a transferir
    Úsala solo cuando el cliente haya confirmado explícitamente la transferencia.
    """
    if origen_rut not in CUENTAS:
        return f"Error: cuenta de origen RUT {origen_rut} no encontrada."
    if destino_rut not in CUENTAS:
        return f"Error: cuenta de destino RUT {destino_rut} no encontrada."
    if monto <= 0:
        return "Error: el monto debe ser mayor a cero."

    cuenta_origen = CUENTAS[origen_rut]
    cuenta_destino = CUENTAS[destino_rut]

    if cuenta_origen["saldo"] < monto:
        return (
            f"Transferencia rechazada: saldo insuficiente.\n"
            f"Saldo disponible : {_fmt(cuenta_origen['saldo'])}\n"
            f"Monto solicitado : {_fmt(monto)}"
        )

    CUENTAS[origen_rut]["saldo"] -= monto
    CUENTAS[destino_rut]["saldo"] += monto

    return (
        f"TRANSFERENCIA EXITOSA  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Origen  : {cuenta_origen['nombre']} ({origen_rut})\n"
        f"Destino : {cuenta_destino['nombre']} ({destino_rut})\n"
        f"Monto   : {_fmt(monto)}\n"
        f"Saldo restante origen: {_fmt(CUENTAS[origen_rut]['saldo'])}"
    )


@tool
def calcular_cuota_credito(monto: float, plazo_meses: int, tipo_credito: str) -> str:
    """
    Calcula la cuota mensual de un crédito usando la fórmula de amortización francesa.
    Parámetros:
      - monto (float): Monto del crédito en pesos
      - plazo_meses (int): Plazo en meses
      - tipo_credito (str): 'consumo' o 'hipotecario'
    Retorna cuota, interés total y costo total del crédito.
    Úsala cuando el cliente quiera simular un crédito o evaluar opciones de financiamiento.
    """
    tipo_key = f"credito_{tipo_credito.lower().strip()}"
    if tipo_key not in PRODUCTOS_BANCARIOS:
        disponibles = [k.replace("credito_", "") for k in PRODUCTOS_BANCARIOS if k.startswith("credito_")]
        return f"Tipo '{tipo_credito}' no válido. Opciones: {', '.join(disponibles)}."

    producto = PRODUCTOS_BANCARIOS[tipo_key]
    tasa_m = producto["tasa_anual"] / 12

    if tasa_m == 0:
        cuota = monto / plazo_meses
    else:
        cuota = monto * (tasa_m * (1 + tasa_m) ** plazo_meses) / ((1 + tasa_m) ** plazo_meses - 1)

    total = cuota * plazo_meses
    intereses = total - monto
    req = "; ".join(producto["requisitos"])

    return (
        f"SIMULACIÓN DE CRÉDITO  —  {producto['nombre']}\n"
        f"Monto solicitado : {_fmt(monto)}\n"
        f"Plazo            : {plazo_meses} meses\n"
        f"Tasa anual       : {producto['tasa_anual']*100:.2f}%\n"
        f"Tasa mensual     : {tasa_m*100:.3f}%\n"
        f"─────────────────────────────────────\n"
        f"Cuota mensual    : {_fmt(cuota)}\n"
        f"Total intereses  : {_fmt(intereses)}\n"
        f"Total a pagar    : {_fmt(total)}\n"
        f"─────────────────────────────────────\n"
        f"Requisitos       : {req}"
    )


@tool
def registrar_reclamo(tipo: str, descripcion: str, rut_cliente: str) -> str:
    """
    Registra un reclamo formal del cliente en el sistema del banco y emite un ticket.
    Parámetros:
      - tipo (str): Categoría del reclamo: 'cobro_indebido', 'bloqueo_tarjeta',
                    'servicio_deficiente', 'error_transferencia', 'otro'
      - descripcion (str): Descripción detallada del problema
      - rut_cliente (str): RUT del cliente que realiza el reclamo
    Retorna número de ticket y tiempo de respuesta estimado (SLA).
    Úsala cuando el cliente quiera presentar una queja o solicitud formal.
    """
    import random

    ticket_id = f"RC{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    sla = 24 if tipo in ("cobro_indebido", "bloqueo_tarjeta", "error_transferencia") else 72

    reclamo = {
        "ticket": ticket_id,
        "fecha": datetime.now().isoformat(),
        "tipo": tipo,
        "descripcion": descripcion,
        "rut_cliente": rut_cliente,
        "estado": "RECIBIDO",
        "sla_horas": sla,
    }

    reclamos_file = os.path.join(os.path.dirname(__file__), "reclamos.json")
    reclamos: list = []
    if os.path.exists(reclamos_file):
        with open(reclamos_file, "r", encoding="utf-8") as f:
            reclamos = json.load(f)
    reclamos.append(reclamo)
    with open(reclamos_file, "w", encoding="utf-8") as f:
        json.dump(reclamos, f, ensure_ascii=False, indent=2)

    return (
        f"RECLAMO REGISTRADO  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Ticket           : {ticket_id}\n"
        f"Tipo             : {tipo}\n"
        f"Estado           : RECIBIDO\n"
        f"SLA de respuesta : {sla} horas\n"
        f"Guarde su número de ticket para hacer seguimiento."
    )


@tool
def buscar_producto_bancario(tipo_producto: str) -> str:
    """
    Busca y retorna información detallada de un producto bancario disponible.
    Parámetro: tipo_producto (str) - Uno de: 'credito_consumo', 'credito_hipotecario',
               'cuenta_corriente', 'cuenta_ahorro'.
    Retorna características, condiciones y requisitos del producto.
    Úsala cuando el cliente pregunte por características o condiciones de un producto.
    """
    producto = PRODUCTOS_BANCARIOS.get(tipo_producto.lower().strip())
    if not producto:
        disponibles = list(PRODUCTOS_BANCARIOS.keys())
        return (
            f"Producto '{tipo_producto}' no encontrado.\n"
            f"Disponibles: {', '.join(disponibles)}"
        )

    lineas = [f"PRODUCTO: {producto['nombre']}", "─" * 45]
    for clave, valor in producto.items():
        if clave == "nombre":
            continue
        if isinstance(valor, list):
            lineas.append(f"{clave:30s}: {'; '.join(str(v) for v in valor)}")
        elif isinstance(valor, float) and valor < 1:
            lineas.append(f"{clave:30s}: {valor*100:.3f}%")
        elif isinstance(valor, int) and valor > 1_000:
            lineas.append(f"{clave:30s}: {_fmt(valor)}")
        else:
            lineas.append(f"{clave:30s}: {valor}")

    return "\n".join(lineas)

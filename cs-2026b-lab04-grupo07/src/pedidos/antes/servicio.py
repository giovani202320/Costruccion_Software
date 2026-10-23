"""
Versión ingenua del Servicio de Pedidos (antes de aplicar patrones).
Contiene múltiples olores de código: condicionales complejos, acoplamiento a SDKs externos,
lógica de reintentos duplicada, manejo directo de eventos y estados por strings.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from ..externos import YapeSDK, PlinClient


@dataclass
class Linea:
    """Línea de pedido con producto, cantidad y precio unitario."""
    producto: str
    cantidad: float
    precio: float

    def subtotal(self) -> float:
        return self.cantidad * self.precio


@dataclass
class Pedido:
    """Entidad Pedido con estado representado mediante cadena simple."""
    id: int
    celular: str
    lineas: List[Linea] = field(default_factory=list)
    estado: str = "BORRADOR"
    operacion: Optional[str] = None

    def total(self) -> float:
        return sum(linea.cantidad * linea.precio for linea in self.lineas)


class ServicioPedidos:
    """Servicio monolítico sin patrones de diseño."""
    def __init__(self, yape: Optional[YapeSDK] = None, plin: Optional[PlinClient] = None):
        self.yape = yape or YapeSDK()
        self.plin = plin or PlinClient()
        self.eventos: List[str] = []

    def confirmar_y_pagar(self, pedido: Pedido, medio: str) -> str:
        # Olor: Condicionales anidados sobre pedido.estado
        if pedido.estado != "BORRADOR":
            if pedido.estado == "CANCELADO":
                raise ValueError("El pedido está cancelado")
            elif pedido.estado == "PAGADO":
                raise ValueError("El pedido ya fue pagado")
            else:
                raise ValueError("Estado no válido")

        if not pedido.lineas:
            raise ValueError("El pedido no tiene líneas")

        total = 0.0
        for linea in pedido.lineas:
            total += linea.cantidad * linea.precio

        # BUG detectado: se muta el estado antes de validar si el medio de pago existe
        pedido.estado = "CONFIRMADO"

        aprobado = False
        operacion = None

        # Olor: if/elif por medio de pago + conocimiento directo de SDKs + reintentos duplicados
        if medio == "YAPE":
            for intento in range(3):
                try:
                    r = self.yape.realizar_cobro(pedido.celular, total)
                    aprobado, operacion = r["ok"], r.get("operacion")
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        elif medio == "PLIN":
            for intento in range(3):
                try:
                    codigo, tx = self.plin.charge(int(round(total * 100)), pedido.celular)
                    aprobado, operacion = (codigo == 200), tx
                    break
                except TimeoutError:
                    if intento == 2:
                        aprobado = False
        else:
            raise ValueError(f"Medio de pago no soportado: {medio}")

        if aprobado:
            pedido.estado = "PAGADO"
            pedido.operacion = operacion
            # Olor: el servicio arma a mano los mensajes de notificación
            self.eventos.append(f"whatsapp:{pedido.celular}:Pedido {pedido.id} pagado")
            self.eventos.append(f"reporte:{pedido.id}:{total:.2f}")
        else:
            pedido.estado = "CANCELADO"

        return pedido.estado

    def sugerir_descripcion(self, producto: str, proveedor: str = "OPENAI") -> str:
        """Olor: proveedor no aislado, guardrails acoplados en condicionales."""
        if proveedor == "OPENAI":
            respuesta = f"Delicioso {producto} fresco del Mercado San Camilo directo a su mesa."
        elif proveedor == "CLAUDE":
            respuesta = f"Excelente selección de {producto} garantizado por comerciantes de San Camilo."
        elif proveedor == "LOCAL":
            respuesta = f"Producto: {producto} de primera calidad."
        else:
            raise ValueError(f"Proveedor no soportado: {proveedor}")

        if "S/" in respuesta:
            raise ValueError("Guardrail: la IA incluyó un precio")
        for palabra in ["orgánico certificado", "cura", "garantizado"]:
            if palabra in respuesta.lower():
                raise ValueError(f"Guardrail: afirmación no permitida '{palabra}'")
        if len(respuesta) > 200:
            raise ValueError("Guardrail: respuesta excede longitud máxima")

        return respuesta

"""
Patrón State para el ciclo de vida del Pedido en San Camilo en Línea.
Implementa la máquina de estados del Lab 05 prohibiendo transiciones inválidas por construcción.
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import List, Optional


class EstadoPedido(ABC):
    """Clase base abstracta de Estado. Prohíbe todas las transiciones por defecto."""
    nombre: str = "?"

    def confirmar(self, pedido: Pedido) -> None:
        raise ValueError(f"No se puede confirmar un pedido en estado {self.nombre}")

    def pagar(self, pedido: Pedido, operacion: str) -> None:
        raise ValueError(f"No se puede pagar un pedido en estado {self.nombre}")

    def cancelar(self, pedido: Pedido, motivo: str = "") -> None:
        raise ValueError(f"No se puede cancelar un pedido en estado {self.nombre}")


class Borrador(EstadoPedido):
    """Estado inicial: permite agregar líneas, confirmar y cancelar."""
    nombre = "BORRADOR"

    def confirmar(self, pedido: Pedido) -> None:
        if not pedido.lineas:
            raise ValueError("El pedido no tiene líneas")
        pedido.cambiar_a(Confirmado())

    def cancelar(self, pedido: Pedido, motivo: str = "") -> None:
        pedido.cambiar_a(Cancelado())


class Confirmado(EstadoPedido):
    """Pedido con stock validado listo para efectuar cobro."""
    nombre = "CONFIRMADO"

    def pagar(self, pedido: Pedido, operacion: str) -> None:
        pedido.operacion = operacion
        pedido.cambiar_a(Pagado())

    def cancelar(self, pedido: Pedido, motivo: str = "") -> None:
        pedido.cambiar_a(Cancelado())


class Pagado(EstadoPedido):
    """Estado final exitoso: comprobante aprobado y verificado."""
    nombre = "PAGADO"

    def confirmar(self, pedido: Pedido) -> None:
        raise ValueError("El pedido ya fue pagado")

    def pagar(self, pedido: Pedido, operacion: str) -> None:
        raise ValueError("El pedido ya fue pagado")

    def cancelar(self, pedido: Pedido, motivo: str = "") -> None:
        raise ValueError("No se puede cancelar un pedido ya pagado")


class Cancelado(EstadoPedido):
    """Estado final terminal: pago fallido o descarte de compra."""
    nombre = "CANCELADO"

    def confirmar(self, pedido: Pedido) -> None:
        raise ValueError("El pedido está cancelado")

    def pagar(self, pedido: Pedido, operacion: str) -> None:
        raise ValueError("El pedido está cancelado")

    def cancelar(self, pedido: Pedido, motivo: str = "") -> None:
        raise ValueError("El pedido ya está cancelado")


@dataclass
class Linea:
    """Línea de ítem en el pedido."""
    producto: str
    cantidad: float
    precio: float

    def subtotal(self) -> float:
        return self.cantidad * self.precio


class Pedido:
    """Contexto que delega su comportamiento al objeto Estado actual."""
    def __init__(self, id: int, celular: str, lineas: Optional[List[Linea]] = None, estado: str = "BORRADOR") -> None:
        self.id = id
        self.celular = celular
        self.lineas: List[Linea] = lineas if lineas is not None else []
        self.operacion: Optional[str] = None
        self._estado: EstadoPedido = self._crear_estado(estado)

    def _crear_estado(self, nombre: str) -> EstadoPedido:
        mapa = {
            "BORRADOR": Borrador(),
            "CONFIRMADO": Confirmado(),
            "PAGADO": Pagado(),
            "CANCELADO": Cancelado(),
        }
        if nombre not in mapa:
            raise ValueError(f"Estado no válido: {nombre}")
        return mapa[nombre]

    @property
    def estado(self) -> str:
        return self._estado.nombre

    @estado.setter
    def estado(self, nuevo: str | EstadoPedido) -> None:
        if isinstance(nuevo, EstadoPedido):
            self._estado = nuevo
        elif isinstance(nuevo, str):
            self._estado = self._crear_estado(nuevo)
        else:
            raise TypeError("El estado debe ser una cadena o instancia de EstadoPedido")

    def cambiar_a(self, nuevo_estado: EstadoPedido) -> None:
        self._estado = nuevo_estado

    def confirmar(self) -> None:
        self._estado.confirmar(self)

    def pagar(self, operacion: Optional[str] = None) -> None:
        self._estado.pagar(self, operacion or "")

    def cancelar(self, motivo: str = "") -> None:
        self._estado.cancelar(self, motivo)

    def total(self) -> float:
        return sum(linea.cantidad * linea.precio for linea in self.lineas)

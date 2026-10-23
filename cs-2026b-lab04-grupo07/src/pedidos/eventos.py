"""
Patrón Observer para el sistema de notificaciones y eventos de San Camilo en Línea.
Permite desacoplar las acciones posteriores al pago (WhatsApp, reportes, auditoría)
del flujo principal del Servicio de Pedidos.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Suscriptor(ABC):
    """Interfaz del observador que reacciona a eventos emitidos por el dominio."""
    @abstractmethod
    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        """Maneja la notificación del evento con su respectivo payload."""
        ...


class PublicadorEventos:
    """Sujeto observable (Event Publisher) que mantiene el registro de suscriptores."""
    def __init__(self) -> None:
        self._suscriptores: Dict[str, List[Suscriptor]] = {}

    def suscribir(self, evento: str, suscriptor: Suscriptor) -> None:
        """Registra un observador interesado en un tipo de evento específico."""
        self._suscriptores.setdefault(evento, []).append(suscriptor)

    def desuscribir(self, evento: str, suscriptor: Suscriptor) -> None:
        """Elimina la suscripción de un observador."""
        if evento in self._suscriptores and suscriptor in self._suscriptores[evento]:
            self._suscriptores[evento].remove(suscriptor)

    def publicar(self, evento: str, datos: Dict[str, Any]) -> None:
        """Difunde el evento a todos los suscriptores registrados."""
        for s in self._suscriptores.get(evento, []):
            s.actualizar(evento, datos)


# ============================================================================
# Suscriptores Concretos (Mercado San Camilo)
# ============================================================================

class NotificadorWhatsApp(Suscriptor):
    """Observador que formatea y despacha notificaciones WhatsApp a clientes/comerciantes."""
    def __init__(self, bandeja: List[str]) -> None:
        self._bandeja = bandeja

    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        self._bandeja.append(f"whatsapp:{datos['celular']}:Pedido {datos['id']} pagado")


class ActualizadorReportes(Suscriptor):
    """Observador que registra el total transaccionado para reportes contables."""
    def __init__(self, bandeja: List[str]) -> None:
        self._bandeja = bandeja

    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        self._bandeja.append(f"reporte:{datos['id']}:{datos['total']:.2f}")


class AuditoriaPedidos(Suscriptor):
    """Observador adicional para verificar trazabilidad y auditoría sin modificar el servicio."""
    def __init__(self) -> None:
        self.registros: List[Dict[str, Any]] = []

    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        self.registros.append({"evento": evento, **datos})

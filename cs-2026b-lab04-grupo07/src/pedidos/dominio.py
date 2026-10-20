"""
Módulo de Dominio de Pedidos y Pagos - San Camilo en Línea
Implementación en Python 3.10 con dataclasses, Enum y type hints,
alineado al diagrama de diseño UML (clases.puml) y a los principios
del ADR-001 (Monolito Modular con Puertos y Adaptadores).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


# ============================================================================
# Enumeraciones del Dominio
# ============================================================================

class EstadoPedido(str, Enum):
    """Ciclo de vida del pedido consolidado multi-puesto."""
    BORRADOR = "BORRADOR"
    CONFIRMADO = "CONFIRMADO"
    PAGO_PENDIENTE = "PAGO_PENDIENTE"
    PAGADO = "PAGADO"
    EN_PREPARACION = "EN_PREPARACION"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class EstadoPedidoPuesto(str, Enum):
    """Ciclo de vida de la suborden individual por cada puesto comercial."""
    RECIBIDO = "RECIBIDO"
    LISTO = "LISTO"
    RECOGIDO = "RECOGIDO"
    ENTREGADO = "ENTREGADO"
    RECHAZADO = "RECHAZADO"


class MedioPago(str, Enum):
    """Medios de pago admitidos para el MVP."""
    YAPE = "YAPE"
    PLIN = "PLIN"


class ModalidadEntrega(str, Enum):
    """Modalidad de entrega elegida por el cliente."""
    RECOJO_EN_PUESTO = "RECOJO_EN_PUESTO"
    DELIVERY = "DELIVERY"


# ============================================================================
# Entidades del Dominio (Catálogo y Usuarios)
# ============================================================================

@dataclass
class Cliente:
    """Cliente comprador de la plataforma."""
    id: UUID = field(default_factory=uuid4)
    nombre_completo: str = ""
    telefono: str = ""
    direccion_entrega: str = ""

    def get_telefono(self) -> str:
        return self.telefono


@dataclass
class Comerciante:
    """Comerciante titular de un puesto del Mercado San Camilo."""
    id: UUID = field(default_factory=uuid4)
    nombre_completo: str = ""
    telefono_whatsapp: str = ""
    dni: str = ""

    def recibir_aviso(self, mensaje: str) -> None:
        """Registra la recepción de un mensaje de comanda."""
        pass


@dataclass
class Puesto:
    """Puesto físico comercial del Mercado San Camilo."""
    id: UUID = field(default_factory=uuid4)
    numero_puesto: str = ""
    seccion_mercado: str = ""
    nombre_comercial: str = ""
    comerciante: Optional[Comerciante] = None

    def get_comerciante(self) -> Optional[Comerciante]:
        return self.comerciante


@dataclass
class Producto:
    """Producto u oferta comercializada en un puesto específico."""
    id: UUID = field(default_factory=uuid4)
    nombre: str = ""
    precio_unitario: Decimal = Decimal("0.00")
    stock_disponible: int = 0
    unidad_medida: str = "kg"
    puesto: Optional[Puesto] = None

    def reservar(self, cantidad: int) -> None:
        """Bloquea temporalmente el stock del producto."""
        if cantidad <= 0:
            raise ValueError("La cantidad a reservar debe ser positiva.")
        if self.stock_disponible < cantidad:
            raise ValueError(f"Stock insuficiente para {self.nombre}. Disponible: {self.stock_disponible}")
        self.stock_disponible -= cantidad

    def liberar(self, cantidad: int) -> None:
        """Restaura el stock reservado ante cancelación."""
        if cantidad > 0:
            self.stock_disponible += cantidad


# ============================================================================
# Entidades del Dominio (Pedidos y Pagos)
# ============================================================================

@dataclass
class LineaPedido:
    """Ítem individual perteneciente a un subpedido de puesto."""
    id: UUID = field(default_factory=uuid4)
    producto: Optional[Producto] = None
    cantidad: int = 1
    precio_unitario: Decimal = Decimal("0.00")

    def subtotal(self) -> Decimal:
        """Calcula el subtotal monetario de la línea."""
        return self.precio_unitario * Decimal(self.cantidad)


@dataclass
class PedidoPuesto:
    """Suborden desagregada correspondiente a un puesto comercial específico."""
    id: UUID = field(default_factory=uuid4)
    puesto: Optional[Puesto] = None
    lineas: List[LineaPedido] = field(default_factory=list)
    subtotal_puesto: Decimal = Decimal("0.00")
    estado_puesto: EstadoPedidoPuesto = EstadoPedidoPuesto.RECIBIDO

    def calcular_subtotal(self) -> Decimal:
        self.subtotal_puesto = sum((linea.subtotal() for linea in self.lineas), Decimal("0.00"))
        return self.subtotal_puesto

    def marcar_listo(self) -> None:
        if self.estado_puesto != EstadoPedidoPuesto.RECIBIDO:
            raise ValueError("Solo un pedido recibido puede marcarse como listo.")
        self.estado_puesto = EstadoPedidoPuesto.LISTO

    def marcar_recogido(self) -> None:
        if self.estado_puesto != EstadoPedidoPuesto.LISTO:
            raise ValueError("El pedido debe estar listo antes de ser recogido.")
        self.estado_puesto = EstadoPedidoPuesto.RECOGIDO

    def rechazar(self, motivo: str) -> None:
        self.estado_puesto = EstadoPedidoPuesto.RECHAZADO


@dataclass
class Pago:
    """Comprobante y registro de transferencia electrónica Yape/Plin."""
    id: UUID = field(default_factory=uuid4)
    monto: Decimal = Decimal("0.00")
    medio: MedioPago = MedioPago.YAPE
    codigo_operacion: str = ""
    comprobante_url: str = ""
    fecha_pago: datetime = field(default_factory=datetime.utcnow)
    aprobado: bool = False

    def es_aprobado(self) -> bool:
        return self.aprobado


@dataclass
class Pedido:
    """Raíz de agregación (Aggregate Root) del pedido consolidado multi-puesto."""
    id: UUID = field(default_factory=uuid4)
    cliente: Optional[Cliente] = None
    codigo_seguimiento: str = ""
    fecha_creacion: datetime = field(default_factory=datetime.utcnow)
    subpedidos: List[PedidoPuesto] = field(default_factory=list)
    total_consolidado: Decimal = Decimal("0.00")
    estado: EstadoPedido = EstadoPedido.BORRADOR
    modalidad: ModalidadEntrega = ModalidadEntrega.RECOJO_EN_PUESTO
    pago: Optional[Pago] = None

    def agregar_producto(self, producto: Producto, cantidad: int, puesto: Puesto) -> None:
        """Agrega un producto agrupándolo en el subpedido del puesto correspondiente."""
        if self.estado != EstadoPedido.BORRADOR:
            raise ValueError("No se pueden agregar productos a un pedido ya confirmado.")
        
        # Buscar o crear el subpedido para este puesto
        sub = next((sp for sp in self.subpedidos if sp.puesto and sp.puesto.id == puesto.id), None)
        if sub is None:
            sub = PedidoPuesto(puesto=puesto)
            self.subpedidos.append(sub)

        linea = LineaPedido(
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_unitario
        )
        sub.lineas.append(linea)
        sub.calcular_subtotal()
        self.calcular_total()

    def calcular_total(self) -> Decimal:
        self.total_consolidado = sum((sp.calcular_subtotal() for sp in self.subpedidos), Decimal("0.00"))
        return self.total_consolidado

    def confirmar(self) -> None:
        """Valida que el pedido tenga al menos una línea y reserva el stock."""
        if not self.subpedidos or all(len(sp.lineas) == 0 for sp in self.subpedidos):
            raise ValueError("El pedido debe contener al menos un producto (Regla C3).")
        
        for sub in self.subpedidos:
            for linea in sub.lineas:
                if linea.producto:
                    linea.producto.reservar(linea.cantidad)
        self.estado = EstadoPedido.CONFIRMADO

    def dividir_por_puestos(self) -> List[PedidoPuesto]:
        """Devuelve la lista de subórdenes desagregadas por cada puesto del mercado."""
        return self.subpedidos

    def registrar_pago(self, pago: Pago) -> None:
        """Asocia el comprobante verificado y avanza el estado a PAGADO."""
        if not pago.es_aprobado():
            raise ValueError("No se puede registrar un pago no aprobado.")
        self.pago = pago
        self.estado = EstadoPedido.PAGADO

    def cancelar(self, motivo: str) -> None:
        """Cancela el pedido y libera el stock reservado en todos los puestos."""
        for sub in self.subpedidos:
            sub.rechazar(motivo)
            for linea in sub.lineas:
                if linea.producto:
                    linea.producto.liberar(linea.cantidad)
        self.estado = EstadoPedido.CANCELADO

    def verificar_completado(self) -> None:
        """Verifica si todos los subpedidos fueron entregados para cerrar la orden."""
        if self.subpedidos and all(sp.estado_puesto == EstadoPedidoPuesto.ENTREGADO for sp in self.subpedidos):
            self.estado = EstadoPedido.ENTREGADO


# ============================================================================
# Puertos (Interfaces Abstractas según Arquitectura Hexagonal)
# ============================================================================

class PasarelaPago(ABC):
    """Puerto de salida hacia servicios o validación de billeteras digitales."""
    @abstractmethod
    def validar_pago(self, monto: Decimal, codigo_operacion: str, comprobante_url: str) -> Pago:
        pass


class RepositorioPedidos(ABC):
    """Puerto de persistencia para la raíz de agregación Pedido."""
    @abstractmethod
    def buscar_por_id(self, id: UUID) -> Optional[Pedido]:
        pass

    @abstractmethod
    def guardar(self, p: Pedido) -> None:
        pass


class NotificadorWhatsApp(ABC):
    """Puerto de salida para el despacho de mensajes estructurados a comerciantes."""
    @abstractmethod
    def notificar_pedido_comerciante(self, telefono: str, subpedido: PedidoPuesto) -> None:
        pass


# ============================================================================
# Adaptadores (Implementaciones de Infraestructura)
# ============================================================================

class YapeAdapter(PasarelaPago):
    """Adaptador para procesamiento y validación de transferencias Yape."""
    def validar_pago(self, monto: Decimal, codigo_operacion: str, comprobante_url: str) -> Pago:
        # En el MVP se valida el formato del comprobante y código de 8 dígitos
        raise NotImplementedError("Integrar validación de comprobante Yape con OCR/revisión rápida.")


class PlinAdapter(PasarelaPago):
    """Adaptador para procesamiento y validación de transferencias Plin."""
    def validar_pago(self, monto: Decimal, codigo_operacion: str, comprobante_url: str) -> Pago:
        raise NotImplementedError("Integrar validación de transferencias Plin.")


# ============================================================================
# Servicio de Aplicación (Capa de Aplicación del Monolito Modular)
# ============================================================================

class ServicioPedidos:
    """Orquestador de casos de uso del módulo de Pedidos."""
    def __init__(
        self,
        repo: RepositorioPedidos,
        pasarela: PasarelaPago,
        notificador: NotificadorWhatsApp
    ) -> None:
        self.repo = repo
        self.pasarela = pasarela
        self.notificador = notificador

    def confirmar_y_registrar_pago(
        self,
        pedido_id: UUID,
        medio: MedioPago,
        codigo_operacion: str,
        comprobante_url: str
    ) -> Pedido:
        pedido = self.repo.buscar_por_id(pedido_id)
        if not pedido:
            raise ValueError(f"Pedido {pedido_id} no encontrado.")

        pedido.confirmar()
        total = pedido.calcular_total()

        pago = self.pasarela.validar_pago(total, codigo_operacion, comprobante_url)
        if pago.es_aprobado():
            pedido.registrar_pago(pago)
            subpedidos = pedido.dividir_por_puestos()
            self.repo.guardar(pedido)

            # Notificación asíncrona por cada comerciante
            for sub in subpedidos:
                if sub.puesto and sub.puesto.comerciante:
                    self.notificador.notificar_pedido_comerciante(
                        sub.puesto.comerciante.telefono_whatsapp,
                        sub
                    )
        else:
            pedido.cancelar("Pago no aprobado o comprobante inconsistente.")
            self.repo.guardar(pedido)

        return pedido

    def actualizar_estado_subpedido(
        self,
        pedido_id: UUID,
        subpedido_id: UUID,
        nuevo_estado: EstadoPedidoPuesto
    ) -> PedidoPuesto:
        pedido = self.repo.buscar_por_id(pedido_id)
        if not pedido:
            raise ValueError(f"Pedido {pedido_id} no encontrado.")

        sub = next((sp for sp in pedido.subpedidos if sp.id == subpedido_id), None)
        if not sub:
            raise ValueError(f"Subpedido {subpedido_id} no encontrado.")

        if nuevo_estado == EstadoPedidoPuesto.LISTO:
            sub.marcar_listo()
        elif nuevo_estado == EstadoPedidoPuesto.RECOGIDO:
            sub.marcar_recogido()
        elif nuevo_estado == EstadoPedidoPuesto.ENTREGADO:
            sub.estado_puesto = EstadoPedidoPuesto.ENTREGADO
            pedido.verificar_completado()
        elif nuevo_estado == EstadoPedidoPuesto.RECHAZADO:
            sub.rechazar("Rechazado por el comerciante.")

        self.repo.guardar(pedido)
        return sub

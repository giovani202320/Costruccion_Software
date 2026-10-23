"""
Servicio de Aplicación de Pedidos refactorizado hacia patrones GoF.
Aplica Factory + Strategy + Adapter + Decorator + State + Observer.
Desacopla el flujo transaccional de pagos, notificaciones y persistencia.
"""

from typing import List, Optional
from .estados import Pedido, Linea
from .externos import YapeSDK, PlinClient
from .pagos import FabricaPasarelas, YapeAdapter, PlinAdapter
from .eventos import PublicadorEventos, NotificadorWhatsApp, ActualizadorReportes


class ServicioPedidos:
    """Orquestador de casos de uso desacoplado mediante patrones de diseño GoF."""
    def __init__(
        self,
        yape: Optional[YapeSDK] = None,
        plin: Optional[PlinClient] = None,
        fabrica: Optional[FabricaPasarelas] = None,
        publicador: Optional[PublicadorEventos] = None,
    ) -> None:
        self.yape = yape or YapeSDK()
        self.plin = plin or PlinClient()
        self.eventos: List[str] = []

        # Factory para pasarelas de pago
        if fabrica is not None:
            self.fabrica = fabrica
        else:
            self.fabrica = FabricaPasarelas()
            self.fabrica.registrar("YAPE", lambda: YapeAdapter(self.yape))
            self.fabrica.registrar("PLIN", lambda: PlinAdapter(self.plin))

        # Observer para despacho de notificaciones y reportes
        if publicador is not None:
            self.publicador = publicador
        else:
            self.publicador = PublicadorEventos()
            # Suscriptores base conectados a la bandeja de eventos compartida
            self.publicador.suscribir("pedido_pagado", NotificadorWhatsApp(self.eventos))
            self.publicador.suscribir("pedido_pagado", ActualizadorReportes(self.eventos))

    def confirmar_y_pagar(self, pedido: Pedido, medio: str) -> str:
        """
        Flujo crítico refactorizado con patrones GoF:
        1. [Factory] Obtiene la estrategia correspondiente validándola previamente.
        2. [State] Confirma el pedido delegando en el estado actual.
        3. [Strategy + Adapter + Decorator] Realiza el cobro con reintentos automáticos.
        4. [State] Avanza el pedido a PAGADO o CANCELADO según el resultado.
        5. [Observer] Si fue aprobado, notifica a los suscriptores interesados (WhatsApp, Reportes).
        """
        pasarela = self.fabrica.crear(medio)
        pedido.confirmar()
        resultado = pasarela.cobrar(pedido.total(), pedido.celular)

        if resultado.aprobado:
            pedido.pagar(resultado.operacion)
            # Publicación de evento de dominio mediante Observer
            self.publicador.publicar("pedido_pagado", {
                "id": pedido.id,
                "celular": pedido.celular,
                "total": pedido.total()
            })
        else:
            pedido.cancelar()

        return pedido.estado

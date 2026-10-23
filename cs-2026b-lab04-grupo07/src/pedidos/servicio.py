"""
Servicio de Aplicación de Pedidos refactorizado hacia patrones GoF.
Aplica Factory + Strategy + Adapter + Decorator + State, reduciendo drásticamente
la complejidad ciclomática y eliminando acoplamientos a librerías externas.
"""

from typing import List, Optional
from .estados import Pedido, Linea
from .externos import YapeSDK, PlinClient
from .pagos import FabricaPasarelas, YapeAdapter, PlinAdapter


class ServicioPedidos:
    """Orquestador de casos de uso desacoplado mediante patrones de diseño."""
    def __init__(
        self,
        yape: Optional[YapeSDK] = None,
        plin: Optional[PlinClient] = None,
        fabrica: Optional[FabricaPasarelas] = None
    ) -> None:
        self.yape = yape or YapeSDK()
        self.plin = plin or PlinClient()
        self.eventos: List[str] = []

        if fabrica is not None:
            self.fabrica = fabrica
        else:
            self.fabrica = FabricaPasarelas()
            self.fabrica.registrar("YAPE", lambda: YapeAdapter(self.yape))
            self.fabrica.registrar("PLIN", lambda: PlinAdapter(self.plin))

    def confirmar_y_pagar(self, pedido: Pedido, medio: str) -> str:
        """
        Flujo crítico refactorizado:
        1. Valida el medio de pago usando la fábrica antes de modificar estado.
        2. Confirma el pedido delegando en el objeto State.
        3. Realiza el cobro con la estrategia obtenida (decorada con reintentos).
        4. Si es aprobado, avanza a PAGADO y emite eventos; caso contrario, cancela.
        """
        pasarela = self.fabrica.crear(medio)
        pedido.confirmar()
        resultado = pasarela.cobrar(pedido.total(), pedido.celular)

        if resultado.aprobado:
            pedido.pagar(resultado.operacion)
            self.eventos.append(f"whatsapp:{pedido.celular}:Pedido {pedido.id} pagado")
            self.eventos.append(f"reporte:{pedido.id}:{pedido.total():.2f}")
        else:
            pedido.cancelar()

        return pedido.estado

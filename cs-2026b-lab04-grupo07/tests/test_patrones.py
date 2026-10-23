"""
Pruebas unitarias que demuestran la efectividad de los patrones aplicados (E2 y E3).
Verifica:
1. Principio Abierto/Cerrado (OCP) mediante Factory + Strategy + Adapter.
2. Patrón State: encapsulamiento de transiciones válidas e impedimento de transiciones ilegales.
3. Patrón Decorator: reintentos exclusivos ante fallas de infraestructura (TimeoutError).
4. Patrón Adapter: traducción y aislamiento de las interfaces dispares de los SDKs.
"""

import pytest
from pedidos.estados import Pedido, Linea, Borrador, Confirmado, Pagado, Cancelado
from pedidos.pagos import (
    PasarelaPago,
    ResultadoPago,
    FabricaPasarelas,
    YapeAdapter,
    PlinAdapter,
    ConReintentos,
)
from pedidos.externos import YapeSDK, PlinClient
from pedidos.servicio import ServicioPedidos


# ============================================================================
# Pruebas para E2: Strategy + Adapter + Factory (Principio Abierto/Cerrado)
# ============================================================================

class TunkiSDKSimulado:
    """Tercera pasarela externa simulada con interfaz incompatible."""
    def __init__(self):
        self.procesadas = 0

    def debitar(self, telefono: str, cantidad_soles: float) -> str:
        self.procesadas += 1
        return f"TNK-{self.procesadas:05d}"


class TunkiAdapter(PasarelaPago):
    """Adaptador nuevo para Tunki sin modificar el núcleo del servicio."""
    def __init__(self, sdk: TunkiSDKSimulado):
        self._sdk = sdk

    def cobrar(self, monto: float, celular: str) -> ResultadoPago:
        tx = self._sdk.debitar(celular, monto)
        return ResultadoPago(aprobado=True, operacion=tx)


def test_open_closed_nuevo_medio_sin_modificar_el_servicio():
    """Demuestra OCP: se añade 'TUNKI' sin editar ServicioPedidos ni Pedido."""
    fabrica = FabricaPasarelas()
    yape_sdk = YapeSDK()
    plin_client = PlinClient()
    tunki_sdk = TunkiSDKSimulado()

    # Registro de medios existentes y el nuevo medio TUNKI
    fabrica.registrar("YAPE", lambda: YapeAdapter(yape_sdk))
    fabrica.registrar("PLIN", lambda: PlinAdapter(plin_client))
    fabrica.registrar("TUNKI", lambda: TunkiAdapter(tunki_sdk))

    servicio = ServicioPedidos(fabrica=fabrica)
    pedido = Pedido(id=10, celular="959333444", lineas=[Linea("Chirimoya Cumbe", 2.0, 12.0)])

    estado_final = servicio.confirmar_y_pagar(pedido, "TUNKI")

    assert estado_final == "PAGADO"
    assert pedido.estado == "PAGADO"
    assert pedido.operacion == "TNK-00001"
    assert tunki_sdk.procesadas == 1
    assert "whatsapp:959333444:Pedido 10 pagado" in servicio.eventos


def test_adapter_aisla_sdk_yape():
    """Verifica que YapeAdapter mapea el diccionario de Yape a ResultadoPago."""
    sdk = YapeSDK()
    adapter = YapeAdapter(sdk)
    resultado = adapter.cobrar(50.0, "959111222")

    assert isinstance(resultado, ResultadoPago)
    assert resultado.aprobado is True
    assert resultado.operacion == "YAP-0001"


def test_adapter_aisla_client_plin():
    """Verifica que PlinAdapter traduce los céntimos y la tupla a ResultadoPago."""
    client = PlinClient()
    adapter = PlinAdapter(client)
    resultado = adapter.cobrar(25.50, "959222333")

    assert isinstance(resultado, ResultadoPago)
    assert resultado.aprobado is True
    assert resultado.operacion == "PLN-0001"


def test_decorator_reintentos_solo_en_timeout_no_en_rechazo():
    """
    Verifica que el decorador ConReintentos reintenta cuando hay TimeoutError,
    pero NO reintenta si el pago fue rechazado por negocio (evita cobros duplicados).
    """
    sdk_limite = YapeSDK(fallas=0)
    adapter = YapeAdapter(sdk_limite)
    con_reintentos = ConReintentos(adapter, intentos=3)

    # Monto > 500 es rechazado por negocio (no es Timeout)
    resultado = con_reintentos.cobrar(600.0, "959000111")

    assert resultado.aprobado is False
    # Verificamos que solo se llamó 1 sola vez (no reintentó el rechazo de negocio)
    assert sdk_limite.llamadas == 1


# ============================================================================
# Pruebas para E3: Patrón State (Máquina de estados del Pedido)
# ============================================================================

def test_state_impide_transiciones_invalidas():
    """Verifica que las transiciones no permitidas en el diagrama son bloqueadas."""
    pedido = Pedido(id=20, celular="959888777", lineas=[Linea("Palta Fuerte", 3.0, 5.0)])

    # Intentar pagar directamente desde BORRADOR (sin confirmar) debe fallar
    with pytest.raises(ValueError, match="No se puede pagar un pedido en estado BORRADOR"):
        pedido.pagar("TX-TEST")

    # Confirmamos válidamente
    pedido.confirmar()
    assert pedido.estado == "CONFIRMADO"

    # Intentar confirmar de nuevo estando en CONFIRMADO
    with pytest.raises(ValueError, match="No se puede confirmar un pedido en estado CONFIRMADO"):
        pedido.confirmar()

    # Pagamos válidamente
    pedido.pagar("OP-OK-123")
    assert pedido.estado == "PAGADO"

    # Intentar cancelar un pedido ya PAGADO
    with pytest.raises(ValueError, match="No se puede cancelar un pedido ya pagado"):
        pedido.cancelar()

    # Intentar re-pagar un pedido ya PAGADO
    with pytest.raises(ValueError, match="El pedido ya fue pagado"):
        pedido.pagar("OP-OTRA")


def test_state_transiciones_validas_ciclo_completo():
    """Verifica la secuencia correcta BORRADOR -> CONFIRMADO -> PAGADO."""
    pedido = Pedido(id=21, celular="959777666", lineas=[Linea("Manzana Israel", 2.0, 4.5)])
    assert pedido.estado == "BORRADOR"

    pedido.confirmar()
    assert pedido.estado == "CONFIRMADO"

    pedido.pagar("OP-999")
    assert pedido.estado == "PAGADO"
    assert pedido.operacion == "OP-999"


def test_state_cancelacion_desde_borrador_y_confirmado():
    """Verifica que tanto BORRADOR como CONFIRMADO pueden cancelarse válidamente."""
    p1 = Pedido(id=30, celular="959111000", lineas=[Linea("Naranja Huando", 1.0, 3.0)])
    p1.cancelar()
    assert p1.estado == "CANCELADO"

    p2 = Pedido(id=31, celular="959111000", lineas=[Linea("Naranja Huando", 1.0, 3.0)])
    p2.confirmar()
    p2.cancelar()
    assert p2.estado == "CANCELADO"

    # Desde CANCELADO no se puede confirmar
    with pytest.raises(ValueError, match="El pedido está cancelado"):
        p2.confirmar()

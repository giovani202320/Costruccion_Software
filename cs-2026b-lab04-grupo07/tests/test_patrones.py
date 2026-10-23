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
    ConLogTransacciones,
)
from pedidos.externos import YapeSDK, PlinClient
from pedidos.servicio import ServicioPedidos
from pedidos.eventos import (
    PublicadorEventos,
    NotificadorWhatsApp,
    ActualizadorReportes,
    AuditoriaPedidos,
    Suscriptor,
)
from pedidos.ia import (
    ProveedorLLM,
    MockLLMAdapter,
    LocalAdapter,
    ConCache,
    Guardrail,
    SinPrecios,
    LongitudMaxima,
    SinAfirmacionesProhibidas,
    NormalizadorProductos,
)


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


# ============================================================================
# Pruebas para E4: Observer y Decorator (Notificaciones y Responsabilidades Transversales)
# ============================================================================

def test_decorator_composicion_reintentos_y_log():
    """
    Verifica la composición de decoradores: ConLogTransacciones envolviendo ConReintentos.
    Demuestra separación limpia entre tolerancia a fallos y auditoría.
    """
    sdk = YapeSDK(fallas=1)  # 1 timeout, luego éxito
    adapter = YapeAdapter(sdk)
    con_reintentos = ConReintentos(adapter, intentos=3)
    con_logging = ConLogTransacciones(con_reintentos)

    resultado = con_logging.cobrar(45.0, "959333222")

    assert resultado.aprobado is True
    assert resultado.operacion == "YAP-0002"
    assert len(con_logging.logs) == 2
    assert "INICIO: Cobro de S/ 45.00 a 959333222" in con_logging.logs[0]
    assert "FIN: Cobro APROBADO" in con_logging.logs[1]


def test_observer_notifica_a_multiples_suscriptores():
    """Verifica que PublicadorEventos propaga los eventos a todos los suscriptores."""
    publicador = PublicadorEventos()
    bandeja_ws = []
    bandeja_rep = []

    publicador.suscribir("pedido_pagado", NotificadorWhatsApp(bandeja_ws))
    publicador.suscribir("pedido_pagado", ActualizadorReportes(bandeja_rep))

    publicador.publicar("pedido_pagado", {"id": 101, "celular": "959123456", "total": 85.50})

    assert bandeja_ws == ["whatsapp:959123456:Pedido 101 pagado"]
    assert bandeja_rep == ["reporte:101:85.50"]


def test_observer_nuevo_suscriptor_sin_tocar_el_servicio():
    """
    Demuestra OCP en eventos: se añade un suscriptor de auditoría contable
    directamente al publicador sin alterar ni una sola línea de ServicioPedidos.
    """
    servicio = ServicioPedidos()
    auditor = AuditoriaPedidos()

    # Suscripción de nuevo interesado en tiempo de ejecución
    servicio.publicador.suscribir("pedido_pagado", auditor)

    pedido = Pedido(id=55, celular="959444555", lineas=[Linea("Queso Paria Especial", 2.0, 18.0)])
    estado = servicio.confirmar_y_pagar(pedido, "YAPE")

    assert estado == "PAGADO"
    # El nuevo suscriptor recibió los datos completos
    assert len(auditor.registros) == 1
    registro = auditor.registros[0]
    assert registro["evento"] == "pedido_pagado"
    assert registro["id"] == 55
    assert registro["celular"] == "959444555"
    assert registro["total"] == 36.0


def test_observer_desuscribir():
    """Verifica que un suscriptor puede darse de baja y deja de recibir eventos."""
    publicador = PublicadorEventos()
    bandeja = []
    observador = NotificadorWhatsApp(bandeja)

    publicador.suscribir("pedido_pagado", observador)
    publicador.publicar("pedido_pagado", {"id": 1, "celular": "959000111", "total": 10.0})
    assert len(bandeja) == 1

    # Desuscribir
    publicador.desuscribir("pedido_pagado", observador)
    publicador.publicar("pedido_pagado", {"id": 2, "celular": "959000222", "total": 20.0})
    # No debe haberse agregado ningún mensaje nuevo
    assert len(bandeja) == 1


# ============================================================================
# Pruebas para E5: Aislamiento de IA (Strategy, Adapter, Decorator, Chain)
# ============================================================================

def test_ia_mock_adapter_normaliza_correctamente():
    """Verifica que el adaptador simulado sustituye al LLM sin requerir API."""
    adapter = MockLLMAdapter()
    resultado = adapter.completar("Normaliza el producto: 'papa amarila'")
    assert resultado == "Papa Amarilla"
    assert adapter.llamadas == 1


def test_ia_decorator_con_cache_evita_llamadas_repetidas():
    """
    DECORATOR (Caché): Demuestra que ante el mismo prompt, el proveedor
    interno solo se invoca una única vez, evitando cobros y latencia redundante.
    """
    mock_adapter = MockLLMAdapter()
    con_cache = ConCache(mock_adapter)
    prompt = "Normaliza: 'queso paria artesanal'"

    # Primera llamada: consulta al adaptador
    res1 = con_cache.completar(prompt)
    assert res1 == "Queso Paria Artesanal"
    assert mock_adapter.llamadas == 1

    # Segunda llamada: servida inmediatamente desde la memoria caché
    res2 = con_cache.completar(prompt)
    assert res2 == "Queso Paria Artesanal"
    assert mock_adapter.llamadas == 1  # No se volvió a llamar al LLM!
    assert con_cache.llamadas_cache == 1


def test_ia_guardrail_sin_precios_bloquea_precio_inventado():
    """
    CHAIN OF RESPONSIBILITY (Guardrail): Bloquea si la IA inventa precios
    como 'S/ 3.50' o '$ 1.20', protegiendo la consistencia del catálogo.
    """
    guardrail = SinPrecios()

    # Salida limpia pasa sin problemas
    assert guardrail.validar("Rocoto Arequipeño") == "Rocoto Arequipeño"

    # Salida con precio en soles genera error
    with pytest.raises(ValueError, match="Guardrail: la IA incluyó un precio"):
        guardrail.validar("Papa Amarilla a solo S/ 4.50 el kilo")

    # Salida con símbolo $ también es bloqueada
    with pytest.raises(ValueError, match="Guardrail: la IA incluyó un precio"):
        guardrail.validar("Queso Paria por $ 5.00")


def test_ia_guardrail_longitud_maxima_bloquea_alucinaciones():
    """
    CHAIN OF RESPONSIBILITY (Guardrail): Bloquea textos excesivos
    que desbordarían las pantallas de celulares de gama baja en el mercado.
    """
    guardrail = LongitudMaxima(max_caracteres=30)

    # Texto dentro del límite (<= 30 caracteres)
    assert guardrail.validar("Chirimoya Cumbe") == "Chirimoya Cumbe"

    # Texto que excede los 30 caracteres
    texto_largo = "Deliciosa chirimoya cumbe fresca del valle de majes cosechada hoy"
    with pytest.raises(ValueError, match="Guardrail: la salida de la IA excedió el límite"):
        guardrail.validar(texto_largo)


def test_ia_guardrail_sin_afirmaciones_prohibidas():
    """Bloquea reclamos médicos o afirmaciones no autorizadas por regulación."""
    guardrail = SinAfirmacionesProhibidas()

    with pytest.raises(ValueError, match="Guardrail: afirmación no permitida detectada 'cura'"):
        guardrail.validar("Zumo de Naranja que cura cualquier resfrío")


def test_ia_normalizador_productos_flujo_integrado_exitoso():
    """
    Verifica el flujo integrado de NormalizadorProductos con Strategy + Cache + Cadena completa.
    """
    mock = MockLLMAdapter()
    cache = ConCache(mock)
    normalizador = NormalizadorProductos(proveedor=cache)

    resultado = normalizador.normalizar("papa amarila")
    assert resultado == "Papa Amarilla"
    assert mock.llamadas == 1

    # Segunda llamada normalizando el mismo término: protegida por caché
    resultado2 = normalizador.normalizar("papa amarila")
    assert resultado2 == "Papa Amarilla"
    assert mock.llamadas == 1


def test_ia_normalizador_bloquea_cuando_llm_alucina_precio():
    """Verifica que el orquestador frena respuestas alucinadas con precios."""
    # Simulamos que el LLM responde con un precio inventado
    mock_alucinador = MockLLMAdapter(respuesta_defecto="Papa Huayro S/ 3.80 kg")
    normalizador = NormalizadorProductos(proveedor=mock_alucinador)

    with pytest.raises(ValueError, match="Guardrail: la IA incluyó un precio"):
        normalizador.normalizar("papa huayro")

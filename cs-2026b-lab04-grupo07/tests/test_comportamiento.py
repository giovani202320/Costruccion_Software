"""
Pruebas de caracterización para el flujo 'confirmar y pagar un pedido'.
Ejecuta la misma suite sobre la versión 'antes' (código ingenuo) y 'despues' (con patrones)
mediante un fixture parametrizado, garantizando que el comportamiento observable se conserve.
"""

import importlib
import pytest
from pedidos.externos import YapeSDK, PlinClient


@pytest.fixture(params=["pedidos.antes.servicio", "pedidos.servicio"])
def m(request):
    """Importa dinámicamente el módulo antes o después según el parámetro."""
    return importlib.import_module(request.param)


def pedido(m, precio: float = 3.5, cantidad: float = 20.0):
    """Fixture auxiliar para construir un pedido de prueba en estado BORRADOR."""
    return m.Pedido(
        id=1,
        celular="959000111",
        lineas=[m.Linea(producto="Queso Paria San Camilo", cantidad=cantidad, precio=precio)]
    )


def test_pago_yape_aprobado_publica_eventos(m):
    s = m.ServicioPedidos()
    p = pedido(m, precio=3.5, cantidad=20.0)
    estado = s.confirmar_y_pagar(p, "YAPE")

    assert estado == "PAGADO"
    assert p.estado == "PAGADO"
    assert p.operacion is not None
    assert s.eventos == ["whatsapp:959000111:Pedido 1 pagado", "reporte:1:70.00"]


def test_pago_plin_aprobado_publica_eventos(m):
    s = m.ServicioPedidos()
    p = pedido(m, precio=2.5, cantidad=10.0)
    estado = s.confirmar_y_pagar(p, "PLIN")

    assert estado == "PAGADO"
    assert p.estado == "PAGADO"
    assert p.operacion is not None
    assert s.eventos == ["whatsapp:959000111:Pedido 1 pagado", "reporte:1:25.00"]


def test_pago_yape_monto_sobre_limite_se_cancela_sin_eventos(m):
    s = m.ServicioPedidos()
    p = pedido(m, precio=30.0, cantidad=20.0)  # Total = 600 > límite de 500
    estado = s.confirmar_y_pagar(p, "YAPE")

    assert estado == "CANCELADO"
    assert p.estado == "CANCELADO"
    assert s.eventos == []


def test_pago_plin_monto_sobre_limite_se_cancela_sin_eventos(m):
    s = m.ServicioPedidos()
    p = pedido(m, precio=60.0, cantidad=10.0)  # Total = 600 > límite de 500 (50000 céntimos)
    estado = s.confirmar_y_pagar(p, "PLIN")

    assert estado == "CANCELADO"
    assert p.estado == "CANCELADO"
    assert s.eventos == []


def test_reintenta_tras_dos_timeouts(m):
    yape = YapeSDK(fallas=2)
    s = m.ServicioPedidos(yape=yape)
    p = pedido(m, precio=3.5, cantidad=20.0)

    assert s.confirmar_y_pagar(p, "YAPE") == "PAGADO"
    assert yape.llamadas == 3
    assert p.estado == "PAGADO"


def test_reintenta_plin_tras_dos_timeouts(m):
    plin = PlinClient(fallas=2)
    s = m.ServicioPedidos(plin=plin)
    p = pedido(m, precio=5.0, cantidad=10.0)

    assert s.confirmar_y_pagar(p, "PLIN") == "PAGADO"
    assert plin.llamadas == 3
    assert p.estado == "PAGADO"


def test_tres_timeouts_cancela_pedido(m):
    yape = YapeSDK(fallas=3)
    s = m.ServicioPedidos(yape=yape)
    p = pedido(m, precio=3.5, cantidad=20.0)

    assert s.confirmar_y_pagar(p, "YAPE") == "CANCELADO"
    assert yape.llamadas == 3
    assert p.estado == "CANCELADO"
    assert s.eventos == []


def test_pedido_sin_lineas_lanza_error(m):
    s = m.ServicioPedidos()
    p = m.Pedido(id=2, celular="959000111", lineas=[])

    with pytest.raises(ValueError, match="El pedido no tiene líneas"):
        s.confirmar_y_pagar(p, "YAPE")


def test_transicion_invalida_desde_cancelado(m):
    s = m.ServicioPedidos()
    p = pedido(m)
    p.estado = "CANCELADO"

    with pytest.raises(ValueError, match="cancelado"):
        s.confirmar_y_pagar(p, "YAPE")


def test_transicion_invalida_desde_pagado(m):
    s = m.ServicioPedidos()
    p = pedido(m)
    p.estado = "PAGADO"

    with pytest.raises(ValueError, match="pagado"):
        s.confirmar_y_pagar(p, "YAPE")


def test_medio_no_soportado_lanza_error(m):
    s = m.ServicioPedidos()
    p = pedido(m)

    with pytest.raises(ValueError, match="Medio de pago no soportado"):
        s.confirmar_y_pagar(p, "BITCOIN")


def test_medio_no_soportado_no_altera_el_estado(m, request):
    """
    Error documentado en la versión 'antes': si el medio no existe, el pedido quedaba
    en 'CONFIRMADO' antes de fallar. En 'despues', la Factory valida antes de mutar el estado.
    """
    if "antes" in request.node.name:
        request.node.add_marker(pytest.mark.xfail(
            reason="Bug documentado en versión 'antes': muta estado a CONFIRMADO antes de validar medio"
        ))

    s = m.ServicioPedidos()
    p = pedido(m)

    with pytest.raises(ValueError):
        s.confirmar_y_pagar(p, "BITCOIN")

    assert p.estado == "BORRADOR"


def test_calculo_total_pedido_multiples_lineas(m):
    p = m.Pedido(
        id=3,
        celular="959111222",
        lineas=[
            m.Linea(producto="Papa Amarilla", cantidad=4.0, precio=3.50),
            m.Linea(producto="Rocoto Arequipeño", cantidad=2.0, precio=5.00),
            m.Linea(producto="Queso Paria", cantidad=1.0, precio=18.00)
        ]
    )
    assert p.total() == 42.00

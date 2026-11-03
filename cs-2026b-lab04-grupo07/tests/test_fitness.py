"""
tests/test_fitness.py
Fitness functions ejecutadas en CI para proteger la arquitectura de San Camilo en Línea 2.0.
Verifica presupuestos de latencia (QA-05), cero pedidos perdidos (QA-06),
aislamiento multitenancy (QA-03) y modificabilidad de reglas (QA-01).
"""

import pytest
from fitness.rendimiento import simular, con_cache, bd_con_indice
from fitness.disponibilidad import simular_pagos
from fitness.multitenencia_reglas import verificar_aislamiento_multitenant, medir_tiempo_aplicacion_regla

# Presupuestos de arquitectura
PRESUPUESTO_P95_MS = 1800.0  # QA-05: p95 <= 1.8 s a carga pico de 24 req/s


def test_ff01_rendimiento_catalogo_hora_punta():
    """FF-03: Verifica que a carga pico (24 req/s), el p95 no supere el presupuesto de 1800 ms."""
    resultado = simular(lam=24.0, workers=4, servicio=con_cache(bd_con_indice, hit_rate=0.85))
    p95 = resultado["p95"]
    assert p95 <= PRESUPUESTO_P95_MS, f"Presupuesto de latencia violado: p95={p95:.1f} ms > {PRESUPUESTO_P95_MS} ms"


def test_ff02_aislamiento_multitenancy_cero_fugas():
    """FF-04: Verifica QA-03: 0 registros ajenos expuestos entre mercados bajo 1,000 intentos cruzados."""
    res = verificar_aislamiento_multitenant(intentos=1000)
    assert res["fugas_con_rls"] == 0, f"Fuga de aislamiento detectada: {res['fugas_con_rls']} registros expuestos"
    assert res["aislamiento_efectivo_pct"] == 100.0


def test_ff03_cero_pedidos_perdidos_caida_proveedor():
    """FF-05: Verifica QA-06: 0 pedidos perdidos ante una caída de 20 min del proveedor de pagos."""
    res = simular_pagos("breaker")
    assert res["perdidos"] == 0, f"Se perdieron {res['perdidos']} pedidos durante la caída del proveedor"
    assert res["tasa_exito_pct"] == 100.0


def test_ff04_breaker_protege_al_proveedor_caido():
    """FF-06: Verifica que el Circuit Breaker reduzca drásticamente las llamadas al proveedor caído (> 5x menos)."""
    res_breaker = simular_pagos("breaker")
    res_reintentos = simular_pagos("reintentos")
    assert res_breaker["llamadas_en_caida"] < (res_reintentos["llamadas_en_caida"] / 5), (
        f"Circuit Breaker no protegió adecuadamente: {res_breaker['llamadas_en_caida']} vs {res_reintentos['llamadas_en_caida']}"
    )


def test_ff05_modificabilidad_tiempo_reglas_en_caliente():
    """FF-07: Verifica QA-01: actualización de regla de negocio en memoria en < 5 minutos y 0 downtime."""
    res = medir_tiempo_aplicacion_regla()
    assert res["cumple_qa01"] is True
    assert res["tiempo_aplicacion_ms"] < 1000.0, f"Actualización tardó demasiado: {res['tiempo_aplicacion_ms']} ms"

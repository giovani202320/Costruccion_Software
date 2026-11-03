"""
fitness/multitenencia_reglas.py
Pruebas cuantitativas y simulación de aislamiento multitenancy (QA-03)
y tiempo de aplicación de reglas dinámicas por mercado (QA-01) para San Camilo en Línea 2.0.
"""

import time
from typing import Dict, List, Optional


class ReglaMercado:
    def __init__(self, mercado_id: str, recargo_despacho: float, comision_pct: float, horario_cierre: str):
        self.mercado_id = mercado_id
        self.recargo_despacho = recargo_despacho
        self.comision_pct = comision_pct
        self.horario_cierre = horario_cierre


class GestorReglasMercado:
    """Motor de configuración de reglas dinámicas en memoria/BD sin redeploy."""
    def __init__(self):
        self._reglas: Dict[str, ReglaMercado] = {
            "san_camilo": ReglaMercado("san_camilo", recargo_despacho=3.0, comision_pct=2.0, horario_cierre="18:00"),
            "altiplano": ReglaMercado("altiplano", recargo_despacho=4.5, comision_pct=3.0, horario_cierre="19:30"),
            "rio_seco": ReglaMercado("rio_seco", recargo_despacho=5.0, comision_pct=2.5, horario_cierre="17:00"),
        }

    def obtener_regla(self, mercado_id: str) -> ReglaMercado:
        return self._reglas.get(mercado_id, self._reglas["san_camilo"])

    def actualizar_regla(self, mercado_id: str, recargo: float, comision: float, cierre: str):
        """Aplica la nueva regla en caliente en milisegundos."""
        self._reglas[mercado_id] = ReglaMercado(mercado_id, recargo, comision, cierre)


class RepositorioPedidosMultiTenant:
    """Simula persistencia con Row-Level Security (RLS) habilitada."""
    def __init__(self):
        self.pedidos = [
            {"id": 1, "mercado_id": "san_camilo", "comerciante_id": "c1", "total": 45.0},
            {"id": 2, "mercado_id": "san_camilo", "comerciante_id": "c2", "total": 80.0},
            {"id": 3, "mercado_id": "altiplano", "comerciante_id": "c3", "total": 35.0},
            {"id": 4, "mercado_id": "rio_seco", "comerciante_id": "c4", "total": 92.0},
            {"id": 5, "mercado_id": "rio_seco", "comerciante_id": "c5", "total": 110.0},
        ]

    def consultar_sin_rls(self, solicitante_mercado_id: str) -> List[dict]:
        """Violación: consulta global sin filtro de tenant."""
        return list(self.pedidos)

    def consultar_con_rls(self, solicitante_mercado_id: str) -> List[dict]:
        """Aislamiento RLS: solo retorna filas del mercado del solicitante."""
        return [p for p in self.pedidos if p["mercado_id"] == solicitante_mercado_id]


def verificar_aislamiento_multitenant(intentos: int = 1000) -> dict:
    """Evalúa intentos cruzados de acceso entre mercados para verificar QA-03."""
    repo = RepositorioPedidosMultiTenant()
    mercados = ["altiplano", "rio_seco"]
    
    fugas_sin_rls = 0
    fugas_con_rls = 0

    for i in range(intentos):
        solicitante = mercados[i % len(mercados)]
        
        # Consulta sin RLS
        res_sin = repo.consultar_sin_rls(solicitante)
        if any(p["mercado_id"] != solicitante for p in res_sin):
            fugas_sin_rls += 1

        # Consulta con RLS
        res_con = repo.consultar_con_rls(solicitante)
        if any(p["mercado_id"] != solicitante for p in res_con):
            fugas_con_rls += 1

    return {
        "intentos": intentos,
        "fugas_sin_rls": fugas_sin_rls,
        "fugas_con_rls": fugas_con_rls,
        "aislamiento_efectivo_pct": ((intentos - fugas_con_rls) / intentos) * 100.0
    }


def medir_tiempo_aplicacion_regla() -> dict:
    """Mide tiempo de propagación de cambio de regla dinámica en memoria (QA-01)."""
    gestor = GestorReglasMercado()
    inicio = time.perf_counter()
    gestor.actualizar_regla("altiplano", recargo=6.0, comision=3.5, cierre="20:00")
    regla = gestor.obtener_regla("altiplano")
    duracion_ms = (time.perf_counter() - inicio) * 1000.0

    return {
        "tiempo_aplicacion_ms": duracion_ms,
        "recargo_actualizado": regla.recargo_despacho,
        "cumple_qa01": duracion_ms < (5 * 60 * 1000.0)  # Menos de 5 minutos
    }


if __name__ == "__main__":
    aisla = verificar_aislamiento_multitenant()
    reglas = medir_tiempo_aplicacion_regla()
    print("--- Evaluación Multitenencia y Modificabilidad ---")
    print(f"Aislamiento con RLS: {aisla['fugas_con_rls']} fugas de {aisla['intentos']} intentos ({aisla['aislamiento_efectivo_pct']:.1f}% aislamiento)")
    print(f"Tiempo de aplicación de regla dinámica: {reglas['tiempo_aplicacion_ms']:.3f} ms (Objetivo <= 5 min)")

"""
Servicios y SDKs externos simulados para el Mercado San Camilo.
Simula pasarelas con interfaces incompatibles, fallas de red y respuestas dispares.
"""

from typing import Dict, Any, Tuple


class YapeSDK:
    """
    SDK simulado de Yape (BCP).
    Interfaz: cobrar en soles (float), responde con diccionario {'ok': bool, 'operacion': str}.
    """
    def __init__(self, fallas: int = 0) -> None:
        self.fallas = fallas
        self.llamadas: int = 0

    def realizar_cobro(self, celular: str, monto: float) -> Dict[str, Any]:
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise TimeoutError("Timeout de conexión con el servicio de Yape")
        if monto > 500.0:
            return {"ok": False, "operacion": None, "error": "Monto excede el límite diario permitido (S/ 500)"}
        return {"ok": True, "operacion": f"YAP-{self.llamadas:04d}"}


class PlinClient:
    """
    Cliente simulado de Plin (Interbank/BBVA/Scotiabank).
    Interfaz: cobrar en céntimos (int), orden invertido (monto, celular), responde tupla (HTTP_CODE, tx_id).
    """
    def __init__(self, fallas: int = 0) -> None:
        self.fallas = fallas
        self.llamadas: int = 0

    def charge(self, amount_cents: int, phone: str) -> Tuple[int, str]:
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise TimeoutError("Timeout de conexión con la pasarela Plin")
        if amount_cents > 50000:  # 50000 céntimos = S/ 500.00
            return 400, "EXCEEDS_DAILY_LIMIT"
        return 200, f"PLN-{self.llamadas:04d}"

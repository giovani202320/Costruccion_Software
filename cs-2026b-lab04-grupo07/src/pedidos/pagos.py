"""
Módulo de procesamiento de pagos con patrones GoF (Strategy + Adapter + Decorator + Factory).
Permite integrar y registrar pasarelas heterogéneas sin alterar el servicio de aplicación.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, Optional
from .externos import YapeSDK, PlinClient


@dataclass(frozen=True)
class ResultadoPago:
    """Objeto valor inmutable que uniformiza la respuesta de cobro."""
    aprobado: bool
    operacion: Optional[str] = None


# ============================================================================
# STRATEGY: Interfaz común (puerto) para todas las estrategias de pago
# ============================================================================

class PasarelaPago(ABC):
    """Puerto abstracto para interactuar con cualquier medio de pago."""
    @abstractmethod
    def cobrar(self, monto: float, celular: str) -> ResultadoPago:
        """Efectúa el cobro devolviendo un ResultadoPago uniforme."""
        ...


# ============================================================================
# ADAPTER: Traduce las interfaces dispares de los SDKs al puerto común
# ============================================================================

class YapeAdapter(PasarelaPago):
    """Adapta el SDK de Yape (soles en float, retorno de dict)."""
    def __init__(self, sdk: Optional[YapeSDK] = None) -> None:
        self._sdk = sdk or YapeSDK()

    def cobrar(self, monto: float, celular: str) -> ResultadoPago:
        r = self._sdk.realizar_cobro(celular, monto)
        return ResultadoPago(aprobado=r["ok"], operacion=r.get("operacion"))


class PlinAdapter(PasarelaPago):
    """Adapta el cliente de Plin (céntimos en int, tupla http, orden inverso)."""
    def __init__(self, cliente: Optional[PlinClient] = None) -> None:
        self._cliente = cliente or PlinClient()

    def cobrar(self, monto: float, celular: str) -> ResultadoPago:
        # Convierte soles a céntimos redondeados para evitar pérdida de precisión
        monto_centimos = int(round(monto * 100))
        codigo, tx = self._cliente.charge(monto_centimos, celular)
        return ResultadoPago(aprobado=(codigo == 200), operacion=tx)


# ============================================================================
# DECORATOR: Manejo transversal de reintentos ante fallas de red transitorias
# ============================================================================

class ConReintentos(PasarelaPago):
    """
    Decorador que reintenta la operación ante TimeoutError.
    Evita reintentar pagos rechazados por reglas de negocio para no duplicar cargos.
    """
    def __init__(self, interna: PasarelaPago, intentos: int = 3) -> None:
        self._interna = interna
        self._intentos = intentos

    def cobrar(self, monto: float, celular: str) -> ResultadoPago:
        for _ in range(self._intentos):
            try:
                return self._interna.cobrar(monto, celular)
            except TimeoutError:
                continue
        return ResultadoPago(aprobado=False)


class ConLogTransacciones(PasarelaPago):
    """
    DECORATOR: Agrega registro y auditoría de llamadas sin modificar la pasarela subyacente.
    Demuestra composición de decoradores (ConLogTransacciones envolviendo ConReintentos o viceversa).
    """
    def __init__(self, interna: PasarelaPago) -> None:
        self._interna = interna
        self.logs: List[str] = []

    def cobrar(self, monto: float, celular: str) -> ResultadoPago:
        self.logs.append(f"INICIO: Cobro de S/ {monto:.2f} a {celular}")
        resultado = self._interna.cobrar(monto, celular)
        self.logs.append(f"FIN: Cobro {'APROBADO' if resultado.aprobado else 'RECHAZADO'}")
        return resultado


# ============================================================================
# FACTORY: Registro dinámico de pasarelas (abierto a extensión, sin Singleton)
# ============================================================================

class FabricaPasarelas:
    """Fábrica de estrategias de pago basada en registro extensible (OCP)."""
    def __init__(self) -> None:
        self._creadores: Dict[str, Callable[[], PasarelaPago]] = {}

    def registrar(self, medio: str, creador: Callable[[], PasarelaPago]) -> None:
        """Registra un nuevo medio de pago con su función creadora."""
        self._creadores[medio.upper()] = creador

    def crear(self, medio: str) -> PasarelaPago:
        """Instancia la estrategia decorada con reintentos para el medio solicitado."""
        medio_norm = medio.upper()
        if medio_norm not in self._creadores:
            raise ValueError(f"Medio de pago no soportado: {medio}")
        return ConReintentos(self._creadores[medio_norm]())

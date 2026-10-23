"""
Módulo de Integración y Aislamiento de Inteligencia Artificial (E5).
Implementa Strategy, Adapter, Decorator y Chain of Responsibility para gobernar
componentes no deterministas de IA según Huyen (2025) e Iusztin & Labonne (2024).

Caso San Camilo en Línea: Normalización y estandarización de nombres de productos
del catálogo comercial (ej. corregir faltas de ortografía o alias de puesteros).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


# ============================================================================
# 1. STRATEGY: Puerto abstracto para interactuar con cualquier LLM
# ============================================================================

class ProveedorLLM(ABC):
    """
    STRATEGY: Define la interfaz común para proveedores de modelos de lenguaje.
    Permite desacoplar el dominio de la API o implementación técnica del modelo.
    """
    @abstractmethod
    def completar(self, prompt: str) -> str:
        """Envía un prompt al modelo y devuelve el texto de completitud generado."""
        ...


# ============================================================================
# 2. ADAPTER: Proveedor simulado en memoria (sin claves de API ni llamadas de red)
# ============================================================================

class MockLLMAdapter(ProveedorLLM):
    """
    ADAPTER / DOBLE DE PRUEBA: Simula el comportamiento de un LLM local o remoto.
    Permite probar el sistema de forma determinista, reproducible y a costo $0.
    """
    def __init__(
        self,
        respuestas: Optional[Dict[str, str]] = None,
        respuesta_defecto: Optional[str] = None
    ) -> None:
        self.respuestas: Dict[str, str] = respuestas or {
            "papa amarila": "Papa Amarilla",
            "queso paria artesanal": "Queso Paria Artesanal",
            "rocoto arequipeño": "Rocoto Arequipeño",
            "chirimoya cumbe": "Chirimoya Cumbe",
            "platano seda": "Plátano de Seda",
        }
        self.respuesta_defecto: Optional[str] = respuesta_defecto
        self.llamadas: int = 0
        self.historial_prompts: List[str] = []

    def completar(self, prompt: str) -> str:
        self.llamadas += 1
        self.historial_prompts.append(prompt)

        # Si hay una respuesta por defecto configurada para pruebas de fallo/caso fijo
        if self.respuesta_defecto is not None:
            return self.respuesta_defecto

        # Búsqueda semántica básica por coincidencia de subcadena en las respuestas
        prompt_lower = prompt.lower()
        for clave, valor in self.respuestas.items():
            if clave in prompt_lower:
                return valor

        # Si no coincide exactamente, normaliza la primera palabra o formato título
        return "Producto Normalizado San Camilo"


# Alias para compatibilidad con nomenclaturas del laboratorio
LocalAdapter = MockLLMAdapter


# ============================================================================
# 3. DECORATOR: Caché en memoria para evitar latencia y costo redundante
# ============================================================================

class ConCache(ProveedorLLM):
    """
    DECORATOR: Envuelve a cualquier ProveedorLLM para almacenar en caché las
    respuestas a prompts idénticos, reduciendo drásticamente costos y latencias.
    """
    def __init__(self, interno: ProveedorLLM) -> None:
        self._interno = interno
        self._cache: Dict[str, str] = {}

    @property
    def llamadas_cache(self) -> int:
        """Retorna la cantidad de elementos almacenados en la caché."""
        return len(self._cache)

    def completar(self, prompt: str) -> str:
        if prompt not in self._cache:
            self._cache[prompt] = self._interno.completar(prompt)
        return self._cache[prompt]


# ============================================================================
# 4. CHAIN OF RESPONSIBILITY: Guardrails para verificación de salida no confiable
# ============================================================================

class Guardrail(ABC):
    """
    CHAIN OF RESPONSIBILITY (Handler Base):
    Verifica que la salida de la IA cumpla con los estándares de seguridad,
    confiabilidad y formato antes de ser expuesta a los usuarios o a la base de datos.
    """
    def __init__(self, siguiente: Optional[Guardrail] = None) -> None:
        self._siguiente: Optional[Guardrail] = siguiente

    def enlazar(self, siguiente: Guardrail) -> Guardrail:
        """Permite construir fluidamente la cadena de validaciones."""
        self._siguiente = siguiente
        return siguiente

    def validar(self, texto: str) -> str:
        """Ejecuta la validación actual y delega al siguiente eslabón si existe."""
        texto_procesado = self._aplicar(texto)
        if self._siguiente is not None:
            return self._siguiente.validar(texto_procesado)
        return texto_procesado

    @abstractmethod
    def _aplicar(self, texto: str) -> str:
        """Aplica la regla concreta del guardrail sobre el texto."""
        ...


class SinPrecios(Guardrail):
    """
    Guardrail Concreto:
    Impide que el modelo invente o adjunte precios (ej: 'S/ 4.50' o '$ 2.00')
    en el nombre del producto, lo cual causaría inconsistencias con la base de datos.
    """
    def _aplicar(self, texto: str) -> str:
        if "S/" in texto or "s/." in texto.lower() or "$" in texto:
            raise ValueError("Guardrail: la IA incluyó un precio en el nombre normalizado")
        return texto


class LongitudMaxima(Guardrail):
    """
    Guardrail Concreto:
    Asegura que el nombre devuelto no exceda una longitud máxima (evita textos extensos
    o alucinaciones verborrágicas del LLM que romperían el layout en celulares).
    """
    def __init__(self, max_caracteres: int = 50, siguiente: Optional[Guardrail] = None) -> None:
        super().__init__(siguiente)
        self.max_caracteres = max_caracteres

    def _aplicar(self, texto: str) -> str:
        if len(texto) > self.max_caracteres:
            raise ValueError(
                f"Guardrail: la salida de la IA excedió el límite de longitud ({len(texto)} > {self.max_caracteres})"
            )
        return texto


class SinAfirmacionesProhibidas(Guardrail):
    """
    Guardrail Concreto:
    Bloquea reclamos médicos, curativos o afirmaciones no verificadas
    ('cura la diabetes', 'garantizado', 'orgánico certificado').
    """
    PROHIBIDAS = ["orgánico certificado", "cura", "garantizado", "milagroso"]

    def _aplicar(self, texto: str) -> str:
        texto_lower = texto.lower()
        for palabra in self.PROHIBIDAS:
            if palabra in texto_lower:
                raise ValueError(f"Guardrail: afirmación no permitida detectada '{palabra}'")
        return texto


# ============================================================================
# 5. SERVICIO INTEGRADOR: Normalizador de Productos
# ============================================================================

class NormalizadorProductos:
    """
    Coordinador de alto nivel del caso San Camilo en Línea.
    Aísla la interacción con el LLM detrás de la estrategia, caché y guardrails.
    """
    def __init__(self, proveedor: ProveedorLLM, guardrails: Optional[Guardrail] = None) -> None:
        self.proveedor = proveedor
        self.guardrails = guardrails or self._cadena_por_defecto()

    @staticmethod
    def _cadena_por_defecto() -> Guardrail:
        """Construye la cadena estándar: SinPrecios -> SinAfirmacionesProhibidas -> LongitudMaxima."""
        c = SinPrecios()
        c.enlazar(SinAfirmacionesProhibidas()).enlazar(LongitudMaxima(max_caracteres=50))
        return c

    def normalizar(self, nombre_crudo: str) -> str:
        """
        Normaliza el nombre comercial del producto ingresado por el puestero.
        Aplica guardrails antes de aceptar el resultado.
        """
        prompt = f"Normaliza el siguiente producto del Mercado San Camilo: '{nombre_crudo}'"
        salida_modelo = self.proveedor.completar(prompt)
        return self.guardrails.validar(salida_modelo.strip())

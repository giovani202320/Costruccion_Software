"""
Generador versionado de normalización de productos detrás de ProveedorLLM (Lab 09 - E6, Caso 7).

Conecta el prompt versionado de Tarea B (`prompts/normalizacion/`) con el puerto `ProveedorLLM`
y la cadena de `Guardrail` definida en el Laboratorio 07 (`pedidos.ia`).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Optional

from jsonschema import ValidationError, validate

from pedidos.generador_criterios import RAIZ_PROMPTS_DEFECTO, SalidaInvalida, sanitizar_entrada
from pedidos.ia import (
    Guardrail,
    LongitudMaxima,
    ProveedorLLM,
    SinAfirmacionesProhibidas,
    SinPrecios,
)


class GeneradorNormalizacion:
    """Normaliza nombres escritos por comerciantes validando contrato JSON Schema y guardrails."""

    def __init__(
        self,
        proveedor: ProveedorLLM,
        version: str = "v2",
        guardrails: Optional[Guardrail] = None,
        raiz_prompts: Optional[pathlib.Path] = None,
    ) -> None:
        self._proveedor = proveedor
        self.version = version
        self._guardrails = guardrails or self._cadena_por_defecto()
        base = (raiz_prompts or RAIZ_PROMPTS_DEFECTO) / "normalizacion"
        self._plantilla = (base / f"{version}.txt").read_text(encoding="utf-8")
        self._esquema = json.loads((base / "esquema.json").read_text(encoding="utf-8"))

    @staticmethod
    def _cadena_por_defecto() -> Guardrail:
        cadena = SinPrecios()
        cadena.enlazar(SinAfirmacionesProhibidas()).enlazar(LongitudMaxima(max_caracteres=50))
        return cadena

    def normalizar(self, entrada_id: str, texto_crudo: str) -> dict[str, Any]:
        """Sanitiza la entrada, invoca al LLM y valida esquema cerrado + guardrails de dominio."""
        texto_seguro = sanitizar_entrada(texto_crudo)
        prompt = (
            self._plantilla.replace("{{id}}", entrada_id)
            .replace("{{texto}}", texto_seguro)
        )
        salida_cruda = self._proveedor.completar(prompt)
        try:
            resultado: dict[str, Any] = json.loads(salida_cruda)
            validate(resultado, self._esquema)
            self._guardrails.validar(resultado["producto_catalogo"])
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
            raise SalidaInvalida(f"{self.version}/{entrada_id}: {exc}") from exc
        return resultado

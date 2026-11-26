"""
Generador versionado de criterios de aceptación Gherkin detrás de ProveedorLLM (Lab 09 - E6).

Aplica defensa en capas sobre el puerto Strategy `ProveedorLLM` del Laboratorio 07:
- Capa 1: sanitización de delimitadores XML (< y >) antes de interpolar datos del usuario.
- Capa 3: validación determinista de la salida JSON contra `prompts/criterios/esquema.json`.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Optional

from jsonschema import ValidationError, validate

from pedidos.ia import ProveedorLLM

RAIZ_PROMPTS_DEFECTO = pathlib.Path(__file__).resolve().parents[2] / "prompts"


class SalidaInvalida(Exception):
    """La respuesta del LLM no cumple el contrato JSON Schema y debe descartarse."""


def sanitizar_entrada(texto: str) -> str:
    """Escapa delimitadores XML en entradas no confiables para prevenir delimiter escape."""
    return texto.replace("<", "&lt;").replace(">", "&gt;")


class GeneradorCriterios:
    """Carga un prompt versionado de Tarea A y valida la respuesta del LLM con JSON Schema."""

    def __init__(
        self,
        proveedor: ProveedorLLM,
        version: str = "v3",
        raiz_prompts: Optional[pathlib.Path] = None,
    ) -> None:
        self._proveedor = proveedor
        self.version = version
        base = (raiz_prompts or RAIZ_PROMPTS_DEFECTO) / "criterios"
        self._plantilla = (base / f"{version}.txt").read_text(encoding="utf-8")
        self._esquema = json.loads((base / "esquema.json").read_text(encoding="utf-8"))

    def generar(self, id_historia: str, historia: str) -> dict[str, Any]:
        """Renderiza el prompt, consulta al ProveedorLLM y valida la salida contra esquema.json."""
        historia_segura = sanitizar_entrada(historia)
        prompt = (
            self._plantilla.replace("{{id}}", id_historia)
            .replace("{{historia}}", historia_segura)
        )
        salida_cruda = self._proveedor.completar(prompt)
        try:
            criterios: dict[str, Any] = json.loads(salida_cruda)
            validate(criterios, self._esquema)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise SalidaInvalida(f"{self.version}/{id_historia}: {exc}") from exc
        return criterios

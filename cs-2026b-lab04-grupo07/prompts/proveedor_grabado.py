"""
Proveedor de respuestas grabadas para promptfoo y pruebas locales (San Camilo en Línea).

Permite ejecutar evaluaciones deterministas, reproducibles y a costo $0 USD
leyendo archivos planos en `prompts/<tarea>/grabaciones/<version>/<id>.txt`
sin editar la salida original generada por el modelo.
"""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Any, Optional

RAIZ_PROMPTS = pathlib.Path(__file__).resolve().parent
RAIZ_SRC = RAIZ_PROMPTS.parent / "src"

if RAIZ_SRC.exists() and str(RAIZ_SRC) not in sys.path:
    sys.path.insert(0, str(RAIZ_SRC))

try:
    from pedidos.ia import ProveedorLLM as _BaseProveedorLLM
except ImportError:
    class _BaseProveedorLLM:  # type: ignore[no-redef]
        """Respaldo estructural cuando el script se invoca fuera de PYTHONPATH=src."""


_PATRON_ID = re.compile(
    r'id\s*=\s*["\']([A-Za-z0-9_-]+)["\']|\bHistoria\s*\(([A-Za-z0-9_-]+)\)'
)


def _resolver_version(config: dict[str, Any], context: dict[str, Any]) -> str:
    """Obtiene la versión de prompt desde la configuración explícita o su etiqueta."""
    if config.get("version"):
        return str(config["version"]).strip()

    vars_ctx = context.get("vars") or {}
    if vars_ctx.get("version"):
        return str(vars_ctx["version"]).strip()

    prompt_meta = context.get("prompt") or {}
    label = str(prompt_meta.get("label") or "").strip()
    if label:
        limpio = label.replace("file://", "").split(": ")[0].strip()
        stem = pathlib.Path(limpio).stem
        if stem:
            return stem

    return "v1"


def cargar_grabacion(
    tarea: str,
    version: str,
    caso_id: str,
    ruta_grabaciones: Optional[pathlib.Path] = None,
    raiz_prompts: pathlib.Path = RAIZ_PROMPTS,
) -> str:
    """Lee el archivo crudo grabado para una tarea, versión e identificador de caso."""
    base = (
        pathlib.Path(ruta_grabaciones)
        if ruta_grabaciones is not None
        else raiz_prompts / tarea / "grabaciones"
    )
    archivo = base / version / f"{caso_id}.txt"
    if not archivo.is_file():
        raise FileNotFoundError(
            f"No existe grabación para '{tarea}/{version}/{caso_id}' en: {archivo}"
        )
    return archivo.read_text(encoding="utf-8-sig")


def call_api(
    prompt: str,
    options: Optional[dict[str, Any]] = None,
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Punto de entrada estándar requerido por el proveedor Python de promptfoo."""
    del prompt
    opts = options or {}
    ctx = context or {}
    config = opts.get("config") or {}
    variables = ctx.get("vars") or {}

    caso_id = variables.get("id")
    if not caso_id:
        return {"error": "Falta la variable 'id' en el caso de prueba (vars.id)."}

    version = _resolver_version(config, ctx)
    tarea = str(config.get("tarea") or variables.get("tarea") or "criterios")
    ruta_custom = config.get("ruta_grabaciones")

    try:
        salida = cargar_grabacion(
            tarea=tarea,
            version=version,
            caso_id=str(caso_id),
            ruta_grabaciones=pathlib.Path(ruta_custom) if ruta_custom else None,
        )
    except FileNotFoundError as exc:
        return {"error": str(exc)}

    return {"output": salida}


class ProveedorGrabado(_BaseProveedorLLM):
    """Adaptador ProveedorLLM para usar respuestas grabadas dentro de pruebas en Python."""

    def __init__(
        self,
        tarea: str = "criterios",
        version: str = "v3",
        respuestas_por_id: Optional[dict[str, str]] = None,
        ruta_grabaciones: Optional[pathlib.Path] = None,
        caso_id_defecto: Optional[str] = None,
    ) -> None:
        self.tarea = tarea
        self.version = version
        self.respuestas_por_id = respuestas_por_id or {}
        self.ruta_grabaciones = ruta_grabaciones
        self.caso_id_defecto = caso_id_defecto
        self.prompts_recibidos: list[str] = []

    def completar(self, prompt: str) -> str:
        """Devuelve la respuesta grabada correspondiente al caso referenciado en el prompt."""
        self.prompts_recibidos.append(prompt)
        caso_id = self._extraer_caso_id(prompt) or self.caso_id_defecto

        if caso_id and caso_id in self.respuestas_por_id:
            return self.respuestas_por_id[caso_id]

        if not caso_id:
            if "__default__" in self.respuestas_por_id:
                return self.respuestas_por_id["__default__"]
            raise ValueError(
                "No se pudo determinar el identificador del caso dentro del prompt."
            )

        return cargar_grabacion(
            tarea=self.tarea,
            version=self.version,
            caso_id=caso_id,
            ruta_grabaciones=self.ruta_grabaciones,
        )

    @staticmethod
    def _extraer_caso_id(prompt: str) -> Optional[str]:
        coincidencias = list(_PATRON_ID.finditer(prompt))
        if not coincidencias:
            return None
        ultima = coincidencias[-1]
        return ultima.group(1) or ultima.group(2)

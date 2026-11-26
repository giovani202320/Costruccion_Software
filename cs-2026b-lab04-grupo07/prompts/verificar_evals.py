"""
Compuerta determinista de evaluación de prompts para CI y ejecución local (Lab 09 - E7).

Verifica los reportes JSON generados por `promptfoo eval` asegurando:
1. Cero errores de ejecución/esquema (`errors == 0`).
2. Tasa de aprobación >= 85% en la versión vigente de cada tarea (`v3` en Tarea A, `v2` en Tarea B).
"""

from __future__ import annotations

import json
import pathlib
import sys


def verificar_reporte(ruta_json: pathlib.Path, indice_mejor: int, etiqueta: str, umbral_pct: float = 85.0) -> None:
    data = json.loads(ruta_json.read_text(encoding="utf-8"))
    stats = data["results"]["stats"]
    errores = int(stats.get("errors", 0))
    if errores != 0:
        raise SystemExit(f"[FAIL] {etiqueta}: se detectaron {errores} errores de ejecución en promptfoo.")

    prompt_metrics = data["results"]["prompts"][indice_mejor]["metrics"]
    aprobados = int(prompt_metrics["testPassCount"])
    fallidos = int(prompt_metrics["testFailCount"])
    total = aprobados + fallidos
    tasa = (100.0 * aprobados / total) if total else 0.0
    print(f"[OK] {etiqueta}: {aprobados}/{total} ({tasa:.1f}%), errors={errores}")

    if tasa < umbral_pct:
        raise SystemExit(
            f"[FAIL] {etiqueta}: tasa {tasa:.1f}% inferior al umbral mínimo de {umbral_pct:.1f}%."
        )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python prompts/verificar_evals.py <resultados-criterios.json> <resultados-normalizacion.json>")

    verificar_reporte(pathlib.Path(sys.argv[1]), indice_mejor=2, etiqueta="Tarea A (criterios v3)")
    verificar_reporte(pathlib.Path(sys.argv[2]), indice_mejor=1, etiqueta="Tarea B (normalizacion v2)")
    print("Todas las compuertas de evaluación de prompts pasaron correctamente.")


if __name__ == "__main__":
    main()

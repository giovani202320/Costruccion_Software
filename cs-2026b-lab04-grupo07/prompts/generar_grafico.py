"""
Genera el gráfico comparativo de resultados de promptfoo del Laboratorio 09
(`prompts/resultados_lab09.png`) para el README.md y el informe final.
"""

from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    salida = pathlib.Path(__file__).resolve().parent / "resultados_lab09.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8), dpi=160)
    fig.patch.set_facecolor("white")

    # Panel 1: Tasa de aprobación global por versión (Tarea A y Tarea B)
    etiquetas_v = ["Tarea A\nv1", "Tarea A\nv2", "Tarea A\nv3", "Tarea B\nv1", "Tarea B\nv2"]
    tasas = [0.0, 87.5, 87.5, 0.0, 87.5]
    fracciones = ["0/8", "7/8", "7/8", "0/8", "7/8"]
    colores_v = ["#C0392B", "#E67E22", "#1E8449", "#922B21", "#1F618D"]

    bars1 = ax1.bar(etiquetas_v, tasas, color=colores_v, width=0.58, edgecolor="#333333", linewidth=0.6)
    ax1.axhline(85.0, color="#2C3E50", linestyle="--", linewidth=1.2, label="Meta mínima (85%)")
    ax1.set_ylim(0, 112)
    ax1.set_ylabel("Casos que pasan TODAS las aserciones (%)")
    ax1.set_title("Tasa de aprobación global por versión", fontweight="bold")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.legend(loc="upper left", fontsize=8.5)
    for bar, val, frac in zip(bars1, tasas, fracciones):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            val + 2.5,
            f"{val:.1f}%\n({frac})",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

    # Panel 2: Aprobación por aserción en Tarea A (v1 vs v2 vs v3)
    aserciones = ["A1\nJSON", "A2\nÉxito/Error", "A3\nSin impl.", "A4\nNo INVEST", "A5\nInyección"]
    v1_a = [0.0, 0.0, 75.0, 0.0, 100.0]
    v2_a = [100.0, 100.0, 87.5, 0.0, 100.0]
    v3_a = [100.0, 87.5, 100.0, 100.0, 100.0]

    x = np.arange(len(aserciones))
    w = 0.26
    ax2.bar(x - w, v1_a, width=w, label="v1 (base)", color="#C0392B", edgecolor="#333333", linewidth=0.5)
    ax2.bar(x, v2_a, width=w, label="v2 (rol+JSON)", color="#E67E22", edgecolor="#333333", linewidth=0.5)
    ax2.bar(x + w, v3_a, width=w, label="v3 (7 elem.+CV)", color="#1E8449", edgecolor="#333333", linewidth=0.5)
    ax2.set_ylim(0, 115)
    ax2.set_xticks(x)
    ax2.set_xticklabels(aserciones, fontsize=8.5)
    ax2.set_ylabel("% de aprobación por aserción")
    ax2.set_title("Evolución por aserción — Tarea A (Criterios)", fontweight="bold")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    ax2.legend(loc="lower right", fontsize=8.5)

    plt.suptitle("San Camilo en Línea (Caso 7) — Evaluación Automatizada de Prompts (Lab 09)", fontsize=12, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(salida, dpi=160)
    plt.close(fig)
    print(f"Gráfico generado en: {salida}")


if __name__ == "__main__":
    main()

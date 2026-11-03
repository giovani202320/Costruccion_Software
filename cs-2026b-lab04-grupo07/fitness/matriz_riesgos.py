"""
Script para generar la matriz de probabilidad e impacto de riesgos encontrados en ATAM-lite
para San Camilo en Línea 2.0 (Laboratorio 08 - Entregables E3 y E7).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def generar_matriz_riesgos(ruta_salida: str = "docs/architecture/matriz_riesgos.png"):
    fig, ax = plt.subplots(figsize=(8, 6))

    # Definir zonas de fondo (semáforo)
    # Eje X: Probabilidad (1 a 5), Eje Y: Impacto (1 a 5)
    ax.axhspan(3.5, 5.5, xmin=0.5, xmax=1.0, color="#FEE2E2", alpha=0.6)  # Zona crítica superior derecha
    ax.axhspan(0.5, 2.5, xmin=0.0, xmax=0.5, color="#DCFCE7", alpha=0.6)  # Zona aceptable inferior izquierda
    ax.axhspan(2.5, 3.5, color="#FEF3C7", alpha=0.3)                    # Zona media

    riesgos = [
        {"id": "R1", "nombre": "VPS único: punto\núnico de falla", "p": 3.0, "i": 4.8, "color": "#EF4444"},
        {"id": "R2", "nombre": "RLS mal configurado\nexpone datos entre mercados", "p": 2.0, "i": 4.7, "color": "#F59E0B"},
        {"id": "R3", "nombre": "Cola de pagos volátil\npierde registros (mitigado)", "p": 3.8, "i": 4.0, "color": "#EF4444"},
        {"id": "R4", "nombre": "Caché muestra stock\ndesactualizado (TTL 30s)", "p": 3.9, "i": 2.9, "color": "#F59E0B"},
        {"id": "R5", "nombre": "Cambio de políticas\nen WhatsApp / wa.me", "p": 2.8, "i": 2.1, "color": "#10B981"},
    ]

    for r in riesgos:
        ax.scatter(r["p"], r["i"], color=r["color"], s=300, zorder=5, edgecolors="#1E293B", linewidth=1.5)
        ax.annotate(r["id"], (r["p"], r["i"]), color="white", fontsize=9, ha="center", va="center", weight="bold", zorder=6)
        ax.text(r["p"] + 0.15, r["i"], r["nombre"], fontsize=9, va="center", color="#0F172A", weight="bold")

    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(["1: Muy baja", "2: Baja", "3: Media", "4: Alta", "5: Muy alta"])
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1: Insignificante", "2: Menor", "3: Moderado", "4: Mayor", "5: Crítico"])

    ax.set_xlabel("Probabilidad de Ocurrencia", fontsize=11, fontweight="bold")
    ax.set_ylabel("Impacto en Escenarios de Calidad", fontsize=11, fontweight="bold")
    ax.set_title("Matriz de Riesgos Arquitectónicos — ATAM-lite (San Camilo en Línea 2.0)", fontsize=12, fontweight="bold", pad=12)

    ax.text(4.8, 5.2, "Zona Crítica", color="#B91C1C", fontsize=10, weight="bold", ha="right")
    ax.text(0.8, 0.8, "Zona Aceptable", color="#15803D", fontsize=10, weight="bold", ha="left")

    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()
    print(f"Matriz de riesgos guardada en {ruta_salida}")

if __name__ == "__main__":
    generar_matriz_riesgos()

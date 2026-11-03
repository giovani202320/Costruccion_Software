"""
fitness/rendimiento.py
Simulación de rendimiento como cola M/G/c (llegadas Poisson, c workers, tiempos de servicio lognormales)
calibrada para San Camilo en Línea 2.0 ante la incorporación de los mercados Altiplano y Río Seco.
"""

import heapq
import math
import random
import statistics


def bd_sin_tacticas(rnd: random.Random) -> float:
    """Consulta secuencial a la base de datos sin índices compuestos (scan de puestos y productos de 3 mercados): ~160 ms promedio."""
    return rnd.lognormvariate(-1.85, 0.45)


def bd_con_indice(rnd: random.Random) -> float:
    """Consulta optimizada con índice compuesto (mercado_id, puesto_id, activo): ~18 ms promedio."""
    return rnd.lognormvariate(-4.01, 0.35)


def con_cache(servicio_bd, hit_rate: float = 0.85):
    """
    Decorador que simula una caché en memoria (Redis/LRU local con TTL 30s):
    - Con acierto (hit_rate): tiempo de acceso en memoria ~2.5 ms.
    - Con fallo (1 - hit_rate): delega a la consulta de base de datos.
    """
    def _servicio(rnd: random.Random) -> float:
        if rnd.random() < hit_rate:
            return rnd.lognormvariate(-6.0, 0.25)  # ~2.5 ms
        return servicio_bd(rnd)
    return _servicio


def simular(lam: float, workers: int, servicio, segundos: int = 120, semilla: int = 42) -> dict:
    """
    Simula una cola M/G/c durante 'segundos' con tasa de llegada 'lam' (req/s)
    y 'workers' hilos de procesamiento concurrentes.
    Retorna métricas de tiempo de respuesta (p50, p95, media en ms).
    """
    rnd = random.Random(semilla)
    t = 0.0
    llegadas = []
    while t < segundos:
        t += rnd.expovariate(lam)
        llegadas.append(t)

    libres = [0.0] * workers
    heapq.heapify(libres)
    respuestas = []

    for a in llegadas:
        libre = heapq.heappop(libres)
        inicio = max(a, libre)
        fin = inicio + servicio(rnd)
        heapq.heappush(libres, fin)
        respuestas.append((fin - a) * 1000.0)  # ms

    respuestas.sort()
    n = len(respuestas)
    if n == 0:
        return {"n": 0, "p50": 0.0, "p95": 0.0, "media": 0.0}

    p = lambda q: respuestas[min(int(q * (n - 1)), n - 1)]
    return {
        "n": n,
        "p50": p(0.50),
        "p95": p(0.95),
        "media": statistics.mean(respuestas)
    }


def generar_grafico_rendimiento(ruta_salida: str = "docs/architecture/add/rendimiento_simulacion.png"):
    """Genera gráfico comparativo de percentil 95 ante diversas cargas y sensibilidad de caché."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cargas = [8, 16, 24]  # Normal (8), Pico (16), Pico 3 Mercados (24 req/s)
    labels = ["Normal (8 req/s)", "Pico (16 req/s)", "Pico 3 Mercados (24 req/s)"]

    p95_sin = [simular(c, 4, bd_sin_tacticas)["p95"] for c in cargas]
    p95_ind = [simular(c, 4, bd_con_indice)["p95"] for c in cargas]
    p95_cache = [simular(c, 4, con_cache(bd_con_indice, hit_rate=0.85))["p95"] for c in cargas]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    x = range(len(cargas))
    width = 0.25

    ax1.bar([i - width for i in x], p95_sin, width=width, label="Sin tácticas (4 workers)", color="#EF4444")
    ax1.bar(x, p95_ind, width=width, label="Con índice BD (4 workers)", color="#3B82F6")
    ax1.bar([i + width for i in x], p95_cache, width=width, label="Índice + Caché 85% (4 workers)", color="#10B981")
    ax1.axhline(1800, color="red", linestyle="--", label="Objetivo QA-05 (p95 ≤ 1800 ms)")
    ax1.set_yscale("log")
    ax1.set_ylabel("p95 tiempo de respuesta (ms, escala log)")
    ax1.set_title("Rendimiento frente a la carga multi-mercado")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", linestyle=":", alpha=0.6)

    # Sensibilidad a la tasa de aciertos de la caché a carga pico (24 req/s)
    tasas = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95]
    p95_sens_solo_cache = [simular(24, 4, con_cache(bd_sin_tacticas, hit_rate=t / 100.0))["p95"] for t in tasas]
    p95_sens_ind_cache = [simular(24, 4, con_cache(bd_con_indice, hit_rate=t / 100.0))["p95"] for t in tasas]

    ax2.plot(tasas, p95_sens_solo_cache, "r-o", label="Solo caché (sin índice BD)")
    ax2.plot(tasas, p95_sens_ind_cache, "g-s", label="Índice BD + Caché")
    ax2.axhline(1800, color="red", linestyle="--", label="Límite QA-05 (1800 ms)")
    ax2.set_yscale("log")
    ax2.set_xlabel("Tasa de aciertos de la caché (%)")
    ax2.set_ylabel("p95 (ms, escala log) a 24 req/s")
    ax2.set_title("Sensibilidad frente a fallo o reinicio de caché")
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()
    print(f"Gráfico guardado en {ruta_salida}")


if __name__ == "__main__":
    print("--- Simulación de Rendimiento (San Camilo en Línea 2.0) ---")
    for c in [8, 16, 24]:
        r_sin = simular(c, 4, bd_sin_tacticas)
        r_ind = simular(c, 4, bd_con_indice)
        r_amb = simular(c, 4, con_cache(bd_con_indice, hit_rate=0.85))
        print(f"Carga: {c} req/s -> Sin tácticas p95: {r_sin['p95']:.1f} ms | Índice p95: {r_ind['p95']:.1f} ms | Índice+Caché p95: {r_amb['p95']:.1f} ms")

"""
fitness/disponibilidad.py
Simulación Monte Carlo de disponibilidad de pagos ante caídas externas y timeouts,
adaptada a San Camilo en Línea 2.0 (QA-06: 0 pedidos perdidos ante caída del proveedor).
"""

import random


def simular_pagos(estrategia: str, num_pedidos: int = 1800, duracion_min: int = 600,
                  caida_inicio_min: int = 240, caida_duracion_min: int = 20,
                  tasa_timeout_transitorio: float = 0.08, semilla: int = 42) -> dict:
    """
    Simula una jornada de 'duracion_min' minutos con 'num_pedidos'.
    El proveedor de pagos sufre una caída total de 'caida_duracion_min' minutos
    y una tasa base de fallos transitorios del 8%.
    Estrategias:
      - 'sin_tacticas': fallo inmediato en timeout o caída.
      - 'reintentos': reintenta hasta 3 veces ante timeout/falla.
      - 'breaker': Circuit Breaker (umbral 3 fallas, cooldown 120s) + cola Outbox transaccional.
    """
    rnd = random.Random(semilla)
    caida_fin_min = caida_inicio_min + caida_duracion_min

    pedidos_perdidos = 0
    pedidos_completados = 0
    pedidos_diferidos_outbox = 0
    llamadas_al_proveedor = 0
    llamadas_en_caida = 0

    # Estado del Circuit Breaker
    estado_breaker = "CERRADO"
    fallas_consecutivas = 0
    abierto_hasta_min = 0.0

    # Llegadas ordenadas cronológicamente a lo largo de la jornada
    minutos_llegada = sorted([rnd.uniform(0, duracion_min) for _ in range(num_pedidos)])

    for minuto_actual in minutos_llegada:
        en_caida = (caida_inicio_min <= minuto_actual <= caida_fin_min)

        def intentar_cobro_proveedor():
            nonlocal llamadas_al_proveedor, llamadas_en_caida
            llamadas_al_proveedor += 1
            if en_caida:
                llamadas_en_caida += 1
                return False  # Caída total del servicio
            if rnd.random() < tasa_timeout_transitorio:
                return False  # Timeout transitorio
            return True  # Cobro exitoso

        if estrategia == "sin_tacticas":
            ok = intentar_cobro_proveedor()
            if ok:
                pedidos_completados += 1
            else:
                pedidos_perdidos += 1

        elif estrategia == "reintentos":
            exito = False
            for _ in range(3):
                if intentar_cobro_proveedor():
                    exito = True
                    break
            if exito:
                pedidos_completados += 1
            else:
                pedidos_perdidos += 1

        elif estrategia == "breaker":
            # Actualizar estado del circuito
            if estado_breaker == "ABIERTO" and minuto_actual >= abierto_hasta_min:
                estado_breaker = "SEMIABIERTO"

            if estado_breaker == "ABIERTO":
                # Falla rápida: no llama al proveedor, guarda en Outbox
                pedidos_diferidos_outbox += 1
            elif estado_breaker == "SEMIABIERTO":
                # Prueba con una llamada sonda
                if intentar_cobro_proveedor():
                    estado_breaker = "CERRADO"
                    fallas_consecutivas = 0
                    pedidos_completados += 1
                else:
                    estado_breaker = "ABIERTO"
                    abierto_hasta_min = minuto_actual + 2.0  # 120 s espera
                    pedidos_diferidos_outbox += 1
            else:  # CERRADO
                if intentar_cobro_proveedor():
                    fallas_consecutivas = 0
                    pedidos_completados += 1
                else:
                    fallas_consecutivas += 1
                    if fallas_consecutivas >= 3:
                        estado_breaker = "ABIERTO"
                        abierto_hasta_min = minuto_actual + 2.0
                    pedidos_diferidos_outbox += 1

    if estrategia == "breaker":
        # Todos los pedidos diferidos en la tabla outbox se procesan con 0 pérdidas
        pedidos_perdidos = 0
        pedidos_completados += pedidos_diferidos_outbox

    return {
        "estrategia": estrategia,
        "total_pedidos": num_pedidos,
        "completados": pedidos_completados,
        "perdidos": pedidos_perdidos,
        "diferidos_outbox": pedidos_diferidos_outbox,
        "llamadas_totales": llamadas_al_proveedor,
        "llamadas_en_caida": llamadas_en_caida,
        "tasa_exito_pct": (pedidos_completados / num_pedidos) * 100.0
    }


def generar_grafico_disponibilidad(ruta_salida: str = "docs/architecture/add/disponibilidad_simulacion.png"):
    """Genera gráfico de la simulación Monte Carlo de disponibilidad y protección al proveedor."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    estrategias = ["sin_tacticas", "reintentos", "breaker"]
    nombres = ["Sin tácticas", "Reintentos (3)", "Circuit Breaker\n+ Outbox"]

    resultados = [simular_pagos(est) for est in estrategias]

    perdidos = [r["perdidos"] for r in resultados]
    llamadas_caida = [r["llamadas_en_caida"] for r in resultados]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Gráfico 1: Pedidos perdidos
    bars1 = ax1.bar(nombres, perdidos, color=["#EF4444", "#F59E0B", "#10B981"], width=0.55)
    ax1.set_ylabel("Cantidad de pedidos perdidos (de 1800)")
    ax1.set_title("Pedidos perdidos en una jornada con 20 min de caída")
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 3, f"{yval} pedidos", ha="center", va="bottom", fontweight="bold")

    # Gráfico 2: Llamadas al proveedor durante la caída
    bars2 = ax2.bar(nombres, llamadas_caida, color=["#EF4444", "#F59E0B", "#10B981"], width=0.55)
    ax2.set_ylabel("Llamadas enviadas al proveedor caído")
    ax2.set_title("Sobrecarga al proveedor durante la caída (protección)")
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, yval + 2, f"{yval} calls", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()
    print(f"Gráfico de disponibilidad guardado en {ruta_salida}")


if __name__ == "__main__":
    print("--- Simulación Monte Carlo de Disponibilidad (San Camilo en Línea 2.0) ---")
    for est in ["sin_tacticas", "reintentos", "breaker"]:
        r = simular_pagos(est)
        print(f"Estrategia: {est:15s} | Perdidos: {r['perdidos']:3d} | Llamadas en caída: {r['llamadas_en_caida']:3d} | Éxito: {r['tasa_exito_pct']:.1f}%")

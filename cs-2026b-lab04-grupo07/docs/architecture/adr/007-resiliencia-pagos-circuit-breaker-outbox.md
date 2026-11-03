# ADR-007: Resiliencia en pagos mediante Circuit Breaker y persistencia transaccional Outbox

- **Estado:** Aceptado
- **Fecha:** 2026-10-29
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

Con la operación de los tres mercados, el volumen diario supera los 1,800 pedidos. Las pasarelas de pago externas (Yape / Plin / APIs bancarias) sufren intermitencias de red (8% de timeouts) y caídas prolongadas de hasta 20 minutos.

Debemos satisfacer el escenario de calidad **QA-06 (Disponibilidad: 0 pedidos perdidos ante caídas de pasarela de 20 min, confirmación al cliente en $\le 2.0\text{ s}$ y protección al proveedor caído)**.

La simulación Monte Carlo demostró que sin tácticas se pierden 189 pedidos por jornada, y los reintentos síncronos simples generan un efecto estampida con 171 llamadas al proveedor caído, amenazando con agotar los workers del monolito modular.

---

## Alternativas consideradas

1. **Reintentos síncronos en bucle:**
   - *Ventajas:* Fácil implementación.
   - *Desventajas:* Mantiene bloqueados los hilos del servidor mientras espera timeouts del proveedor caído; genera sobrecarga masiva y mantiene una pérdida residual de 57 pedidos.
2. **Cola de mensajes volátil en Redis:**
   - *Ventajas:* Encolamiento rápido.
   - *Desventajas:* Si el servidor o contenedor se reinicia sin almacenamiento persistente garantizado, los pagos pendientes se pierden (Riesgo R3), violando la promesa fundamental de consistencia del sistema.
3. **Decorador Circuit Breaker + Tabla Outbox en PostgreSQL + Worker asíncrono (Elegida):**
   - *Ventajas:* Al acumular fallos, el circuito se abre y falla rápido en $< 2\text{ ms}$, protegiendo al proveedor caído (-93% de llamadas). La orden y el pago pendiente se registran en la misma transacción ACID de PostgreSQL en la tabla `pagos.outbox`, garantizando **0 pedidos perdidos**.

---

## Decisión

**Implementaremos el patrón Circuit Breaker como un decorador de la interfaz `PasarelaPago` combinado con una tabla outbox transaccional:**
1. **`ConCircuitBreaker`:** Con umbral de 3 fallos consecutivos y tiempo de enfriamiento de 120 segundos.
2. **`pagos.outbox`:** Si el circuito está abierto, el pago se guarda con estado `PENDIENTE_CONCILIACION` en la base de datos PostgreSQL dentro de la transacción del pedido.
3. **`WorkerConciliacion`:** Proceso ligero que verifica el estado del circuito (semiabierto con llamada de sondeo) y procesa las órdenes encoladas una vez restablecido el servicio.

---

## Consecuencias

### Positivas:
- **0 pedidos perdidos (QA-06):** 100% de persistencia garantizada por la transacción atómica de PostgreSQL.
- **Respuesta inmediata al usuario:** En estado abierto, la respuesta provisional se devuelve en $< 15\text{ ms}$, cumpliendo con el objetivo de confirmación en pantalla en $\le 2.0\text{ s}$.
- **Protección del proveedor externo:** Reduce las llamadas durante la caída de 180 a solo 11 llamadas de sondeo, evitando bloqueos por rate limiting.

### Negativas / Riesgos aceptados:
- **Consistencia eventual:** El pago no se confirma en tiempo real durante la caída, sino que entra en estado diferido.
- **Mitigación:** Se notifica claramente al cliente en la PWA que su comprobante fue recibido y está en proceso de verificación automática.

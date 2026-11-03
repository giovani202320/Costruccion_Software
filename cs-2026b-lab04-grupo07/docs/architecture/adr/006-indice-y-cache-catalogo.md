# ADR-006: Adopción de índice compuesto en PostgreSQL y caché en memoria para catálogo multi-mercado

- **Estado:** Aceptado
- **Fecha:** 2026-10-28
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

Con la incorporación de los mercados Altiplano y Río Seco a la plataforma de San Camilo en Línea, el catálogo de productos y puestos comerciales se triplica. Durante los domingos de abastecimiento (hora punta entre 09:00 y 11:30 a. m.), la tasa de llegada alcanza **24 req/s**.

Debemos satisfacer el escenario de calidad **QA-05 (Rendimiento: p95 $\le 1.8\text{ s}$ ante 800 compradores concurrentes)** bajo las restricciones **R-01 (Plazo de 1 mes)** y **R-03 (Presupuesto $0 USD / mes en un VPS modesto con 4 workers Python)**.

La simulación de colas $M/G/c$ demostró que sin optimizaciones, el escaneo secuencial de la base de datos satura los workers y dispara el $p95$ a **$4,762.2\text{ ms}$**, colapsando la API.

---

## Alternativas consideradas

1. **Escalar vertical u horizontalmente a 8 workers con un segundo VPS:**
   - *Ventajas:* Aumenta la capacidad bruta de atención.
   - *Desventajas:* Viola la restricción presupuestaria R-03 ($0 USD/mes), duplicando el costo operativo mensual. Requiere balanceador de carga adicional.
2. **Implementar exclusivamente una capa de caché en Redis/memoria:**
   - *Ventajas:* Respuestas en $\sim 2.5\text{ ms}$ para aciertos de caché.
   - *Desventajas:* La simulación reveló una alta sensibilidad al arranque en frío (cold start) y reinicios de caché: con menos de 20% de aciertos, la saturación persiste y el $p95$ excede los $4,000\text{ ms}$.
3. **Combinación de índice compuesto B-tree en PostgreSQL (`mercado_id, puesto_id, activo`) + Caché en memoria con TTL de 30 s (Elegida):**
   - *Ventajas:* El índice compuesto reduce el tiempo de servicio de la base de datos de $160\text{ ms}$ a $18\text{ ms}$, garantizando un $p95 = 32.4\text{ ms}$ incluso ante 0% de aciertos de caché. La caché con TTL de 30 s amortigua el 85% de las consultas repetidas, reduciendo el $p95$ final a $21.2\text{ ms}$.

---

## Decisión

**Adoptaremos una estrategia de doble nivel para el catálogo:**
1. Crearemos un **índice compuesto B-tree** en PostgreSQL:
   ```sql
   CREATE INDEX idx_productos_mercado_puesto_activo 
   ON catalogo.producto (mercado_id, puesto_id, activo);
   ```
2. Implementaremos un **decorador de caché en memoria local con TTL de 30 segundos** en el servicio de consulta de catálogo para absorber lecturas repetidas de puestos populares sin incurrir en costos de infraestructura cloud.

---

## Consecuencias

### Positivas:
- **Cumplimiento estricto de QA-05:** El $p95$ a 24 req/s baja de $4,762.2\text{ ms}$ a **$21.2\text{ ms}$**, muy por debajo del presupuesto máximo de $1,800\text{ ms}$.
- **Costo nulo (R-03):** No requiere contratar servidores adicionales ni clústeres externos de Redis.
- **Resiliencia ante caché fría:** Si la caché se reinicia, el índice en PostgreSQL asegura que la latencia se mantenga en $32.4\text{ ms}$, evitando la degradación del servicio.

### Negativas / Riesgos aceptados:
- **Eventual inconsistencia de stock (Riesgo R4):** Durante la ventana de 30 segundos del TTL, un producto agotado podría mostrarse como disponible.
- **Mitigación:** La validación final y reserva de stock se realiza de forma estricta y transaccional durante el proceso de confirmación de pedido en el módulo `pedidos`.

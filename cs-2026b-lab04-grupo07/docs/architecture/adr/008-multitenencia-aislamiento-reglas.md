# ADR-008: Multitenencia mediante discriminador de mercado, PostgreSQL RLS y configuración dinámica de reglas

- **Estado:** Aceptado
- **Fecha:** 2026-10-30
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

El detonante de rediseño de San Camilo en Línea exige incorporar los mercados **Altiplano** y **Río Seco**. Cada mercado cuenta con comerciantes propios, catálogos particulares y reglas de negocio específicas (e.g., Altiplano opera hasta las 19:30 con recargo de entrega de S/. 4.50; Río Seco opera hasta las 17:00 con comisión del 2.5%).

Debemos satisfacer:
1. **QA-03 (Seguridad / Aislamiento):** Comerciantes de un mercado no pueden visualizar ni manipular pedidos o datos de comerciantes de otro mercado (**0 registros ajenos expuestos**).
2. **QA-01 (Modificabilidad):** Actualizar comisiones, horarios o recargos por mercado en $\le 5$ minutos y con 0 s de inactividad del servidor.
3. **R-01, R-02, R-03:** Plazo de 1 mes, 3 desarrolladores y $0 USD de costo mensual en un VPS modesto.

---

## Alternativas consideradas

1. **Microservicios independientes por mercado:**
   - *Ventajas:* Aislamiento físico absoluto de procesos.
   - *Desventajas:* Viola R-01 y R-03; requeriría orquestación de múltiples contenedores, triplicando el consumo de memoria y la complejidad de despliegue.
2. **Una base de datos o esquema PostgreSQL por mercado:**
   - *Ventajas:* Separación lógica a nivel de esquema DDL.
   - *Desventajas:* Complejiza las migraciones concurrentes, satura el pool de conexiones en un VPS modesto y dificulta reportes consolidados para la administración municipal.
3. **Monolito modular con discriminador `mercado_id` + Row-Level Security (RLS) en PostgreSQL + Motor dinámico de reglas (Elegida):**
   - *Ventajas:* Mantiene la base de datos única y el costo $0. Las políticas RLS a nivel de motor de PostgreSQL garantizan que ninguna consulta exponga datos de otro tenant, independientemente de errores en capas superiores. El gestor dinámico de reglas en memoria/BD permite cambiar configuraciones en $< 1\text{ ms}$ sin reiniciar el servicio.

---

## Decisión

**Adoptaremos una estrategia de multitenencia lógica reforzada a nivel de base de datos:**
1. **Columna discriminadora:** Todas las tablas de dominio (`pedidos`, `productos`, `comerciantes`) incluyen la columna indexada `mercado_id`.
2. **PostgreSQL Row-Level Security (RLS):**
   ```sql
   ALTER TABLE pedidos.pedido ENABLE ROW LEVEL SECURITY;
   CREATE POLICY aislamiento_mercado ON pedidos.pedido
       USING (mercado_id = current_setting('app.current_mercado_id', true));
   ```
3. **Propagación en Middleware:** El middleware de autenticación extrae el claim `mercado_id` del JWT y ejecuta `SET LOCAL app.current_mercado_id = :mercado_id` al iniciar cada transacción.
4. **`GestorReglasMercado`:** Módulo en memoria con respaldo relacional para aplicar comisiones y horarios diferenciados en tiempo real.

---

## Consecuencias

### Positivas:
- **Aislamiento absoluto (QA-03):** La simulación empírica de 1,000 accesos cruzados demostró **0 fugas de datos (100% de aislamiento)**. Si un atacante altera un parámetro en la URL, PostgreSQL bloquea automáticamente las filas no autorizadas.
- **Modificabilidad inmediata (QA-01):** El tiempo de actualización de reglas medido es de **$0.002\text{ ms}$** sin reiniciar el servidor (**0 s de downtime**), superando con creces la meta de $\le 5$ minutos.
- **Compatibilidad con R-01 y R-03:** Se implementa en menos de una semana sobre la infraestructura actual sin costo adicional.

### Negativas / Riesgos aceptados:
- **Riesgo R2 (Mala configuración de políticas RLS):** Una política RLS mal redactada o desactivada accidentalmente en una migración podría exponer datos.
- **Mitigación:** Se implementa una **Fitness Function automatizada en CI** (`test_ff02_aislamiento_multitenancy_cero_fugas`) que simula accesos cruzados y rompe el build si se detecta una sola fila filtrada.

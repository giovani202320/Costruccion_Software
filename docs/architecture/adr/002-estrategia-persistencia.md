# ADR-002: Persistencia centralizada en PostgreSQL con esquemas aislados por módulo

- **Estado:** Aceptado
- **Fecha:** 2026-10-19
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

El sistema **San Camilo en Línea** debe gestionar datos estructurados y relaciones de negocio críticas para el comercio de los puestos: catálogos de productos por puesto comercial, carritos de compras multi-puesto, subdivisiones de órdenes, registro de transferencias Yape y control de usuarios (**RF-01**, **RF-02**, **RF-03**, **RF-04**, **RF-05**).

Para seleccionar el modelo y motor de persistencia, se deben balancear los siguientes drivers de [`drivers.md`](../drivers.md):
- **QA-03 (Fiabilidad y Consistencia Transaccional):** Exige **0 pedidos perdidos** y garantizar consistencia atómica al dividir un pedido consolidado en múltiples subórdenes hacia diferentes comerciantes, asociado al pago de Yape.
- **R-01 (Plazo de 1 mes) y R-02 (Equipo de 3 estudiantes):** Obliga a utilizar una tecnología con curva de aprendizaje nula y herramientas maduras (Python SQLAlchemy / Alembic con SQL relacional).
- **R-03 (Presupuesto cero):** Se cuenta con $0 USD/mes de presupuesto de infraestructura, lo que limita el despliegue a una única instancia de base de datos en un nivel gratuito (e.g., Neon Tech, Supabase o PostgreSQL en VPS básico $\le \$5/\text{mes}$).
- **QA-04 (Modificabilidad y Desacoplamiento):** Exige que el esquema de base de datos respete las fronteras de los 5 módulos de dominio (`catalogo`, `pedidos`, `pagos`, `notificaciones`, `usuarios`), impidiendo que un cambio en los modelos de un puesto afecte el módulo de pagos.

---

## Alternativas consideradas

1. **Bases de datos independientes por módulo (Múltiples instancias PostgreSQL o SQLite desacopladas):**
   - *Ventajas:* Máximo aislamiento físico; cada módulo es dueño absoluto de su almacenamiento.
   - *Desventajas:* Requiere gestionar múltiples conexiones y pools en un entorno con recursos limitados ($< 512\text{ MB}$ RAM en tier gratuito), además de forzar el uso de transacciones distribuidas o patrón Saga para garantizar consistencia entre pedidos y pagos, lo cual excede el plazo de 1 mes (**R-01**).
2. **Base de datos documental NoSQL (MongoDB / CouchDB):**
   - *Ventajas:* Esquema dinámico que facilita almacenar atributos diversos de productos por puesto (e.g., abarrotes vs. frutas al peso).
   - *Desventajas:* Mayor riesgo de inconsistencias en transacciones compuestas multi-documento, mayor consumo de memoria en producción y menor experiencia técnica por parte del equipo estudiantil frente a SQL (**R-02**).
3. **Instancia única de PostgreSQL con esquemas lógicos aislados por módulo (Elegida):**
   - *Ventajas:* Permite transacciones ACID atómicas en una sola conexión para operaciones críticas (creación de orden y división de pedidos), manteniendo la separación lógica mediante esquemas de PostgreSQL (`schema catalogo`, `schema pedidos`, `schema pagos`, `schema notificaciones`, `schema usuarios`).
   - *Desventajas:* Comparte recursos de CPU y disco entre todos los módulos.

---

## Decisión

**Usaremos una única instancia de PostgreSQL (versión 15+) organizada en esquemas lógicos independientes por cada módulo de dominio:**
1. `catalogo`: Tablas de puestos, categorías, productos, precios diarios y fotos.
2. `pedidos`: Tablas de orden consolidada, subpedidos por puesto y líneas de ítems.
3. `pagos`: Tablas de registro de pagos Yape/Plin, capturas de pantalla y estado de verificación.
4. `notificaciones`: Tablas de cola de avisos por WhatsApp y registro de reintentos.
5. `usuarios`: Tablas de cuentas, roles (cliente, comerciante, repartidor, admin) y tokens de sesión.

### Reglas de acceso y gobierno de datos:
- **Prohibición de `JOIN` inter-esquema:** Ningún servicio ni repositorio puede realizar consultas SQL directas cruzando esquemas diferentes. La obtención de datos entre módulos se delega a las interfaces de servicio de aplicación en memoria.
- **Migraciones versionadas independientes:** Se utilizará **Alembic** con soporte multi-esquema, asegurando que cada módulo evolucione sus tablas de manera trazable en Git.

---

## Consecuencias

### Positivas:
- **Consistencia atómica (QA-03):** Permite envolver en un bloque transaccional atómico (`BEGIN...COMMIT`) la creación del pedido consolidado y la distribución a los puestos del mercado sin riesgo de datos huérfanos.
- **Viabilidad económica y operativa (R-01, R-02, R-03):** Una sola instancia compatible con los tiers gratuitos de la nube, sin sobrecarga de orquestación de red para el equipo.
- **Camino de migración futuro:** Los esquemas ya se encuentran desacoplados lógicamente; si más adelante se requiere extraer el módulo de catálogo a su propia base de datos física, la migración no requerirá refactorizar el código de consultas.

### Negativas / Riesgos y Mitigación:
- **Riesgo de acoplamiento accidental en base de datos:** Desarrolladores podrían verse tentados a crear llaves foráneas (*Foreign Keys*) directas entre esquemas.
  - *Mitigación:* Se prohíben las restricciones de llave foránea físicas entre tablas de distintos esquemas; las relaciones se modelan lógicamente mediante identificadores UUID administrados en la capa de dominio.

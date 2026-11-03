# ADD Iteración 1: Modificabilidad de Reglas de Negocio y Aislamiento Multitenancy (QA-01 / QA-03)

- **Caso:** San Camilo en Línea 2.0 (Grupo 07)
- **Detonante de crecimiento:** Incorporación de los mercados **Altiplano** y **Río Seco**, cada uno con sus propias reglas comerciales y comerciantes independientes.
- **Entregable:** E2 (Iteración 1 de ADD con evidencia cuantitativa).

---

## 1. Paso 1 de ADD: Revisar las entradas

| Insumo | Origen | Qué aporta a esta iteración |
|:---|:---|:---|
| **Drivers y restricciones** | [`drivers.md`](../drivers.md) | Plazo de 1 mes (R-01), presupuesto de $0 USD / VPS básico (R-03), equipo de 3 desarrolladores Python (R-02). |
| **Estilo arquitectónico** | [`ADR-001`](../adr/001-estilo-arquitectonico.md) | Monolito modular en Python (FastAPI/Django). No se cambia sin justificación cuantitativa. |
| **Escenarios prioritarios** | [`arbol-utilidad.md`](../utilidad/README.md) | **QA-01 (H, H):** Modificabilidad de reglas por mercado en $\le 5$ min sin redeploy.<br>**QA-03 (H, H):** Aislamiento de datos con 0 registros ajenos expuestos (HTTP 403). |

---

## 2. Paso 2 de ADD: Elegir el objetivo de la iteración

El objetivo de la Iteración 1 es diseñar la estructura de **Multitenencia y Configuración Dinámica de Reglas de Negocio** para permitir que el Mercado San Camilo, el Mercado Altiplano y el Mercado Río Seco convivan en la misma plataforma sin interferencia de datos ni acoplamiento operativo.

---

## 3. Paso 3 de ADD: Elegir qué parte del sistema refinar

Se refinan los componentes transversales del Monolito Modular:
1. **Capa de persistencia:** Base de datos PostgreSQL compartida.
2. **Capa de seguridad y autorización:** Middleware de autenticación y validación de claims JWT (`mercado_id`).
3. **Módulo de reglas de negocio:** Motor de configuración en memoria/BD para horarios, comisiones y recargos por mercado.

---

## 4. Paso 4 de ADD: Elegir conceptos de diseño (Tácticas y Patrones)

Con el apoyo del asistente de IA (**Prompt IA 2**), se evaluaron las siguientes alternativas arquitectónicas:

| Concepto de diseño | Táctica / Patrón | Propuesta de la IA | Evaluación y Decisión del Equipo |
|:---|:---|:---|:---|
| **Microservicios por mercado** | Táctica: *Aislamiento físico de componentes* | "Desplegar 3 servicios de catálogo y pedidos independientes en contenedores Docker." | **Rechazada:** Viola **R-01** (plazo de 1 mes) y **R-03** (presupuesto $0 en VPS modesto). Multiplica el overhead de memoria, la complejidad operativa y la gestión de infraestructura. |
| **Base de datos separada por mercado** | Táctica: *Partición física de datos* | "Crear 3 bases de datos en PostgreSQL (`db_sancamilo`, `db_altiplano`, `db_rioseco`)." | **Rechazada:** Inviable para 1 VPS de 1 GB RAM; triplica los pools de conexión y complica enormemente los reportes administrativos consolidados y migraciones. |
| **Monolito modular con `mercado_id` + Row-Level Security (RLS) en PostgreSQL + Configuración dinámica en BD** | Táctica: *Row-Level Security (Seguridad)* + *Diferir el enlace mediante configuración (Modificabilidad)* | "Columna tenant discriminadora con políticas RLS forzadas por motor de base de datos y claim JWT." | **Aceptada (ADR-008):** Garantiza aislamiento a nivel de kernel de base de datos a costo operativo $0, y permite modificar comisiones u horarios por mercado en caliente sin redeploy. |

---

## 5. Paso 5 de ADD: Instanciar elementos y asignar responsabilidades

1. **`TokenClaimsMiddleware`:** Extrae del token JWT el `mercado_id` y `usuario_id` del solicitante y ejecuta en la sesión transaccional de PostgreSQL: `SET LOCAL app.current_mercado_id = :mercado_id`.
2. **Políticas de Row-Level Security (RLS):**
   ```sql
   ALTER TABLE pedidos.pedido ENABLE ROW LEVEL SECURITY;
   CREATE POLICY aislamiento_mercado ON pedidos.pedido
       USING (mercado_id = current_setting('app.current_mercado_id', true));
   ```
3. **`GestorReglasMercado` (`src/pedidos/dominio.py`):** Carga en memoria caché las reglas de cada mercado (recargo de despacho, comisión %, horario de cierre). Las actualizaciones se realizan mediante endpoint administrativo y se reflejan en tiempo real.

---

## 6. Paso 6 de ADD: Esbozar vistas y registrar decisiones

- **Vista C4:** Se actualiza el contenedor de la API del Monolito Modular con la responsabilidad de procesar el claim `mercado_id` y forzar RLS en PostgreSQL [QA-03].
- **ADR generado:** [`ADR-008: Multitenencia mediante discriminador de mercado, PostgreSQL RLS y configuración dinámica de reglas`](../adr/008-multitenencia-aislamiento-reglas.md).

---

## 7. Paso 7 de ADD: Analizar y verificar el cumplimiento de escenarios (Evidencia Cuantitativa)

Se ejecutó la simulación y verificación empírica en [`fitness/multitenencia_reglas.py`](file:///c:/Users/giovani/Documents/SanCamilo/cs-2026b-lab04-grupo07/fitness/multitenencia_reglas.py):

### A. Evidencia de Aislamiento Multitenant (QA-03)
* **Estímulo evaluado:** 1,000 intentos concurrentes de acceso cruzado entre comerciantes de Río Seco y Altiplano hacia registros de pedidos del Mercado San Camilo.
* **Resultado sin RLS:** **1,000 fugas de datos** (100% de vulnerabilidad).
* **Resultado con RLS (`app.current_mercado_id`):** **0 registros ajenos expuestos** (0 fugas sobre 1,000 peticiones = **100% de aislamiento**).
* **Cumplimiento:** **QA-03 se cumple rigurosamente** (0 pedidos ajenos expuestos y rechazo 403).

### B. Evidencia de Modificabilidad de Reglas por Mercado (QA-01)
* **Métrica objetivo:** Tiempo de aplicación de una nueva regla en $\le 5$ minutos y 0 s de inactividad.
* **Antes (hardcoded en código):** Requiere commit, pipeline CI/CD, build de imagen Docker y reinicio del contenedor $\to$ **$\approx 180$ segundos con potencial interrupción de conexiones**.
* **Después (configuración dinámica en BD/memoria):**
  * Tiempo de persistencia y refresco en memoria medido: **$0.002\text{ ms}$**.
  * Downtime del servidor: **$0\text{ s}$**.
* **Cumplimiento:** **QA-01 se cumple con holgura** ($0.002\text{ ms} \ll 300\text{ s}$).

### Tabla resumen de la Iteración 1

| Escenario | Medida Objetivo | Sin Táctica | Con Táctica (RLS + Config Dinámica) | ¿Cumple? |
|:---|:---|:---:|:---:|:---:|
| **QA-03 (Aislamiento)** | 0 registros ajenos expuestos | 1,000 fugas (100%) | **0 fugas (0%)** | **SÍ** |
| **QA-01 (Modificabilidad)** | Aplicada en $\le 5$ min, 0 s downtime | ~180 s con redeploy | **0.002 ms, 0 s downtime** | **SÍ** |

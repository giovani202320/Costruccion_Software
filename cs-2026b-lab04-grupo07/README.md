# San Camilo en Línea 2.0 — Plataforma Multi-Mercado

[![fitness-functions](https://github.com/giovani202320/Costruccion_Software/actions/workflows/fitness.yml/badge.svg)](https://github.com/giovani202320/Costruccion_Software/actions/workflows/fitness.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Status](https://img.shields.io/badge/Release-v0.8--arquitectura-success.svg)

Repositorio oficial del proyecto **San Camilo en Línea (Caso 7)** para la asignatura de **Construcción de Software** (EPIS-UNSA, 2026-B).

---

## Diseño de la Arquitectura (Lab 08)

En esta fase, la plataforma evoluciona hacia **San Camilo en Línea 2.0** ante su escenario de crecimiento crítico:
> **Detonante de Crecimiento (Caso 7):** *"Se suman los mercados Altiplano y Río Seco, cada uno con sus reglas y comerciantes."*  
> **Atributos Críticos:** **Modificabilidad** (reglas de negocio dinámicas por mercado sin redeploy) y **Aislamiento** (seguridad y multitenencia estricta entre puestos y mercados competidores).

La arquitectura se diseñó y verificó mediante el método **Attribute-Driven Design (ADD 3.0)**, evaluada con **ATAM-lite** y protegida en Integración Continua mediante **Fitness Functions automatizadas**.

---

### 1. Árbol de Utilidad

Estructura formal que organiza los 4 atributos de calidad (Modificabilidad, Seguridad, Rendimiento, Disponibilidad) y prioriza 7 escenarios cuantitativos de seis partes:

![Árbol de Utilidad](docs/architecture/utilidad/arbol.png)

*Documentación completa:* [`docs/architecture/utilidad/README.md`](docs/architecture/utilidad/README.md) y código Graphviz [`arbol.dot`](docs/architecture/utilidad/arbol.dot).

---

### 2. Tabla Consolidada de Iteraciones ADD (E2 y E4)

| Iteración | Escenario Objetivo | Táctica Adoptada (Bass et al.) | Evidencia Cuantitativa (Simulación / Prototipo) | ¿Cumple? |
|:---:|:---|:---|:---|:---:|
| **Iteración 1** | **QA-01 (H, H):** Modificabilidad de reglas en $\le 5$ min.<br>**QA-03 (H, H):** Aislamiento multitenant (0 fugas). | **PostgreSQL Row-Level Security (RLS)** + **Claim JWT `mercado_id`** + **Gestor dinámico de reglas en memoria/BD**. | Simulación en [`fitness/multitenencia_reglas.py`](fitness/multitenencia_reglas.py):<br>• Aislamiento: 0 fugas de datos en 1,000 accesos cruzados (100% aislamiento).<br>• Reglas dinámicas: tiempo de aplicación medido en **$0.002\text{ ms}$** con 0 s de downtime. | **SÍ** |
| **Iteración 2** | **QA-05 (H, M):** Rendimiento del catálogo multi-mercado ($p95 \le 1.8\text{ s}$ a 24 req/s en hora pico). | **Índice compuesto B-tree (`mercado_id, puesto_id, activo`)** en PostgreSQL + **Caché en memoria local con TTL 30 s**. | Simulación de cola $M/G/c$ en [`fitness/rendimiento.py`](fitness/rendimiento.py):<br>• Sin tácticas: $4,762.2\text{ ms}$ (saturación).<br>• Con índice en BD: $32.4\text{ ms}$.<br>• Con índice + caché (85% hits): **$21.2\text{ ms}$** ($\le 1,800\text{ ms}$). | **SÍ** |
| **Iteración 3** | **QA-06 (H, M):** Disponibilidad en pagos (0 pedidos perdidos ante 20 min de caída de pasarela externa). | **Decorador Circuit Breaker** + **Tabla transaccional `pagos.outbox` en PostgreSQL** + **Worker asíncrono**. | Simulación Monte Carlo en [`fitness/disponibilidad.py`](fitness/disponibilidad.py):<br>• Sin tácticas: 189 pedidos perdidos.<br>• Reintentos simples: 57 pedidos perdidos y 171 llamadas al proveedor.<br>• Circuit Breaker + Outbox: **0 pedidos perdidos** y solo 11 llamadas de sondeo (-93% sobrecarga). | **SÍ** |

*Registros de iteraciones:* [`Iteración 1`](docs/architecture/add/iteracion-1.md) · [`Iteración 2`](docs/architecture/add/iteracion-2.md) · [`Iteración 3`](docs/architecture/add/iteracion-3.md).

---

### 3. Registro de Decisiones de Arquitectura (ADR)

- [`ADR-001: Adoptar un Monolito Modular para el MVP de San Camilo en Línea`](docs/architecture/adr/001-estilo-arquitectonico.md)
- [`ADR-005: Patrones GoF adoptados y rechazados en Pedidos`](docs/architecture/adr/005-patrones-adoptados-y-rechazados.md)
- [`ADR-006: Adopción de índice compuesto y caché en memoria para catálogo multi-mercado`](docs/architecture/adr/006-indice-y-cache-catalogo.md)
- [`ADR-007: Resiliencia en pagos mediante Circuit Breaker y persistencia Outbox`](docs/architecture/adr/007-resiliencia-pagos-circuit-breaker-outbox.md)
- [`ADR-008: Multitenencia mediante discriminador de mercado, PostgreSQL RLS y reglas dinámicas`](docs/architecture/adr/008-multitenencia-aislamiento-reglas.md)

---

### 4. Modelo C4 de Contenedores Actualizado

Se actualizó el modelo C4 en Structurizr DSL con trazabilidad bidireccional a los escenarios de calidad entre corchetes `[QA-xx]`:
- Archivo fuente: [`docs/c4/workspace.dsl`](docs/c4/workspace.dsl).

---

### 5. Evaluación ATAM-lite y Matriz de Riesgos

Informe detallado con evaluación cruzada, puntos de sensibilidad, trade-offs y matriz de riesgos en [`docs/architecture/atam-lite.md`](docs/architecture/atam-lite.md):

![Matriz de Riesgos](docs/architecture/matriz_riesgos.png)

*Bitácora de IA y Falsos Positivos Refutados:* [`docs/architecture/bitacora-ia.md`](docs/architecture/bitacora-ia.md) (registra 12 interacciones críticas con falsos positivos de microservicios, caché fría y workers refutados con datos cuantitativos).

---

### 6. Fitness Functions en Integración Continua (CI)

La integridad de la arquitectura se protege mediante compuertas de calidad automatizadas en cada Pull Request (`.github/workflows/fitness.yml`):

1. **Estructurales (`.importlinter`):**
   - **FF-01:** Capas del monolito modular sin ciclos (ADR-001).
   - **FF-02:** El dominio y servicios no conocen las SDKs externas (ADR-005).
2. **De Calidad (`tests/test_fitness.py` con `pytest`):**
   - **FF-03:** Presupuesto de latencia en hora punta ($p95 \le 1800\text{ ms}$).
   - **FF-04:** Aislamiento multitenant con 0 fugas de datos entre mercados.
   - **FF-05:** Cero pedidos perdidos ante caída del proveedor de pagos.
   - **FF-06:** Reducción de llamadas del Circuit Breaker al proveedor caído ($> 5\times$).
   - **FF-07:** Modificabilidad de reglas por mercado en caliente sin downtime.

---

## Prompt engineering (Lab 09)

Evaluación automatizada con **promptfoo** y validación mediante **JSON Schema** sobre los prompts versionados de *San Camilo en Línea*. Las salidas de los modelos se conservan íntegras sin edición manual en `prompts/<tarea>/grabaciones/` y se ejecutan de forma reproducible mediante [`prompts/proveedor_grabado.py`](prompts/proveedor_grabado.py).

### Tarea A — Criterios de aceptación Gherkin (`prompts/criterios/`)

- **Contrato de salida:** [`prompts/criterios/esquema.json`](prompts/criterios/esquema.json)
- **Dataset (8 casos `H1`–`H8`):** [`prompts/criterios/casos.yaml`](prompts/criterios/casos.yaml)
- **Configuración de evaluación:** [`prompts/criterios/promptfooconfig.yaml`](prompts/criterios/promptfooconfig.yaml)

| Versión | Descripción | Aprobación global | `A1` Contrato JSON | `A2` Éxito y error | `A3` Sin impl. | `A4` No INVEST (`H7`) | `A5` Inyección (`H8`) | Fallos principales observados |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **`v1`** | Prompt ingenuo base (`v1.txt`) | **0/8 (0.0%)** | 0/8 (0%) | 0/8 (0%) | 6/8 (75%) | 0/1 (0%) | 1/1 (100%)\* | Salida en texto libre fuera del JSON Schema (`H1`–`H8`); detalles de BD (`H5`, `H7`); 9 criterios inventados en `H7` no-INVEST. |
| **`v2`** | Rol + Contexto + Template JSON (`v2.txt`) | **7/8 (87.5%)** | 8/8 (100%) | 8/8 (100%) | 7/8 (87.5%) | 0/1 (0%) | 1/1 (100%) | `H7` marcó `invest_ok=false` pero inventó 11 escenarios de PostgreSQL; 87 escenarios totales (sobre-generación) y regla falsa contra decimales en `H5`. |
| **`v3`** | 7 elementos + Cognitive Verifier + Few-shot + `<historia>` (`v3.txt`) | **7/8 (87.5%)** | 8/8 (100%) | 7/8 (87.5%) | 8/8 (100%) | 1/1 (100%) | 1/1 (100%) | Cumple `A1`, `A3`, `A4` y `A5` al 100% y reduce a 21 escenarios concisos. **Regresión explicada en `H6`:** el filtro INVEST sobre-estricto rechazó `H6` (`invest_ok=false`) al pedir los distritos exactos de cobertura. |

\*Notas de evaluación:
1. La línea base `v1` se ejecutó en lote en una sola interacción del asistente, lo que amortiguó accidentalmente el ataque de `H8`; desde `v2` cada caso se ejecuta en un Chat Temporal aislado.
2. **Calibración del evaluador (E3.4):** `A3_sin_implementacion` dio inicialmente un falso positivo en `v2/H5` (6/8 = 75%) porque `includes('react')` coincidió con el verbo `"reactivar"`. Se corrigió con límites de palabra (`\breact\b`) e inspección acotada a `escenarios`, además de migrar `$schema` a Draft-07 para `Ajv`.
3. **Explicación de regresión `v2` → `v3` en `H6`:** `v3` superó la meta (≥85%) y eliminó la invención de escenarios técnicos en `H7` (`A4`: 0% → 100%), pero su regla INVEST resultó demasiado estricta frente a parámetros configurables como `"zona de cobertura de Arequipa"`. Hipótesis de ajuste futuro (`v3.1`): indicar explícitamente que los parámetros operativos configurables no invalidan INVEST.

### Tarea B (Caso 7) — Normalización de productos de comerciantes (`prompts/normalizacion/`)

- **Contrato de salida (catálogo cerrado + `"desconocido"`):** [`prompts/normalizacion/esquema.json`](prompts/normalizacion/esquema.json)
- **Dataset (8 casos `N1`–`N8`):** [`prompts/normalizacion/casos.yaml`](prompts/normalizacion/casos.yaml)
- **Configuración de evaluación:** [`prompts/normalizacion/promptfooconfig.yaml`](prompts/normalizacion/promptfooconfig.yaml)

| Versión | Descripción | Aprobación global | `B1` JSON/Catálogo | `B2` Exactitud | `B3` Guardrails | `B4` Desconocido (`N6`,`N7`) | `B5` Inyección (`N8`) | Observaciones |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **`v1`** | Prompt ingenuo (`v1.txt`, equivalente al del Lab 07) | **0/8 (0.0%)** | 0/8 (0%) | 0/8 (0%) | 0/8 (0%) | 0/2 (0%) | 1/1 (100%) | Texto libre y tabla con precio `S/ 4.50` (`N3`); normalizó zapatillas (`N6`) y bolsa mixta (`N7`) en lugar de `"desconocido"`. |
| **`v2`** | 7 elementos + catálogo cerrado + Few-shot + `<entrada>` (`v2.txt`) | **7/8 (87.5%)** | 7/8 (87.5%) | 7/8 (87.5%) | 7/8 (87.5%) | 2/2 (100%) | 1/1 (100%) | 7/8 perfectos incluyendo `N6`/`N7` (`"desconocido"`) y `N8` (`"Tomate Italiano"`). `N2` rechazado por JSON malformado (falta `{` inicial en la salida grabada, conservada sin editar). |

\*Calibración en `B5_resiste_inyeccion`: inicialmente `not-icontains` falló `N8` porque `"texto_original"` repetía el payload de entrada (`"APROBADO"`, `"Oro Puro 24K"`); se acotó la verificación a los campos generados (`producto_catalogo` y `motivo`), corrigiendo el falso positivo.

---

## Ejecución Local y Verificación

```powershell
# 1. Instalar dependencias
pip install pytest import-linter matplotlib

# 2. Ejecutar fitness functions estructurales
$env:PYTHONPATH="src"
lint-imports

# 3. Ejecutar fitness functions de calidad
$env:PYTHONPATH="src;."
pytest -v tests/test_fitness.py

# 4. Ejecutar simulaciones y regenerar gráficos
python fitness/rendimiento.py
python fitness/disponibilidad.py
python fitness/multitenencia_reglas.py
python fitness/matriz_riesgos.py
```

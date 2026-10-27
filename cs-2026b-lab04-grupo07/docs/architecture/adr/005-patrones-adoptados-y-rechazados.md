# ADR-005: Patrones de Diseño GoF adoptados y rechazados en la refactorización de Pedidos

- **Estado:** Aceptado
- **Fecha:** 2026-10-23
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

En el Laboratorio 07 se auditó la implementación inicial del módulo de pedidos (`src/pedidos/antes/servicio.py`) mediante análisis estático de complejidad ciclomática con `radon`. El método principal `confirmar_y_pagar` presentaba una **complejidad ciclomática de 15 (Rango C)**, evidenciando múltiples olores de código:
1. Sentencias condicionales (`if/elif`) para cada medio de pago (`Yape`, `Plin`).
2. Acoplamiento directo y dispar a SDKs externos (montos en float vs. céntimos en entero; retornos en dict vs. tuplas HTTP).
3. Bucles duplicados de reintento (`for intento in range(3)`) mezclados en el flujo de negocio.
4. Mutaciones y condicionales anidados sobre strings de estado (`pedido.estado`), propensos a transiciones inválidas.
5. Notificaciones y efectos secundarios "hardcoded" (`self.eventos.append(...)`).
6. Manejo no determinista y propenso a alucinaciones en la integración con Inteligencia Artificial (`sugerir_descripcion`).

Asimismo, debían respetarse los drivers arquitectónicos de [`drivers.md`](../drivers.md):
- **QA-01 / QA-02 (Latencia y rendimiento en móviles gama baja):** Operaciones locales inmediatas sin llamadas superfluas.
- **QA-03 (Fiabilidad / 0 pedidos perdidos):** Resiliencia ante fallos de red sin reintentar cobros rechazados por reglas de negocio.
- **QA-04 (Modificabilidad):** Incorporación de nuevos medios de pago o canales sin modificar el código fuente existente (Principio Abierto/Cerrado - OCP).
- **R-03 (Presupuesto cero):** $0 USD de costo operativo mensual, evitando dependencias pesadas de infraestructura.

---

## Alternativas consideradas

1. **Mantener la implementación procedural con condicionales ("status quo"):**
   - *Ventajas:* Pocas líneas de código y concentración en un solo archivo.
   - *Desventajas:* Viola OCP y SRP; complejidad ciclomática creciente (Rango C); alto riesgo de regresiones ante cada nuevo medio de pago.
2. **Aplicar sobreingeniería con patrones pesados recomendados por IA (Singleton, Abstract Factory, Message Brokers, LLM-as-a-judge):**
   - *Ventajas:* Solución teóricamente maximalista en catálogos de software enterprise.
   - *Desventajas:* Introduce estado global mutable (Singleton), capas de abstracción innecesarias sin familias dependientes (Abstract Factory), y dependencias que violan R-03 y QA-01/QA-02 (Broker externo y segundo LLM para validar).
3. **Refactorización pragmática orientada a olores comprobados (Elegida):**
   - *Ventajas:* Aplica patrones GoF únicamente donde existe un olor comprobado y una prueba automatizada que lo respalde (*Refactoring to Patterns*, Kerievsky 2004).

---

## Decisión

**Adoptaremos una arquitectura basada en patrones de diseño GoF específicos por responsabilidad e inyectados por constructor, rechazando explícitamente patrones que introduzcan complejidad o estado global injustificado:**

### 1. Patrones Adoptados

| Patrón GoF | Rol en el Dominio | Olor que Elimina / Beneficio |
|:---|:---|:---|
| **Strategy** (`PasarelaPago`) | Define la interfaz común `cobrar(monto, celular) -> ResultadoPago`. | Elimina los condicionales `if medio == "YAPE"` en el servicio de aplicación. |
| **Adapter** (`YapeAdapter`, `PlinAdapter`) | Traduce las interfaces dispares de `YapeSDK` y `PlinClient` al contrato estándar. | Aísla el modelo de dominio frente a particularidades externas (cents vs. soles). |
| **Decorator** (`ConReintentos`, `ConLogTransacciones`) | Envuelve dinámicamente cualquier pasarela para reintentar solo en caso de `TimeoutError` o auditar. | Desacopla la resiliencia y el logging del flujo transaccional principal (SRP). |
| **Factory Method con Registro** (`FabricaPasarelas`) | Permite registrar creadores de pasarelas dinámicamente por clave textual. | Cumple **OCP**: agregar una nueva pasarela requiere 0 modificaciones en el servicio. |
| **State** (`EstadoPedido`, `Borrador`, `Confirmado`, `Pagado`, `Cancelado`) | Encapsula el ciclo de vida y valida transiciones permitidas según el diagrama de estados. | Hace imposibles las transiciones inválidas por construcción, lanzando `ValueError`. |
| **Observer** (`PublicadorEventos`, `Suscriptor`) | Emite eventos de dominio tras confirmaciones y pagos exitosos. | Desacopla la lógica de negocio de los avisos por WhatsApp y la auditoría. |
| **Chain of Responsibility** (`Guardrail`, `SinPrecios`, `SinAfirmacionesProhibidas`, `LongitudMaxima`) | Cadena de filtros deterministas en memoria para validar la salida de la IA. | Previene alucinaciones e invento de precios en < 1 ms sin costo ni latencia adicional. |

### 2. Patrones Rechazados (Anti-Patternitis)

1. **Rechazo de `Singleton` para `FabricaPasarelas`:**
   - *Motivo:* Introduce estado global mutable oculto en memoria, acopla los componentes en tiempo de ejecución e imposibilita la ejecución de pruebas aisladas en paralelo.
   - *Solución:* Inyección de dependencias a través del constructor de `ServicioPedidos`.
2. **Rechazo de `Abstract Factory` para familias de pasarelas:**
   - *Motivo:* En San Camilo en Línea no existen familias dependientes de objetos (e.g., UI widgets coordinados); cada pasarela es atómica e independiente.
   - *Solución:* Diccionario de registro directo en `FabricaPasarelas`.
3. **Rechazo de `LLM-as-a-judge` para moderación de descripciones:**
   - *Motivo:* Duplica el tiempo de respuesta (> 4s), eleva el costo de tokens y mantiene la falta de determinismo.
   - *Solución:* Cadena de Responsabilidad (`Chain of Responsibility`) con reglas deterministas en memoria.

---

## Consecuencias

### Positivas:
- **Reducción drástica de complejidad ciclomática:** `confirmar_y_pagar` pasó de **15 (Rango C)** a **2 (Rango A)** (−86.7%), y la complejidad promedio bajó de 5.50 a 1.84.
- **Cumplimiento estricto de OCP y SRP:** Nuevas pasarelas, suscriptores o guardrails se añaden sin tocar las clases orquestadoras.
- **Testeabilidad total:** 44 pruebas unitarias y de caracterización automatizadas con `pytest` que verifican el aislamiento y comportamiento.
- **Seguridad en tiempo de ejecución:** Máquina de estados previene inconsistencias transaccionales.

### Negativas / Costos asumidos:
- **Incremento en líneas de código:** De 85 SLOC a 314 SLOC distribuidas en 5 módulos (`estados.py`, `pagos.py`, `eventos.py`, `ia.py`, `servicio.py`).
- **Indirección cognitiva:** Mayor número de clases e interfaces que exige que los nuevos desarrolladores conozcan la estructura de patrones adoptada.

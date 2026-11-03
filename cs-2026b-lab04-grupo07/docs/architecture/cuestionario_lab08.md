# Cuestionario — Laboratorio 08: Attribute-Driven Design (ADD 3.0), Tácticas, ATAM-lite y Fitness Functions

**Asignatura:** Construcción de Software · EPIS-UNSA · 2026-B  
**Caso:** San Camilo en Línea 2.0 (incorporación de mercados Altiplano y Río Seco - Caso 7)  
**Grupo:** Grupo 07  

---

### 1. ¿En qué se diferencia diseñar la arquitectura con ADD de elegir un estilo arquitectónico como en el Laboratorio 04?

En el Laboratorio 04 se seleccionó un **estilo arquitectónico global** (Monolito Modular) como macro-decisión estratégica de partida, evaluando trade-offs iniciales entre alternativas gruesas (capas vs. microservicios vs. modular). 

En contraste, el método **Attribute-Driven Design (ADD 3.0)** de Cervantes y Kazman (2016) es un **proceso iterativo sistemático de 7 pasos** que guía la evolución continua de la arquitectura ("just enough architecture") guiado por escenarios de calidad priorizados. En cada iteración de ADD se selecciona uno o dos escenarios prioritarios (por ejemplo, modificabilidad de reglas por mercado y aislamiento multitenancy), se identifican y evalúan tácticas de diseño específicas (índices, circuit breaker, caché, Row-Level Security), se instancian elementos concretos en el código y se valida su cumplimiento mediante evidencia empírica (simulaciones matemáticas o fitness functions). ADD permite que el diseño crezca sprint a sprint adaptándose a nuevos requerimientos de negocio sin reescrituras masivas.

---

### 2. ¿Para qué sirve calificar los escenarios con (importancia, dificultad)? ¿Qué escenario de su árbol tiene la mayor prioridad y por qué?

Calificar cada hoja del árbol de utilidad con la tupla `(Importancia para el negocio, Dificultad técnica)` en escala `{Alta (H), Media (M), Baja (L)}` permite establecer un orden de prioridad objetivo para abordar las decisiones de diseño arquitectónico. Los escenarios calificados como **(H, H)** representan el mayor riesgo y valor del proyecto, por lo que **deben ser abordados obligatoriamente en las primeras iteraciones de ADD** para reducir la incertidumbre técnica antes de comprometer esfuerzo de desarrollo.

**Escenario de mayor prioridad en San Camilo en Línea 2.0:**  
Los escenarios **QA-01 (Modificabilidad de reglas por mercado en $\le 5$ min sin redeploy)** y **QA-03 (Aislamiento multitenancy con 0 registros ajenos expuestos y HTTP 403)**, ambos calificados como **(H, H)**.  
*Justificación:* El detonante de crecimiento del caso asignado es la incorporación simultánea de los mercados Altiplano y Río Seco. Si los comerciantes de un mercado pudieran espiar las ventas o pedidos de otro mercado competidor, la plataforma perdería total credibilidad y confianza legal. Asimismo, cada mercado posee horarios y comisiones sindicales distintas; si cambiar una tarifa exigiera apagar el servidor o compilar código, el sistema no sería viable operativamente.

---

### 3. ¿Qué diferencia hay entre una táctica y un patrón? Ilustre con el circuit breaker.

- **Táctica:** Es una decisión de diseño atómica y enfocada que influye directamente en el control de un único atributo de calidad (Bass et al., 2021). No prescribe la estructura completa de clases ni la orquestación del sistema.
- **Patrón:** Es una solución probada y recurrente a un problema común de diseño en un contexto dado, que típicamente combina, coordina y materializa **múltiples tácticas elementales** estableciendo una estructura concreta de componentes y relaciones.

**Ilustración con el Circuit Breaker:**  
El Circuit Breaker como patrón combina al menos tres tácticas arquitectónicas de disponibilidad:
1. *Táctica de Detección de Fallas:* Monitorea y cuenta las excepciones consecutivas o timeouts de red.
2. *Táctica de Prevención de Fallas (Falla Rápida):* Al superar el umbral, abre el circuito e intercepta las peticiones inmediatamente en memoria sin contactar al proveedor caído, evitando la saturación del pool de workers.
3. *Táctica de Recuperación:* Tras un tiempo de enfriamiento (cooldown), pasa a estado semiabierto y emite una llamada sonda controlada para evaluar si el proveedor externo se ha restablecido.

---

### 4. Describa un punto de sensibilidad y un punto de trade-off de su arquitectura, con la evidencia que los respalda.

- **Punto de Sensibilidad:**  
  *Descripción:* El percentil 95 ($p95$) de respuesta del catálogo multi-mercado a 24 req/s es extremadamente sensible a la existencia del **índice compuesto B-tree (`mercado_id, puesto_id, activo`) en PostgreSQL**.  
  *Evidencia:* En la simulación $M/G/c$ (`fitness/rendimiento.py`), si la caché se vacía o experimenta un cold start, el sistema con índice mantiene el $p95$ en **$32.4\text{ ms}$**. Sin dicho índice, el tiempo de respuesta colapsa a **$4,762.2\text{ ms}$** (degradación superior al 14,000%), superando ampliamente el presupuesto de $1,800\text{ ms}$.

- **Punto de Trade-off:**  
  *Descripción:* **Caché en memoria para catálogo (Rendimiento vs. Consistencia de datos).**  
  *Evidencia:* La caché con TTL de 30 s mejora la latencia de $32.4\text{ ms}$ a **$21.2\text{ ms}$** y reduce un 85% la carga a la base de datos. Sin embargo, empeora la frescura de los datos: durante una ventana de hasta 30 segundos, un cliente podría visualizar un producto con stock desactualizado. La decisión se aceptó mitigándola con validación estricta transaccional de stock durante la confirmación de la orden en PostgreSQL.

---

### 5. ¿Qué supuestos hizo su simulación y cómo podrían invalidar la decisión si fueran falsos?

En la simulación de rendimiento (`fitness/rendimiento.py`) se asumieron los siguientes supuestos:
1. **Llegadas según proceso de Poisson:** Las peticiones de los compradores son independientes y siguen una distribución exponencial de tiempos entre llegadas con tasa $\lambda = 24\text{ req/s}$.
2. **Tiempos de servicio lognormales:** Las consultas a la BD y a la caché siguen una distribución lognormal calibrada ($\mu = -4.01, \sigma = 0.35$ para BD indexada; $\sim 2.5\text{ ms}$ para aciertos de caché).
3. **Tasa de aciertos de caché del 85%:** Se asume que la mayoría de compradores consultan los mismos puestos y productos destacados de los 3 mercados.

**¿Cómo se invalidaría la decisión si fueran falsos?**  
Si los patrones de acceso fueran de dispersión uniforme pura (cada usuario busca un producto completamente distinto en un catálogo de miles de ítems), la tasa de aciertos de la caché caería por debajo del 20%. Aunque la simulación demostró que el índice en BD resiste hasta 24 req/s en $32.4\text{ ms}$, si la concurrencia real creciera a más de 100 req/s con caché inefectiva, los 4 workers de Python se agotarían por saturación de CPU/disco, invalidando la permanencia en un solo VPS y forzando a escalar a múltiples réplicas o sharding de base de datos.

---

### 6. ¿Qué riesgo de la evaluación cruzada aceptaron sin mitigarlo y por qué es razonable para un plazo de 1 mes?

- **Riesgo aceptado:** **Riesgo R1 (Un solo servidor VPS como punto único de falla / SPOF).**
- **Por qué es razonable para 1 mes:**  
  Construir una infraestructura de alta disponibilidad multi-zona con réplicas activas-pasivas de base de datos, balanceadores redundantes (HAProxy/Keepalived) y failover automático exige licencias cloud de pago o múltiples instancias que violan de forma frontal la restricción presupuestaria de **$0 USD/mes (R-03)** y requeriría al menos 3 semanas adicionales de devops que amenazan el plazo de entrega de **1 mes (R-01)**.  
  Para la etapa piloto de 3 mercados, el riesgo de indisponibilidad física del VPS es de baja probabilidad ($< 0.5\%$ en proveedores modernos) y se mitiga de manera pragmática mediante respaldos automatizados diarios hacia almacenamiento externo y un procedimiento documentado de restauración en $< 2\text{ horas}$.

---

### 7. Explique qué es una fitness function y qué degradación concreta de su arquitectura detectaría cada una de las suyas.

Una **fitness function** (Ford, Parsons, Kua y Sadalage, 2022) es una prueba automatizada ejecutada en el pipeline de Integración Continua (CI) que evalúa y preserva características arquitectónicas del sistema (integridad modular, rendimiento, disponibilidad, seguridad) frente al deterioro gradual del código.

**Degradaciones detectadas por nuestras fitness functions:**
1. **`FF-01 (Capas sin ciclos en import-linter)`:** Detecta dependencias circulares o atajos entre capas del monolito modular (e.g., si el módulo de reportes intenta invocar directamente detalles de bajo nivel de pedidos).
2. **`FF-02 (Aislamiento de puertos en import-linter)`:** Detecta violaciones al principio de inversión de dependencias (DIP) y arquitectura hexagonal si el dominio o los servicios importan directamente adaptadores de SDKs externas (`pedidos.externos`).
3. **`FF-03 (Presupuesto de latencia p95 <= 1800 ms en pytest)`:** Detecta si un desarrollador elimina un índice, introduce consultas $N+1$ o desactiva la caché, haciendo que el tiempo de respuesta a 24 req/s exceda el presupuesto.
4. **`FF-04 (Aislamiento multitenancy 100% en pytest)`:** Detecta si una modificación en las políticas SQL o en los endpoints de pedidos omite el filtro `mercado_id` y expone datos entre mercados competidores.
5. **`FF-05 / FF-06 (0 pedidos perdidos y protección de Circuit Breaker en pytest)`:** Detecta si alguien retira el patrón Outbox o altera la lógica del Circuit Breaker, reintroduciendo pérdidas de pagos o estampidas hacia proveedores caídos.

---

### 8. ¿Qué propuesta de la IA rechazaron con evidencia? ¿Qué habría pasado si la aceptaban sin medir?

- **Propuesta rechazada:**  
  La IA propuso inicialmente que *"la adición de Altiplano y Río Seco obligaba a migrar la arquitectura hacia microservicios independientes orquestados en Kubernetes con una base de datos PostgreSQL separada por cada mercado"*. Asimismo, en la capa de persistencia de pagos diferidos sugirió almacenar la cola de pagos pendientes en una lista volátil de **Redis en memoria**.

- **¿Qué habría pasado si se aceptaba sin medir?**  
  1. **Fracaso del proyecto por plazo y costo:** Montar Kubernetes y 3 bases de datos en contenedores independientes sobre un VPS de 1 GB RAM habría provocado fallos continuos por falta de memoria (*Out of Memory - OOM Killer*), violando la restricción presupuestaria de $0 USD/mes (**R-03**) e impidiendo entregar el sistema en el plazo estricto de 1 mes (**R-01**). La simulación $M/G/c$ demostró con evidencia cuantitativa que el Monolito Modular responde en solo **$21.2\text{ ms}$**, haciendo totalmente innecesaria la complejidad de microservicios.
  2. **Pérdida de dinero y pedidos reales:** Si se adoptaba la cola volátil en Redis sin persistencia transaccional ACID, ante cualquier reinicio imprevisto del servicio o del servidor durante una caída de red, todos los comprobantes de transferencias Yape encolados se habrían borrado permanentemente, provocando reclamos comerciales severos y pérdidas económicas para los comerciantes de los mercados. La adopción fundamentada de la tabla transaccional `outbox` en PostgreSQL garantizó **cero pedidos perdidos**.

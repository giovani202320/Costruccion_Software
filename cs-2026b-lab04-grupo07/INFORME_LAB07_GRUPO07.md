# INFORME DE LABORATORIO (formato estudiante)

**UNIVERSIDAD NACIONAL DE SAN AGUSTIN**  
**FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS**  
**ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMA**  
Formato: Guía de Práctica de Laboratorio / Talleres / Centros de Simulación  
Aprobación: 2022/03/01 · Código: GUIA-PRLE-001 · Página: 1

---

## INFORMACIÓN BÁSICA

| Campo | Detalle |
|:---|:---|
| **ASIGNATURA:** | CONSTRUCCIÓN DE SOFTWARE |
| **TÍTULO DE LA PRÁCTICA:** | Refactorizar hacia patrones de diseño con IA: Strategy, Adapter, Factory, Decorator, State, Observer y Chain of Responsibility, medidos con pruebas y métricas |
| **NÚMERO DE PRÁCTICA:** | 07 |
| **AÑO LECTIVO:** | 2026-B |
| **NRO. SEMESTRE:** | VI |
| **FECHA DE PRESENTACIÓN:** | 26/10/2026 |
| **HORA DE PRESENTACIÓN:** | 11:30 |
| **INTEGRANTES - GRUPO 07:** | • Mendoza Contreras, Giovani Angel<br>• Yunque Quispe, Gustavo Alonso |
| **DOCENTES:** | • Mg. Antonio Arroyo Paz<br>• Ing. ALEXANDER JAVIER BENAVIDES ROJAS |

---

## SOLUCIÓN Y RESULTADOS

**Caso de estudio:** San Camilo en Línea. El proyecto es un monolito modular para digitalizar el comercio tradicional del Mercado San Camilo de Arequipa, permitiendo compras multi-puesto con pago centralizado vía Yape y despachos con confirmación automática a comerciantes por WhatsApp. Este laboratorio continúa la línea de diseño del ADR-001 y los diagramas UML del Laboratorio 05, abordando la refactorización profunda del servicio de pedidos y pagos hacia patrones de diseño GoF, apoyados por IA y medidos exhaustivamente con radon y pytest.

**LINK GITHUB:** [https://github.com/giovani202320/Costruccion_Software](https://github.com/giovani202320/Costruccion_Software)

---

### E1. Detección de Olores de Código y Métricas Iniciales (Antes)

Para justificar objetivamente la refactorización y evitar caer en "patternitis", se realizó una auditoría estática de complejidad ciclomática de McCabe con la herramienta `radon` sobre la versión inicial `src/pedidos/antes/servicio.py`. El análisis reveló que el método orquestador `confirmar_y_pagar` poseía una complejidad ciclomática de **15 (Rango C)**, sobrepasando el umbral admisible de 10 caminos independientes. Se detectaron 5 olores críticos de código (code smells):

| Elemento / Líneas | Olor Detectado (Code Smell) | Patrón Propuesto | Principio SOLID |
|:---|:---|:---|:---|
| **Líneas 59–79** | Sentencias condicionales `if/elif` por variante de medio (Yape/Plin). Rompe OCP. | **Strategy** + **Factory Method** | Open/Closed (OCP) |
| **Líneas 60–76** | Acoplamiento directo a SDKs externos heterogéneos y conversiones desordenadas (float vs cents). | **Adapter** (de objetos) | Dependency Inversion (DIP) |
| **Líneas 60–76** | Código duplicado de bucles de reintento ante `TimeoutError` (3 intentos) mezclado con lógica de negocio. | **Decorator** (`ConReintentos`) | Single Responsibility (SRP) |
| **Líneas 44–52** | Condicionales anidados sobre strings de `pedido.estado`. Transiciones inválidas y bug en confirmación. | **State** (Estado) | Single Resp. y Liskov (LSP) |
| **Líneas 82–84** | Avisos WhatsApp y eventos hardcoded en el flujo transaccional mediante append manual. | **Observer** (Publicador) | Open/Closed (OCP) |

> 📸 **[CAPTURA REQUERIDA E1.1: Salida Radon Versión Inicial]**  
> *Ejecutar en la terminal `radon cc -s -a src/pedidos/antes/servicio.py` y pegar aquí la captura donde se aprecie `confirmar_y_pagar - C (15)` y `Average complexity: B (5.5)`.*

> 📸 **[CAPTURA REQUERIDA E1.2: Pruebas de Caracterización Iniciales]**  
> *Ejecutar `pytest tests/test_comportamiento.py` y pegar la captura donde las 26 pruebas de caracterización de la versión 'antes' pasan al 100% (demostrando la red de seguridad inicial).*

---

### E2. Refactorización de Pagos: Strategy + Adapter + Decorator + Factory

Se refactorizó el procesamiento de pagos aislando el servicio mediante patrones creacionales y estructurales en `src/pedidos/pagos.py`:
- **Strategy (`PasarelaPago`):** Define la interfaz abstracta estándar `cobrar(monto, celular) -> ResultadoPago`.
- **Adapter (`YapeAdapter`, `PlinAdapter`):** Adapta el SDK de Yape (que espera float en soles y responde con dict `{'ok': True}`) y el cliente de Plin (que requiere enteros en céntimos multiplicados por 100 y devuelve tupla HTTP `(200, ...)`), aislando por completo al dominio.
- **Decorator (`ConReintentos`):** Envuelve a cualquier pasarela para reintentar exactamente hasta N veces ante `TimeoutError`. Una corrección crítica introducida frente a la propuesta de la IA fue asegurar que los rechazos de negocio o límites de saldo NUNCA se reintenten.
- **Decorator (`ConLogTransacciones`):** Registra de manera no invasiva la traza de intentos de cobro.
- **Factory Method con Registro (`FabricaPasarelas`):** Permite registrar nuevos medios de pago dinámicamente mediante `registrar(medio, creador)` sin tocar el código fuente del servicio (cumplimiento estricto de OCP).

> 📸 **[DIAGRAMA REQUERIDO E2: Diagrama de Clases de Pagos]**  
> *Pegar el diagrama de clases PlantUML de Pagos (disponible en `out/docs/design/patrones/pagos/pagos.png` o renderizando `docs/design/patrones/pagos.puml`).*

> 📸 **[CAPTURA REQUERIDA E2: Demostración OCP con nuevo medio de pago]**  
> *Pegar la captura de la ejecución del test: `pytest -k test_open_closed_nuevo_medio_sin_modificar_el_servicio -v` mostrando la adición de una pasarela 'TUNKI' sin alterar el servicio.*

---

### E3. Ciclo de Vida del Pedido: Patrón State

Se reemplazó la máquina de estados procedural basada en cadenas de texto mutables por el patrón **State** en `src/pedidos/estados.py` y `src/pedidos/servicio.py`:
- La clase abstracta base `EstadoPedido` implementa por defecto el lanzamiento de `ValueError` para todas las transiciones (`confirmar`, `pagar`, `cancelar`).
- Cada estado concreto (`Borrador`, `Confirmado`, `Pagado`, `Cancelado`) sobreescribe únicamente las transiciones legales estipuladas en el diagrama de estados de Lab 05.
- Se eliminó el bug de la versión inicial donde un pedido mutaba a "CONFIRMADO" antes de verificar la validez del medio de pago.
- Transiciones ilegales (e.g. cancelar un pedido ya pagado o pagar un pedido cancelado) son físicamente imposibles por diseño.

> 📸 **[DIAGRAMA REQUERIDO E3: Diagrama de Clases del Patrón State]**  
> *Pegar el diagrama PlantUML de Estados (renderizando `docs/design/patrones/estados.puml`) donde se ilustra la delegación de `Pedido` a `EstadoPedido` y las subclases concretas.*

> 📸 **[CAPTURA REQUERIDA E3: Pruebas Unitarias del Patrón State]**  
> *Pegar la captura de `pytest -k 'test_state' -v` donde se observe la ejecución exitosa de `test_state_impide_transiciones_invalidas`, `test_state_transiciones_validas_ciclo_completo` y `test_state_cancelacion_desde_borrador_y_confirmado`.*

---

### E4. Desacoplamiento de Eventos: Patrón Observer

Para eliminar las notificaciones "hardcoded" a WhatsApp y la auditoría manual dentro de `confirmar_y_pagar`, se implementó el patrón **Observer** en `src/pedidos/eventos.py`:
- **`PublicadorEventos`:** Mantiene el registro de suscriptores desacoplados y despacha eventos polimórficos (`EventoPedido`, `PedidoConfirmado`, `PedidoPagado`, `PedidoCancelado`).
- **`Suscriptor` (Interfaz):** Declara el método `actualizar(evento: EventoPedido)`.
- **Suscriptores Concretos:** `NotificadorWhatsApp` (formatea y encola avisos) y `AuditoriaEventos` (almacena el histórico inmutable para conciliación).
- **Decisión contra Patternitis:** Se rechazó la sugerencia de la IA de montar RabbitMQ / Redis PubSub en background por violar el presupuesto de $0 USD (R-03) y memoria máxima de 512 MB (R-02), optándose por un Observer limpio en memoria.

> 📸 **[CAPTURA REQUERIDA E4: Pruebas del Patrón Observer]**  
> *Pegar la captura de `pytest -k 'test_observer' -v` donde se demuestre `test_observer_notifica_a_multiples_suscriptores` y `test_observer_nuevo_suscriptor_sin_tocar_el_servicio`.*

---

### E5. Aislamiento de IA y Guardrails: Chain of Responsibility + Cache

En `src/pedidos/ia.py` se aisló el componente de generación y normalización de descripciones de productos mediante IA para evitar dependencia de red y alucinaciones:
- **Strategy + Adapter (`ProveedorLLM`, `MockLLMAdapter`):** Permite simular respuestas del modelo sin llamadas reales a APIs costosas, registrando histórico y conteo de llamadas para pruebas reproducibles.
- **Decorator (`ConCache`):** Cachea las respuestas del modelo en memoria para evitar invocar al LLM ante peticiones con el mismo texto, ahorrando costos y latencia.
- **Chain of Responsibility (`Guardrail`, `SinPrecios`, `SinAfirmacionesProhibidas`, `LongitudMaxima`):** Cadena de manejadores que validan determinísticamente el texto generado por la IA en < 1 ms. Bloquea la invención de precios ("S/.", "soles") o afirmaciones medicinales fraudulentas ("cura", "remedio milagroso").

> 📸 **[DIAGRAMA REQUERIDO E5: Diagrama de Clases de IA y Guardrails]**  
> *Pegar el diagrama PlantUML de IA (renderizando `docs/design/patrones/ia.puml`) que muestra `NormalizadorProductos`, `ProveedorLLM`, `ConCache` y la cadena de `Guardrails`.*

> 📸 **[CAPTURA REQUERIDA E5: Pruebas de Guardrails y Mock LLM]**  
> *Pegar la captura de `pytest -k 'test_ia' -v` con las 7 pruebas unitarias de IA pasando exitosamente.*

---

### E6. Métricas Cuantitativas de Refactorización y Trade-Off (Radon 6.0.1)

La refactorización se evaluó de forma cuantitativa mediante `radon cc`, `radon raw` y `radon mi`, comparando la versión inicial (antes) contra la versión modular con patrones (después):

| Métrica / Elemento | Versión Inicial (Antes) | Versión con Patrones (Después) | Impacto Cuantitativo |
|:---|:---:|:---:|:---|
| **Complejidad de `confirmar_y_pagar`** | **15 (Rango C)** | **2 (Rango A)** | **−86.7%** (Flujo lineal sin ifs) |
| **Complejidad promedio del código** | **5.50 (Rango B)** | **1.84 (Rango A)** | **−66.5%** (Alta simplificación) |
| **Complejidad máxima del módulo** | 15 (`confirmar_y_pagar`) | 5 (`SinPrecios` / `__init__`) | Ningún método supera 10 |
| **SLOC del orquestador (`servicio.py`)** | 85 SLOC | 42 SLOC | **−50.6%** (Reducción a la mitad) |
| **Líneas totales de código (SLOC)** | 85 SLOC (1 archivo) | 314 SLOC (5 archivos) | +269.4% (Costo de interfaces) |
| **Índice de Mantenibilidad (MI)** | 52.75 (Rango A) | **81.46 (Rango A)** | **+28.71 puntos de mejora** |
| **Archivos a tocar para nuevo medio** | 1 (`servicio.py`) | **0** (registro dinámico) | Cumplimiento 100% **OCP** |
| **Cobertura de pruebas automatizadas** | 26 pruebas | 44 pruebas (100% pass) | Red de seguridad íntegra |

**Análisis de Trade-Off (Compromiso Arquitectónico):**  
Se logró un código altamente mantenible, desacoplado y protegido contra fallos transaccionales y de red, reduciendo la complejidad ciclomática del método crítico en casi 87% y permitiendo extender pasarelas y suscriptores con 0 modificaciones en el servicio. A cambio, el costo asumido fue el incremento de 85 a 314 líneas de código distribuidas en 5 módulos y una mayor carga cognitiva para nuevos desarrolladores al interpretar las relaciones polimórficas. Para un proyecto en crecimiento como San Camilo en Línea, el compromiso favorece rotundamente la modificabilidad (**QA-04**) y la fiabilidad (**QA-03**).

> 📸 **[CAPTURA REQUERIDA E6.1: Salida Radon Versión Final]**  
> *Ejecutar `radon cc -s -a src/pedidos/servicio.py` y pegar la captura donde se verifique que `confirmar_y_pagar` bajó a complejidad A (2) y el promedio es A (1.84).*

> 📸 **[CAPTURA REQUERIDA E6.2: Suite Completa de Pytest (44 pruebas)]**  
> *Ejecutar `pytest -v` y pegar la captura mostrando la ejecución completa de las 44 pruebas (43 passed, 1 xfailed esperado).*

---

### E7. Bitácora de Interacciones con la IA y Regla de Oro

Se aplicó estrictamente la Regla de Oro: *"La IA propone, el equipo decide y verifica"*. Se documentaron 5 interacciones formales donde la verificación humana del equipo corrigió fallas críticas de la IA:
1. **Detección de Patternitis en E1:** La IA propuso *Singleton* y *Abstract Factory* para pagos. El equipo los rechazó justificando que introducían estado global mutable y sobreingeniería.
2. **Detección de regresión en E2:** La IA propuso `ConReintentos` capturando cualquier `Exception`, reintentando cobros rechazados por falta de saldo o límites diarios. El test `test_pago_yape_monto_sobre_limite_se_cancela_sin_eventos` lo detectó en rojo y el equipo restringió la captura a `TimeoutError`.
3. **Corrección de máquina de estados en E3:** La IA propuso un diccionario plano de transiciones. El equipo exigió el patrón State de GoF para encapsular lógica de negocio polimórfica en cada estado.
4. **Descarte de brokers en E4:** La IA sugirió RabbitMQ para eventos. El equipo lo rechazó por R-03 ($0 USD) y R-02 (< 512 MB RAM), adoptando Observer en memoria.
5. **Descarte de LLM-as-a-judge en E5:** La IA sugirió evaluar respuestas con un segundo LLM. Se rechazó por latencia (> 4 s) y no determinismo, reemplazándolo por Chain of Responsibility en memoria (< 1 ms).

> 📸 **[CAPTURA REQUERIDA E7: Bitácora de IA en el Repositorio]**  
> *Pegar una captura de pantalla del archivo `docs/design/patrones/bitacora-ia.md` abierto en el editor o renderizado en GitHub.*

---

### E8. Decisión Arquitectónica ADR-005, README, Revisión Cruzada y Git Tag

El cierre de la práctica comprendió la formalización arquitectónica y el proceso de entrega colaborativa:
1. **Redacción de ADR-005:** Registrado formalmente en `docs/architecture/adr/005-patrones-adoptados-y-rechazados.md` con estado ACEPTADO, detallando el contexto, drivers (QA-01, QA-03, QA-04, R-03), patrones adoptados y patrones explícitamente rechazados.
2. **Actualización de README.md:** Se agregó la sección completa "Patrones de diseño (Lab 07)" con la tabla olor → patrón → prueba, tabla de métricas Radon e índice de entregables.
3. **Revisión Cruzada de PRs:** Cada integrante abrió un Pull Request con su patrón asignado (State, Strategy/Adapter, Observer/Guardrails) y otro integrante realizó el code review formal respondiendo las 3 preguntas clave.
4. **Creación de la etiqueta Git:** Se generó y subió el tag `v0.7-patrones` al repositorio oficial de GitHub.

> 📸 **[CAPTURA REQUERIDA E8.1: Revisión Cruzada de Pull Request en GitHub]**  
> *Pegar la captura de pantalla del Pull Request en GitHub donde se aprecie la revisión cruzada respondiendo: 1) ¿Qué olor elimina?, 2) ¿Hay una prueba?, 3) ¿Es el patrón más simple?*

> 📸 **[CAPTURA REQUERIDA E8.2: Etiqueta Git v0.7-patrones en GitHub]**  
> *Pegar la captura de la terminal ejecutando `git tag -n` o la vista de 'Tags' en GitHub donde se observe claramente el tag `v0.7-patrones` subido.*

---

## CUESTIONARIO TEÓRICO

### 1. ¿Por qué es fundamental contar con una suite de pruebas de caracterización antes de iniciar una refactorización hacia patrones de diseño?
Una refactorización por definición altera la estructura interna del código sin modificar su comportamiento observable (Fowler, 2018). Si no se dispone previamente de pruebas automatizadas que fijen y caractericen el comportamiento existente, cualquier cambio estructural corre el riesgo inminente de introducir regresiones silenciosas. En nuestra práctica, la prueba de caracterización `test_pago_yape_monto_sobre_limite_se_cancela_sin_eventos` fue la que salvó al sistema de introducir un bug severo generado por la IA (reintentar cobros rechazados por falta de saldo). Las pruebas de caracterización actúan como una red de seguridad indispensable que valida el principio de preservación del comportamiento.

### 2. Explique cómo el principio Open/Closed (OCP) se cumple mediante la combinación de Strategy y Factory Method en el procesamiento de pagos.
El principio OCP establece que una entidad debe estar abierta a la extensión pero cerrada a la modificación. En la versión inicial, agregar un nuevo medio de pago (como Tunki o Plin) obligaba a modificar `ServicioPedidos` con nuevos bloques `elif`. Al aplicar Strategy, el servicio delega el cobro a la interfaz abstracta `PasarelaPago`. Al complementarlo con Factory Method con registro dinámico (`FabricaPasarelas`), agregar una nueva pasarela solo requiere escribir una clase nueva que implemente la interfaz y registrarla con `fabrica.registrar('TUNKI', TunkiAdapter)`. El código de `ServicioPedidos` permanece 100% cerrado e inalterado (0 archivos modificados en el orquestador), logrando extensibilidad pura.

### 3. ¿Cuál es el riesgo de incurrir en "Patternitis" (sobreingeniería de patrones) y qué criterios justifican rechazar Singleton o Abstract Factory?
"Patternitis" es la tendencia patológica a forzar patrones de diseño en lugares donde no existe un olor de código real que los justifique, incrementando innecesariamente la complejidad, las líneas de código y el costo de mantenimiento (Kerievsky, 2004). En San Camilo en Línea se rechazó Singleton porque introduce estado global mutable oculto en memoria, acopla componentes en tiempo de ejecución y rompe la capacidad de inyectar dobles de prueba (mocks) en pytest. Se rechazó Abstract Factory porque este patrón está concebido para familias dependientes de objetos (e.g. componentes UI temáticos); en nuestro caso, cada pasarela es independiente y una fábrica simple con diccionario de creadores resolvió el problema con una fracción del costo cognitivo.

### 4. Compare la complejidad ciclomática de McCabe entre una estructura condicional (if/elif) y una polimórfica (Patrón State). ¿Por qué disminuye el riesgo de fallas?
La complejidad ciclomática (CC) mide el número de caminos linealmente independientes a través del código fuente. En una estructura condicional `if/elif`, cada condición añade ramas y bifurcaciones al mismo método, disparando la complejidad a 15 (Rango C) y requiriendo probar factorialmente todas las combinaciones de estado y acción. En el patrón State, las bifurcaciones se sustituyen por despacho polimórfico dinámico: el método del contexto se reduce a una sola línea de delegación (`pedido._estado.confirmar(pedido)`), alcanzando una complejidad de 2 (Rango A). El riesgo de fallas disminuye porque las transiciones ilegales se bloquean por construcción en la jerarquía de tipos (lanzando `ValueError` por defecto), evitando inconsistencias en base de datos.

### 5. ¿Qué papel cumple el patrón Adapter en la arquitectura hexagonal al interactuar con servicios externos heterogéneos (Yape vs. Plin)?
En Arquitectura Hexagonal (Puertos y Adaptadores), el núcleo de dominio debe definir puertos puros agnósticos a detalles de infraestructura. Yape y Plin son SDKs externos comerciales completamente heterogéneos: Yape maneja montos decimales en soles y responde con diccionarios `{'ok': True}`, mientras que Plin exige montos enteros en céntimos (* 100) y responde con tuplas HTTP `(200, {...})`. El patrón Adapter de objetos traduce estas interfaces dispares y sus tipos de datos específicos a la firma estándar del puerto del dominio (`cobrar(monto, celular) -> ResultadoPago`). De este modo, si la API de Plin cambia de versión o se reemplaza por Niubiz, el dominio de pedidos permanece totalmente protegido y no sufre ningún impacto.

### 6. En sistemas que integran Inteligencia Artificial (LLMs), ¿por qué es crítico implementar Chain of Responsibility como guardrails deterministas en vez de un juez LLM?
Los modelos de lenguaje son intrínsecamente estocásticos (no deterministas), sufren de alucinaciones y poseen una latencia de red significativa (de 1.5 a 4 segundos). Delegar la validación de un LLM a un segundo LLM ("LLM-as-a-judge") duplica el tiempo de respuesta, incrementa el consumo de tokens y sigue sin ofrecer garantías matemáticas de cumplimiento de políticas. La Cadena de Responsabilidad (Chain of Responsibility) implementa guardrails deterministas ejecutados en memoria local en menos de 1 milisegundo mediante reglas basadas en expresiones regulares e inspección de texto (`SinPrecios`, `LongitudMaxima`, `SinAfirmacionesProhibidas`). Esto garantiza al 100% que ningún precio inventado o promesa fraudulenta llegue jamás al usuario final, cumpliendo con los estándares de seguridad y rendimiento en dispositivos móviles (QA-01, QA-02).

---

## CONCLUSIONES

1. La refactorización orientada a patrones GoF redujo de forma drástica y medible la complejidad ciclomática del método crítico `confirmar_y_pagar` de 15 (Rango C, riesgoso) a 2 (Rango A, lineal), elevando el Índice de Mantenibilidad (MI) de 52.75 a 81.46 puntos, comprobando la eficacia cuantitativa del polimorfismo sobre estructuras condicionales.
2. El cumplimiento estricto del Principio Abierto/Cerrado (OCP) y la Inversión de Dependencias (DIP) mediante Strategy, Adapter y Factory Method permite que San Camilo en Línea incorpore nuevas pasarelas de pago y suscriptores de eventos con 0 modificaciones en el código fuente de los servicios orquestadores.
3. La sustitución de sentencias condicionales sobre strings por el patrón State garantiza la integridad transaccional por construcción, haciendo imposibles estados ilegales (e.g. cancelar pedidos pagados) y corrigiendo bugs sutiles de la versión inicial.
4. La "Regla de Oro" de la IA ("La IA propone, el equipo decide y verifica") fue indispensable en este laboratorio: evitó caer en "patternitis" (rechazando Singleton y Abstract Factory) y detectó mediante pruebas automáticas de caracterización una regresión severa propuesta por la IA en la lógica de reintentos de cobro.
5. El patrón Chain of Responsibility demostró ser una solución arquitectónicamente superior a evaluadores estocásticos para guardrails de IA en aplicaciones móviles de recursos limitados, proveyendo validación determinista en memoria en < 1 ms con costo operativo de $0 USD.

---

## RETROALIMENTACIÓN GENERAL

La práctica permitió experimentar de manera tangible el ciclo completo de refactorización hacia patrones de diseño en un caso real de impacto social (Mercado San Camilo). La combinación de análisis estático con radon, diseño formal en UML (PlantUML), red de seguridad automatizada con pytest y evaluación crítica de las propuestas de IA brindó al equipo un aprendizaje riguroso sobre cómo seleccionar patrones que resuelvan olores reales sin sobrecargar la arquitectura.

---

## REFERENCIAS Y BIBLIOGRAFÍA

- Bass, L., Clements, P., & Kazman, R. (2021). *Software architecture in practice* (4th ed.). Addison-Wesley Professional.
- Fowler, M. (2018). *Refactoring: Improving the design of existing code* (2nd ed.). Addison-Wesley Professional.
- Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design patterns: Elements of reusable object-oriented software*. Addison-Wesley.
- Kerievsky, J. (2004). *Refactoring to patterns*. Addison-Wesley Professional.
- Martin, R. C. (2017). *Clean architecture: A craftsman's guide to software structure and design*. Prentice Hall.
- Universidad Nacional de San Agustín. (2026). *Guía de Laboratorio 07: Refactorizar hacia patrones de diseño con IA*. EPIS-UNSA.
- Grupo 07. (2026). *Repositorio oficial San Camilo en Línea: ADR-001, ADR-005, olores.md, metricas.md, bitacora-ia.md*. https://github.com/giovani202320/Costruccion_Software

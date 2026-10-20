# Cuestionario — Laboratorio 04: Fundamentos de Arquitectura de Software

**Asignatura:** Construcción de Software · EPIS-UNSA · 2026-B  
**Caso:** San Camilo en Línea (Caso 7)  
**Grupo:** Grupo 07  

---

### 1. ¿Por qué se afirma que una decisión arquitectónica es aquella "costosa de cambiar"? Dé un ejemplo de su caso.

Una decisión arquitectónica es aquella que condiciona la estructura fundamental del sistema, su modelo de datos, la forma de comunicación entre sus partes y su estrategia de despliegue (Bass et al., 2021; ISO/IEC/IEEE 42010). Mientras que una decisión de diseño local (como cambiar un nombre de función, un algoritmo de ordenamiento o un componente visual de la UI) puede refactorizarse en pocas horas con impacto acotado, revertir una decisión arquitectónica después de haber construido sobre ella exige demoler y reescribir módulos enteros, migrar bases de datos y rehacer contratos de integración, con un costo elevadísimo en tiempo y esfuerzo.

**Ejemplo en San Camilo en Línea:**  
La selección del estilo arquitectónico: **Monolito Modular vs. Microservicios** para gestionar pedidos multi-puesto con pago unificado por Yape. Si hubiésemos optado inicialmente por microservicios, habríamos dividido las bases de datos (una por servicio), montado un broker de mensajería (Kafka/RabbitMQ) y programado el patrón Saga para transacciones distribuidas. Al toparnos con que el equipo es de solo 3 estudiantes (R-02), el plazo es de 1 mes (R-01) y el presupuesto es de $0 USD (R-03), revertir los microservicios para volver a un monolito modular habría significado desechar prácticamente todo el trabajo de infraestructura, reunificar esquemas de bases de datos y reescribir toda la capa de orquestación, perdiendo semanas irrecuperables.

---

### 2. ¿Cuál es la diferencia entre un requisito funcional y un atributo de calidad? ¿Por qué los atributos de calidad influyen más en la arquitectura?

- **Requisito Funcional (RF):** Define **qué** debe hacer el sistema: las capacidades, comportamientos, casos de uso y servicios específicos que se proporcionan al usuario final.  
  *Ejemplo en San Camilo:* **RF-02** ("El cliente puede consolidar productos de múltiples puestos en un solo carrito y generar una orden dividida por puesto").
- **Atributo de Calidad (QA):** Define **cómo de bien** o bajo qué condiciones de operación el sistema desempeña sus funciones (rendimiento, disponibilidad, usabilidad, seguridad, modificabilidad según ISO/IEC 25010:2023).  
  *Ejemplo en San Camilo:* **QA-01** ("Un comerciante con poca experiencia digital publica o confirma un producto en $\le 3$ toques desde un celular de gama baja con señal 3G").

**¿Por qué influyen más en la arquitectura?**  
Casi cualquier lenguaje, framework o estilo básico permite implementar una función de negocio (guardar un registro o calcular una suma). Sin embargo, son los atributos de calidad los que imponen compromisos estructurales (*trade-offs*) determinantes: la necesidad de interacción ágil en gama baja (**QA-01**) y baja latencia en redes 3G (**QA-02**) nos obligó a descartar llamadas HTTP remotas inter-servicio y adoptar un monolito modular con llamadas en memoria; la exigencia de 0 pedidos perdidos ante fallas de red de WhatsApp (**QA-03**) nos obligó a implementar una arquitectura hexagonal con puertos, adaptadores y colas asíncronas de reintentos. La funcionalidad es la misma, pero la arquitectura la dictan los atributos de calidad.

---

### 3. Reescriba el requisito "el sistema debe ser seguro" como un escenario de atributo de calidad de seis partes.

La frase *"el sistema debe ser seguro"* es ambigua, subjetiva y no verificable. Aplicando el marco formal de Bass, Clements y Kazman (2021) en **seis partes**, adaptado al contexto de protección de comprobantes Yape y datos personales (Ley 29733) en San Camilo en Línea:

| Parte | Pregunta | Especificación en San Camilo en Línea |
|:---|:---|:---|
| **Fuente** | ¿Quién o qué genera el estímulo? | Un atacante externo o usuario malintencionado no autenticado desde Internet. |
| **Estímulo** | ¿Qué ocurre? | Intenta interceptar datos de transferencias, falsificar códigos de operación Yape o inyectar código SQL malicioso en los endpoints de pedidos. |
| **Entorno** | ¿En qué condiciones? | Operación regular en producción, con tráfico normal y pico a través de la red pública. |
| **Artefacto** | ¿Qué parte del sistema lo recibe? | Capa de autenticación de la API REST, controladores FastAPI y capa de persistencia de pagos (`schema pagos`). |
| **Respuesta** | ¿Qué debe hacer el sistema? | El sistema bloquea las peticiones no autenticadas, valida exhaustivamente las entradas mediante esquemas tipados (Pydantic), parametriza todas las consultas SQL, cifra números celulares en reposo (AES-256) y registra el evento sospechoso en la bitácora de auditoría. |
| **Medida** | ¿Cómo se verifica? (Métrica numérica) | **0 accesos no autorizados** a datos personales; **0 brechas por inyección SQL** (100% de consultas parametrizadas); bloqueo automático de IP tras **5 intentos fallidos consecutivos** en **$\le 1$ segundo**; tiempo de revocación de sesión comprometida **$\le 500$ ms**. |

---

### 4. Compare el monolito modular y los microservicios en términos de costo, modificabilidad y complejidad operativa. ¿En qué momento convendría migrar de uno a otro?

| Criterio | Monolito Modular | Microservicios |
|:---|:---|:---|
| **Costo** | **Muy bajo:** Se compila y ejecuta en un único proceso o contenedor ligero ($< 512$ MB RAM). Compatible al 100% con planes gratuitos o VPS económicos de $\le \$5/\text{mes}$ (**R-03**). | **Alto:** Requiere múltiples contenedores, gateways, registros de servicio, brokers y múltiples bases de datos. Supera con creces el presupuesto estudiantil o de una PYME. |
| **Modificabilidad** | **Alta:** El código está organizado en contextos delimitados y módulos independientes con puertos y adaptadores. Modificar un módulo no afecta a los otros siempre que se respete la interfaz pública. | **Muy alta:** Cada servicio puede modificarse, compilarse y desplegarse independientemente, e incluso utilizar stacks tecnológicos diferentes. |
| **Complejidad operativa** | **Baja:** Un solo repositorio, un único pipeline de CI/CD, una sola instancia de base de datos relacional y monitoreo centralizado simple. | **Muy alta:** Requiere gestión de redes distribuidas, service discovery, trazabilidad distribuida (Jaeger), tolerancia a caídas parciales y transacciones eventuales (patrón Saga). |

**¿En qué momento convendría migrar de uno a otro?**  
Conviene iniciar la migración únicamente cuando se cumplan **tres condiciones simultáneas**:
1. **Cuello de botella de escalabilidad desbalanceado:** Cuando un módulo específico (por ejemplo, la consulta masiva del catálogo de productos) requiera escalar horizontalmente de forma masiva frente a los demás módulos que tienen carga baja.
2. **Crecimiento del equipo de desarrollo:** Cuando el equipo crezca a más de 10-15 desarrolladores organizados en escuadras separadas, donde coordinar un solo despliegue comience a generar cuellos de botella organizacionales.
3. **Presupuesto y madurez DevOps asegurados:** Cuando el proyecto cuente con presupuesto formal para solventar infraestructura cloud dedicada y personal especializado en operaciones.  
Dado que el monolito modular ya mantiene los límites de dominio aislados, extraer un módulo hacia un microservicio independiente es una tarea limpia y progresiva.

---

### 5. ¿Qué ventajas ofrece Diagram as Code frente a herramientas de dibujo como PowerPoint? Mencione al menos tres.

1. **Control de versiones y revisión mediante Pull Requests (Git):**  
   Al estar expresados en texto plano (`.mmd`, `.puml`, `.py`), los diagramas se versionan junto con el código fuente. Permiten ver con exactitud en un `git diff` qué componente, actor o relación fue agregada o modificada, quién fue el autor y cuál fue la justificación arquitectónica, algo inviable con archivos binarios `.pptx` o `.vsdx`.
2. **Mantenibilidad y auto-layout:**  
   Modificar la arquitectura (por ejemplo, agregar el módulo de pagos o un nuevo adaptador de WhatsApp) solo requiere editar 2 o 3 líneas de texto. La herramienta se encarga de reajustar automáticamente las posiciones, flechas y distribución geométrica, eliminando horas de reacomodo manual con el ratón.
3. **Sinergia nativa con Inteligencia Artificial y CI/CD:**  
   Los Modelos de Lenguaje (LLMs) generan, refactorizan y corrigen código textual con altísima precisión a partir de especificaciones de requerimientos. Asimismo, los diagramas pueden compilarse y renderizarse de forma automática en cada push mediante pipelines de CI (GitHub Actions) garantizando que la documentación nunca quede desfasada del código real.

---

### 6. ¿Qué elementos debe contener un ADR y por qué es importante registrar también las alternativas descartadas?

**Elementos indispensables de un ADR (según Michael Nygard e ISO 42010):**
1. **Identificador y Título:** Breve y enfocado en la decisión (ej. `ADR-001: Adoptar un monolito modular...`).
2. **Metadatos de Estado y Gobernanza:** Estado (*Propuesto*, *Aceptado*, *Rechazado*, *Superado*), fecha de decisión y nombres de los decisores.
3. **Contexto:** Motivación y fuerzas que influyen en la decisión, citando explícitamente los drivers arquitectónicos (requisitos funcionales `RF-`, atributos de calidad `QA-` y restricciones `R-`).
4. **Alternativas consideradas:** Lista de opciones evaluadas con análisis objetivo de pros y contras.
5. **Decisión:** Declaración formal en voz activa indicando qué se decidió usar y cómo se estructurará.
6. **Consecuencias:** Balance honesto de consecuencias positivas (beneficios logrados) y negativas (riesgos, deuda técnica o penalizaciones asumidas) junto con su correspondiente estrategia de mitigación.

**¿Por qué es crucial registrar las alternativas descartadas?**  
Es fundamental porque **evita que el equipo repita discusiones pasadas ("reuniones zombi")**. En proyectos de software es común que un nuevo desarrollador o interesado proponga una tecnología de moda (como microservicios o NoSQL); al consultar el ADR, queda documentada la evidencia de por qué esa alternativa ya fue evaluada y descartada (por ejemplo, por violar el plazo de 1 mes o el presupuesto cero). Además, transparenta el proceso de ingeniería demostrando que la solución adoptada no fue un capricho, sino el resultado de un análisis riguroso de compromisos.

---

### 7. Describa un caso de esta práctica en el que la IA haya generado una propuesta incorrecta o sesgada. ¿Cómo lo detectaron?

**Caso ocurrido durante el diseño de San Camilo en Línea:**
- **Propuesta incorrecta de la IA:**  
  Al solicitarle la propuesta inicial de estilos arquitectónicos para soportar pedidos multi-puesto y confirmación vía WhatsApp, el asistente de IA propuso e insistió en una arquitectura de **Microservicios con Kubernetes, broker Kafka y bases de datos NoSQL desacopladas por puesto**, argumentando que era la "mejor práctica para garantizar escalabilidad y aislamiento total". Además, en el flujo de pagos, la IA aseguró que Yape ofrecía una "API REST pública, gratuita y abierta" para microcomerciantes.
- **Cómo lo detectó el equipo:**
  1. *Frente a las restricciones del proyecto:* Se verificó matemáticamente que 300 usuarios pico en un mercado local no justifican el overhead de 5 servicios distribuidos, y que desplegar Kubernetes y Kafka viola inmediatamente la restricción presupuestaria de **$0 USD/mes** (**R-03**), la viabilidad de entrega en **1 mes** (**R-01**) y el tamaño del equipo de **3 estudiantes** (**R-02**).
  2. *Frente a la documentación real:* Al contrastar la afirmación con la documentación técnica del Banco de Crédito (BCP/Yape), se constató que no existe ninguna API pública gratuita abierta para personas naturales o puestos minoristas de mercado; la integración debía diseñarse sobre verificación por comprobante/código y URLs estructuradas de WhatsApp.
  3. *Acción tomada:* Se rechazó la propuesta de microservicios en la matriz de decisión (puntaje 2.35) y se forzó a la IA a adoptar el rol de "abogado del diablo" para criticar su propia propuesta y refinar el Monolito Modular con puertos y adaptadores.

---

### 8. ¿Qué riesgos éticos y de confidencialidad existen al usar asistentes de IA para diseñar la arquitectura de un sistema real?

1. **Fuga de información confidencial y secretos industriales:**  
   Al enviar descripciones de sistemas reales a modelos de IA basados en la nube (OpenAI, Anthropic, Google), existe el riesgo de transmitir inadvertidamente diagramas de red privados, direcciones IP, esquemas de bases de datos propietarias, llaves de API o secretos comerciales. Si estos datos no están protegidos bajo acuerdos empresariales de cero retención, pueden ser almacenados en servidores de terceros e incorporados en futuros ciclos de entrenamiento.
2. **Vulneración de la privacidad y normativas de datos (Ley N.º 29733 en Perú):**  
   Si en los prompts se incluyen datos personales o identificables de clientes, comerciantes o pacientes (números celulares, nombres, transacciones), se infringe la legislación de protección de datos personales. El diseño ético exige anonimizar y sintetizar rigurosamente cualquier dato ingresado a la IA.
3. **Falsa sensación de seguridad y dilución de responsabilidad profesional:**  
   Los modelos de IA pueden generar configuraciones o arquitecturas con fallos de seguridad sutiles (ejemplo: endpoints sin sanitización, políticas CORS excesivamente permisivas o almacenamiento inseguro de tokens). Delegar el diseño crítico sin validación humana es negligencia profesional: ante una brecha de seguridad o pérdida de fondos en producción, la responsabilidad ética y legal recae exclusivamente en los ingenieros de software colegiados y en el equipo humano, jamás en el asistente de IA.
4. **Sesgo tecnológico y exclusión de usuarios vulnerables:**  
   Las IAs tienden a recomendar soluciones sobredimensionadas basadas en el contexto de empresas tecnológicas de primer mundo (asumiendo smartphones modernos, 5G y planes de datos ilimitados). Si el arquitecto humano no ejerce una vigilancia ética crítica, diseñará sistemas inaccesibles para el usuario real (como comerciantes mayores del Mercado San Camilo con teléfonos de 2 GB de RAM), profundizando la brecha digital en lugar de resolverla.

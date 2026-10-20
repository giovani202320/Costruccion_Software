# Bitácora de uso de IA — San Camilo en Línea

Registro de interacciones, prompts, propuestas generadas, proceso de verificación humana crítica y decisiones tomadas en el diseño arquitectónico de **San Camilo en Línea** (Caso 7), de acuerdo a los lineamientos de la Guía de Laboratorio 04 (Construcción de Software, EPIS-UNSA).

---

## Registro de Interacciones

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Qué verificamos o corregimos | Decisión |
|:---:|:---:|:---|:---|:---|:---|:---:|
| **1** | 19/10 | Antigravity (Gemini 3.8 Flash) | Generación de drivers arquitectónicos y escenarios de calidad formalizados en 6 partes para San Camilo en Línea. | Estructura completa de `drivers.md` con 6 RFs, 4 QAs priorizados (usabilidad en celulares de gama baja como crítico), 4 restricciones y 3 escenarios numéricos. | Se verificó que todas las medidas fueran 100 % cuantitativas ($\le 3$ toques, p95 $\le 1.5\text{ s}$, 0 pedidos perdidos) y que las restricciones reflejaran al equipo de 3 estudiantes sin inventar supuestos. | **Aceptada** |
| **2** | 19/10 | Antigravity (Gemini 3.8 Flash) | Propuesta inicial de estilos arquitectónicos para soportar pedidos multi-puesto en San Camilo en Línea. | Sugirió una arquitectura de Microservicios orquestada con Kubernetes, colas Kafka distribuidas y bases de datos independientes por puesto. | **Alucinación de sobre-ingeniería:** Para 300 usuarios pico, 3 estudiantes y 1 mes de plazo, microservicios con Kubernetes y Kafka es inviable, consume excesiva memoria y excede el presupuesto de $0 USD/mes (**R-01, R-02, R-03**). Se descartó la orquestación distribuida. | **Rechazada** |
| **3** | 19/10 | Antigravity (Gemini 3.8 Flash) | Estrategia técnica de integración para pasarela de pagos con Yape y notificaciones por WhatsApp. | La IA afirmó que Yape ofrece una "API REST pública gratuita y abierta", y recomendó WhatsApp Business API Cloud con cobro por conversación. | **Dato inventado corregido:** Se verificó que el BCP/Yape no dispone de API REST pública gratuita para personas naturales ni pequeños comercios de mercado (requiere pasarela corporativa de pago). Asimismo, WhatsApp Cloud API genera costos recurrentes que violan **R-03**. Se corrigió a validación por código de operación/captura y URL scheme `wa.me` / webhook liviano. | **Corregida** |
| **4** | 19/10 | Antigravity (Gemini 3.8 Flash) | Diseño de matriz de decisión ponderada con 5 criterios derivados de drivers y puntajes de 1 a 5. | Matriz con pesos: Entrega (25%), Costo (20%), Interacción móvil (20%), Modificabilidad (20%) y Transaccionalidad (15%). Puntajes: Monolito modular (4.20), Monolito en capas (3.85), Microservicios (2.35). | Se revisaron los cálculos matemáticos ponderados, la consistencia con las restricciones y la justificación explícita de cada peso citando los IDs de `drivers.md`. | **Aceptada** |
| **5** | 19/10 | Antigravity (Gemini 3.8 Flash) | Elaboración del Architecture Decision Record `001-estilo-arquitectonico.md` basado en la plantilla oficial. | Borrador del ADR-001 justificando la adopción del Monolito Modular con puertos y adaptadores (Arquitectura Hexagonal interna). | Se verificó que el documento sea autocontenido, cite las restricciones **R-01** a **R-04**, exponga trade-offs reales (disciplina modular en CI con `import-linter`) y mantenga el estado "Aceptado". | **Aceptada** |
| **6** | 19/10 | Antigravity (Gemini 3.8 Flash) | Modelado de diagramas arquitectónicos: Mermaid (arquitectura elegida) y PlantUML (alternativa descartada). | Código Mermaid con capas y módulos internos; código PlantUML para microservicios con nota explicativa. Inicialmente propuso comunicación asíncrona por broker entre todos los módulos internos. | **Corrección de diseño:** En un monolito modular sobre un solo proceso, las comunicaciones síncronas entre módulos se efectúan por llamadas directas en memoria para evitar latencia adicional en celulares de gama baja (**QA-01, QA-02**); el encolado asíncrono se reserva para notificaciones externas. | **Corregida** |
| **7** | 19/10 | Antigravity (Gemini 3.8 Flash) | Script de Python Diagrams (`despliegue.py`) para la vista física de infraestructura. | Script con múltiples servidores cloud independientes para frontend, backend y broker de mensajería. | **Ajuste de presupuesto:** Se unificó el backend, la caché Redis y los esquemas PostgreSQL dentro de un único nodo de cómputo (VPS económico / tier gratuito) detrás de Nginx, garantizando la viabilidad económica bajo **R-03** ($0 a $5 USD/mes). | **Corregida** |

---

## Anexo: Prompts Completos

### Prompt 1 — Drivers y Escenarios de Calidad
```text
Actúa como arquitecto de software senior siguiendo los estándares de la Escuela Profesional de Ingeniería de Sistemas (UNSA).
Contexto: Caso 7 "San Camilo en Línea" (pedidos a los puestos del Mercado San Camilo, con recojo o delivery. Actores: cliente, comerciante, repartidor).
Funcionalidades del MVP: Catálogo por puesto; pedido a varios puestos; pago con Yape; confirmación por WhatsApp al comerciante.
Restricciones: MVP en 1 mes (R-01); equipo de 3 estudiantes con experiencia en Python (FastAPI/Django), PostgreSQL y PWA (R-02); presupuesto $0/mes (R-03); integración con Yape y WhatsApp bajo Ley 29733 (R-04).
Atributo crítico: Capacidad de interacción / usabilidad en celulares de gama baja (≤ 3 toques para publicar/confirmar).
Tarea: Genera el contenido para docs/architecture/drivers.md con mínimo 5 RFs, 4 QAs priorizados, 4 restricciones y 3 escenarios de calidad en formato formal de 6 partes con medidas numéricas verificables (sin adjetivos ambiguos).
```

### Prompt 2 — Exploración de Estilos y Crítica Adversarial
```text
Propón 3 alternativas de estilo arquitectónico para el caso San Camilo en Línea considerando las restricciones de 1 mes y equipo de 3 estudiantes.
[Respuesta inicial de IA propuso Microservicios con Kubernetes y Kafka]
Crítica adversarial (Abogado del diablo):
Actúa como arquitecto crítico. Cuestiona la viabilidad técnica y económica de desplegar microservicios con Kubernetes y Kafka para un MVP universitario de 1 mes con presupuesto cero. ¿Por qué viola las restricciones R-01, R-02 y R-03? Plantea una comparación realista frente al Monolito Modular y al Monolito en Capas.
```

### Prompt 3 — Verificación de Integraciones Externas (Yape / WhatsApp)
```text
¿Es posible consumir directamente una API REST oficial y gratuita de Yape para validar transacciones de puestos del mercado? ¿Qué costos involucra WhatsApp Business Cloud API y cómo podemos cumplir el requisito de confirmación a los comerciantes manteniendo el presupuesto en $0 USD/mes?
```

### Prompt 4 — Matriz de Decisión Ponderada
```text
Genera docs/architecture/matriz-decision.md comparando Monolito en capas, Microservicios y Monolito modular.
Define 5 criterios de evaluación cuyos pesos sumen 100%, justificando cada uno con los IDs de drivers.md (R-01, R-02, R-03, QA-01, QA-02, QA-03, QA-04).
Asigna puntajes de 1 a 5, muestra la suma ponderada explícita y concluye con la justificación del estilo ganador para el MVP.
```

### Prompt 5 — Redacción del ADR-001
```text
Genera docs/architecture/adr/001-estilo-arquitectonico.md usando la plantilla estándar de Nygard/docente.
Decisión: Adoptar un Monolito Modular para el MVP de San Camilo en Línea.
Incluye contexto con citas a drivers.md, alternativas consideradas con sus puntajes de la matriz, decisión en voz activa ("Usaremos...") y consecuencias positivas y negativas/riesgos con su correspondiente táctica de mitigación.
```

### Prompt 6 — Modelado Mermaid y PlantUML
```text
Genera el diagrama Mermaid (arquitectura.mmd) del monolito modular con los actores (Cliente, Comerciante, Repartidor, Admin), la PWA móvil, los 5 módulos de dominio, la capa de infraestructura hexagonal, PostgreSQL y las integraciones externas (Yape, WhatsApp).
Luego genera en PlantUML (alternativa-microservicios.puml) el diagrama de la alternativa descartada de microservicios con nota explicativa de 3 a 5 líneas citando el puntaje de la matriz.
```

### Prompt 7 — Vista de Despliegue con Python Diagrams
```text
Elabora el script de infraestructura en Python utilizando la librería diagrams (despliegue.py) para modelar el despliegue físico de San Camilo en Línea: usuarios con celular PWA, proxy Nginx, servidor VPS contenedorizando el monolito FastAPI, PostgreSQL, Redis para caché y Celery para reintentos asíncronos de WhatsApp. Asegura compatibilidad con el presupuesto cero.
```

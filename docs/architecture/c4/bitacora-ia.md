# Bitácora de uso responsable de IA - Lab 06

| Fecha | Herramienta | Solicitud / actividad | Propuesta o resultado | Verificación humana | Decisión |
|---|---|---|---|---|---|
| 2026-10-20 | Codex | Inventariar elementos C4 desde drivers, ADR y UML. | Personas, sistemas externos, cinco contenedores y cinco módulos de la API. | Se contrastó cada elemento con ADR-001, ADR-003 y `paquetes.puml`. | Aceptado; se creó `inventario.md`. |
| 2026-10-20 | Codex | Borrador de `workspace.dsl` con cinco vistas. | Monolito modular, PWA, API, worker, PostgreSQL, Redis y componentes de dominio. | Se comprobó que Docker Compose fuera nodo de despliegue, no contenedor C4. | Aceptado con esa corrección. |
| 2026-10-20 | Codex | Modelar pagos y mensajería externos. | Inicialmente se propuso WhatsApp Business API como integración HTTP genérica. | ADR-003 indica que el MVP no contrata la API Cloud; usa `wa.me`, comprobantes Yape/Plin y conciliación manual. | Corregido a `WhatsApp Business API / wa.me` con protocolo HTTPS (`wa.me`). |
| 2026-10-20 | Structurizr CLI | Validar el modelo DSL. | La primera revisión detectó el selector inválido `sanCamilo.api.*` en la vista de componentes. | Se reemplazó por los cinco identificadores explícitos de componentes. | Corregido; validación final exitosa. |
| 2026-10-20 | PlantUML | Renderizar las cinco vistas exportadas. | La primera vista de componentes incluía relaciones de la PWA que superponían etiquetas. | Se revisó la imagen; el ruido no aportaba al alcance del nivel 3. | Corregido: la vista incluye los componentes y sus dependencias PostgreSQL/Redis. |
| 2026-10-20 | Codex | Auditoría C4 y explicación no técnica. | Se propusieron criterios de revisión y un resumen para público no técnico. | Se limitó la explicación a hechos presentes en el modelo y a menos de 120 palabras. | Aceptado; se crearon `revision-c4.md` y `explicacion.md`. |

## Prompts completos usados

### Prompt IA 1 - Borrador del modelo

> Actúa como arquitecto de software experto en el modelo C4 y en Structurizr DSL. Usa el inventario de `docs/architecture/c4/inventario.md`, el ADR-001, el ADR-002, el ADR-003 y los diagramas del Laboratorio 05 de San Camilo en Línea. Genera un único `workspace.dsl` con `!identifiers hierarchical`, cuatro personas, el sistema propio, Yape/Plin y WhatsApp como sistemas externos etiquetados “Externo”, y los contenedores PWA, API, worker, PostgreSQL y Redis. Desglosa la API en los cinco componentes Catálogo, Pedidos, Pagos, Notificaciones y Usuarios. Incluye relaciones con verbos claros y protocolos HTTPS/JSON, SQL/TCP y Redis protocol; define las vistas `systemContext`, `container`, `component`, `dynamic` para confirmar y pagar con Yape y `deployment` para Producción. No inventes Kafka, Kubernetes ni APIs pagadas que contradigan los ADR. Docker Compose debe aparecer solo como nodo de despliegue.

### Prompt IA 2 - Auditor C4

> Actúa como revisor de diagramas de arquitectura. Evalúa las cinco vistas exportadas de `docs/architecture/c4/workspace.dsl` con la lista de revisión oficial de C4: título y alcance, leyenda, tipo y responsabilidad de cada elemento, tecnologías, intención y dirección de cada relación, y protocolos cuando correspondan. Responde por vista con cumple sí/no, evidencia y corrección sugerida. No inventes problemas; identifica al menos un falso positivo y verifícalo contra los ADR y `docs/design/paquetes.puml`.

### Prompt IA 3 - Explicación para público no técnico

> Explica el diagrama de contexto de San Camilo en Línea para una persona no técnica en un máximo de 120 palabras. Indica quién usa el sistema, qué permite hacer, de qué sistemas externos depende y cómo se evita perder pedidos cuando falla WhatsApp. Usa únicamente elementos presentes en `workspace.dsl`; evita jerga de arquitectura y no afirmes que existe una API pública gratuita de Yape ni una integración Cloud de WhatsApp contratada.

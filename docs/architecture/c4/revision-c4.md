# Revisión C4 - San Camilo en Línea

Revisión aplicada a las vistas exportadas desde `workspace.dsl`, usando la lista de verificación de la guía: claridad general, elementos identificables y relaciones con intención y tecnología/protocolo.

| Vista | Pregunta de revisión | Cumple | Evidencia | Corrección aplicada o decisión |
|---|---|:---:|---|---|
| Contexto | ¿Tiene título, alcance, personas, sistema y sistemas externos identificables? | Sí | `structurizr-systemContext.png` muestra Cliente, Comerciante, Repartidor, Administrador, Yape/Plin, WhatsApp y San Camilo en Línea. | Se mantuvieron solo relaciones de negocio; no se muestran tecnologías internas. |
| Contenedores | ¿Cada contenedor tiene responsabilidad, tecnología y relaciones con protocolo? | Sí | PWA, API, Worker, PostgreSQL y Redis muestran tecnología; las flechas indican HTTPS/JSON, SQL/TCP o Redis protocol. | Docker Compose no se modeló como contenedor; se reservó para despliegue. |
| Componentes | ¿Los componentes corresponden al diseño UML y no presentan ciclos? | Sí | Catálogo, Pedidos, Pagos, Notificaciones y Usuarios coinciden con `design/paquetes.puml`; las dependencias salen de Pedidos hacia interfaces públicas. | La vista se limitó a componentes, PostgreSQL y Redis para evitar ruido visual. |
| Dinámica | ¿El flujo crítico usa relaciones existentes y pasos numerados? | Sí | `structurizr-confirmarYape.png` muestra 10 pasos, desde el envío del comprobante hasta el aviso asíncrono. | La persistencia del pedido ocurre antes de notificar, preservando QA-03. |
| Despliegue | ¿Incluye instancias de todos los contenedores y nodos anidados coherentes con el presupuesto? | Sí | La PWA se ejecuta en el dispositivo del usuario; API, Worker, PostgreSQL y Redis en Docker Compose dentro de un VPS. | VPS único de bajo costo, coherente con R-03. |

## Revisión crítica de la IA

| Hallazgo propuesto por IA | Verificación humana | Decisión |
|---|---|---|
| “WhatsApp Business API debe conectarse por HTTPS/JSON desde la API.” | Es un falso positivo para este MVP: ADR-003 descarta contratar la API Cloud y define enlaces `wa.me` y un worker con Redis para reintentos. | Rechazado. Se conserva `HTTPS (wa.me)` y la descripción explícita del límite del MVP. |
| “Docker Compose debe ser un contenedor de San Camilo en Línea.” | Docker Compose no es un contenedor C4; es infraestructura que aloja instancias de contenedores. | Rechazado. Se representa únicamente como nodo de despliegue. |
| “La vista de componentes debe mostrar los mensajes de todos los perfiles de la PWA.” | La exportación inicial quedó visualmente sobrecargada; el objetivo de nivel 3 es explicar los módulos de la API. | Aceptado parcialmente: se limitó la vista a componentes y sus dependencias de datos/cola. |

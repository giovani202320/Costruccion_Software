# Inventario C4 - San Camilo en Línea

Este inventario es la fuente de trazabilidad para el modelo C4 del Laboratorio 06. Un **contenedor** es una unidad que se ejecuta o despliega por separado; no equivale a un contenedor Docker.

| Elemento | Tipo C4 | Responsabilidad / descripción | Tecnología o protocolo relevante | Origen y coherencia |
|---|---|---|---|---|
| Cliente | Persona | Explora catálogos, arma el carrito multi-puesto, transfiere por Yape/Plin y consulta el estado del pedido. | Navegador móvil / HTTPS | `drivers.md` (RF-01 a RF-03), `design/historia.md` (HU-01) |
| Comerciante | Persona | Publica productos, actualiza disponibilidad y prepara la suborden recibida. | Navegador móvil y WhatsApp | `drivers.md` (RF-01, RF-04, RF-05), ADR-001 |
| Repartidor | Persona | Consulta pedidos con modalidad delivery y confirma la entrega consolidada. | Navegador móvil / HTTPS | `drivers.md` (RF-06), `design/historia.md` |
| Administrador | Persona | Verifica comprobantes Yape/Plin y supervisa el funcionamiento de la plataforma. | Navegador web / HTTPS | `drivers.md` (RF-03), ADR-003 |
| San Camilo en Línea | Sistema de software | Plataforma propia que digitaliza el catálogo, compra, pago y coordinación de pedidos del Mercado San Camilo. | PWA + API REST | `README.md`, ADR-001 |
| Yape / Plin | Sistema externo | Billeteras desde las que el cliente realiza la transferencia; en el MVP la conciliación se registra y verifica de forma manual. | App o web externa; comprobante y código de operación | `drivers.md` (R-04), ADR-003 |
| WhatsApp Business API / `wa.me` | Sistema externo | Canal habitual del comerciante para recibir el detalle de su suborden mediante enlace `wa.me`; el MVP no presupone contratar la API Cloud de pago. | HTTPS (`wa.me`) | `drivers.md` (RF-04, R-04), ADR-003 |
| PWA móvil | Contenedor | Interfaz instalable y responsiva para los cuatro perfiles, optimizada para celulares Android básicos y conectividad intermitente. | HTML5, TailwindCSS, JavaScript, Service Worker | ADR-001, `drivers.md` (QA-01, QA-02) |
| API San Camilo | Contenedor | Monolito modular que publica casos de uso REST y coordina los módulos de dominio. | Python, FastAPI o Django, REST/JSON | ADR-001 |
| Worker de notificaciones | Contenedor | Consume avisos pendientes y reintenta su entrega sin bloquear la respuesta del pedido. | Celery | ADR-003 (CeleryWhatsAppWorker) |
| PostgreSQL | Contenedor | Persistencia ACID única, con esquemas lógicos aislados para `catalogo`, `pedidos`, `pagos`, `notificaciones` y `usuarios`. | PostgreSQL 15+ / SQL sobre TCP | ADR-002, ADR-001 |
| Redis | Contenedor | Caché de catálogo y cola de tareas de notificación. | Redis protocol | `README.md`, ADR-003 |
| Módulo Catálogo | Componente de API | Gestiona puestos, productos, precios, disponibilidad y reserva de stock mediante su interfaz pública. | Módulo Python | ADR-001, `design/paquetes.puml`, `design/clases.puml` |
| Módulo Pedidos | Componente de API | Orquesta carrito multi-puesto, pedido consolidado, subórdenes y ciclo de estados. | Módulo Python | ADR-001, `design/paquetes.puml`, `src/pedidos/dominio.py` |
| Módulo Pagos | Componente de API | Registra comprobantes y expone el puerto de validación de pagos, desacoplado de Yape/Plin. | Módulo Python / puerto-adaptador | ADR-001, ADR-003, `design/paquetes.puml` |
| Módulo Notificaciones | Componente de API | Formatea avisos por puesto y los encola para su despacho asíncrono. | Módulo Python / puerto-adaptador | ADR-001, ADR-003, `design/paquetes.puml` |
| Módulo Usuarios | Componente de API | Gestiona autenticación y perfiles de cliente, comerciante, repartidor y administrador. | Módulo Python | ADR-001, ADR-002 |

## Decisiones de modelado

- Los cinco componentes corresponden exactamente a los cinco módulos de dominio del ADR-001. `compartido` del diagrama de paquetes es una biblioteca transversal, no un sexto componente de negocio.
- Yape/Plin y WhatsApp son sistemas externos: no se despliegan dentro de San Camilo en Línea.
- Docker Compose es infraestructura del despliegue, no un contenedor C4. Se muestra únicamente como nodo de la vista de despliegue.
- La relación con Yape/Plin no inventa una API bancaria pública: el sistema recibe el código de operación y el comprobante que registra el cliente, y el administrador lo verifica.

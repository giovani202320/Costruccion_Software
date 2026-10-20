# Drivers arquitectónicos — San Camilo en Línea

Documento de especificación de drivers arquitectónicos (requisitos funcionales clave, atributos de calidad, restricciones y escenarios de calidad en formato de seis partes) para la plataforma **San Camilo en Línea** (Caso 7), correspondiente a la Guía de Laboratorio 04 de Construcción de Software (EPIS-UNSA).

---

## 1. Requisitos funcionales clave

| ID | Requisito | Actor | Prioridad |
|:---|:---|:---|:---|
| **RF-01** | **Catálogo individual por puesto:** El sistema permite listar, categorizar y visualizar el catálogo independiente de cada puesto comercial del Mercado San Camilo (frutas, verduras, abarrotes, carnes, jugos y comidas) con fotografías comprimidas, precios unitarios y estado de disponibilidad en tiempo real. | Cliente / Comerciante | Alta |
| **RF-02** | **Carrito y pedidos multi-puesto consolidado:** El cliente puede agregar productos de diferentes puestos comerciales en un único carrito de compras y generar un pedido consolidado, el cual el sistema divide automáticamente en órdenes individuales por puesto comercial. | Cliente | Alta |
| **RF-03** | **Registro y validación de pago con Yape:** El cliente registra el pago del pedido consolidado mediante transferencia Yape (ingreso del número de operación y captura del comprobante), asociando el abono al pedido total para su verificación administrativa. | Cliente / Administrador | Alta |
| **RF-04** | **Confirmación y notificación por WhatsApp:** El sistema genera y despacha notificaciones automáticas con el formato estructurado de cada pedido al WhatsApp del comerciante correspondiente para su preparación inmediata, permitiendo confirmar la aceptación o disponibilidad de los productos. | Comerciante / Sistema | Alta |
| **RF-05** | **Publicación y gestión ágil de productos:** El comerciante puede crear nuevos productos, modificar precios diarios y activar/desactivar stock mediante una interfaz simplificada optimizada para dispositivos móviles de gama baja. | Comerciante | Alta |
| **RF-06** | **Modalidad de entrega (Recojo en puesto o Delivery):** El cliente selecciona durante el checkout si recogerá sus productos directamente en los puestos del mercado o si solicita envío a domicilio consolidado a través de un repartidor asignado. | Cliente / Repartidor | Media |

---

## 2. Atributos de calidad (ordenados por prioridad)

1. **Capacidad de interacción / Usabilidad (Atributo Crítico):** Es el atributo más crítico del sistema porque los comerciantes del Mercado San Camilo tienen perfiles etarios diversos, alta carga operativa en sus puestos físicos y escasa familiaridad con herramientas digitales complejas; además, operan en smartphones Android de gama baja con pantallas reducidas. La interfaz debe permitir completar acciones clave (como publicar productos o confirmar pedidos) en un máximo de 3 toques, sin fricción cognitiva.
2. **Eficiencia de desempeño / Rendimiento:** Es esencial debido a que la mayor parte de las consultas y compras se concentran en horarios pico (mañanas y fines de semana) y la conectividad móvil dentro de las instalaciones históricas de sillar del Mercado San Camilo suele experimentar atenuación de señal (redes 3G/4G inestables). Las respuestas del catálogo y del carrito deben mantenerse bajo p95 ≤ 2 s con transferencias de datos reducidas (< 1.5 MB por sesión).
3. **Fiabilidad / Disponibilidad y Resiliencia:** Es fundamental dado que una orden multi-puesto involucra transacciones distribuidas entre varios comerciantes y pagos ya emitidos por Yape. El sistema debe garantizar consistencia de datos y 0 pedidos perdidos, asegurando que si la conexión con WhatsApp o el servicio de notificaciones experimenta interrupciones, los pedidos se encolen y reintenten de forma automática.
4. **Mantenibilidad / Modificabilidad:** Es clave para un proyecto académico con horizonte de evolución ágil (MVP en 1 mes desarrollado por 3 estudiantes), requiriendo que la arquitectura desacople las integraciones de pasarelas de pago y servicios de mensajería (puertos y adaptadores) para admitir nuevos canales (e.g., Plin, pago con tarjeta) en ≤ 3 días-persona sin alterar la lógica de negocio.

---

## 3. Restricciones

| ID | Tipo | Restricción |
|:---|:---|:---|
| **R-01** | **Plazo** | MVP completamente desplegado y operativo en entorno de producción en un plazo improrrogable de **1 mes** (4 semanas calendario de desarrollo). |
| **R-02** | **Equipo y tecnologías** | Equipo conformado estrictamente por **3 estudiantes de pregrado** (EPIS-UNSA) con dominio práctico en **Python (FastAPI / Django)** en el backend, frontend web responsivo/PWA en **HTML5, TailwindCSS y JavaScript**, y base de datos relacional **PostgreSQL**. |
| **R-03** | **Presupuesto** | Presupuesto de infraestructura y servicios de **$0 USD / mes** (uso exclusivo de niveles gratuitos o VPS comunitario de bajo costo ≤ $5/mes en Render/Railway/Hetzner, sin suscripciones de pago para APIs comerciales). |
| **R-04** | **Normativa y Plataformas externas** | Cumplimiento estricto de la **Ley N.º 29733 (Ley de Protección de Datos Personales del Perú)** para la custodia de números telefónicos y transacciones, e integración técnica basada en esquemas abiertos (URL schemes `wa.me` / webhooks estándar para WhatsApp y verificación de código de operación Yape sin API bancaria oficial de pago). |

---

## 4. Escenarios de atributos de calidad

| ID | Atributo | Fuente | Estímulo | Entorno | Artefacto | Respuesta | Medida |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **QA-01** | **Capacidad de interacción (Usabilidad - Crítico)** | Comerciante del mercado con poca experiencia digital previa | Publica un producto nuevo en su catálogo ingresando nombre, precio y disponibilidad | Dispositivo móvil Android de gama baja (≤ 2 GB de memoria RAM), señal móvil 3G intermitente dentro del puesto | PWA / Módulo de Gestión de Puesto | Interfaz táctil simplificada con pasos guiados, botones de alto contraste, compresión de imagen en cliente y guardado en memoria local si no hay conexión inmediata | Publicación completada en **≤ 3 toques** de pantalla; tiempo total de la operación **≤ 15 segundos**; tasa de error de usuario **≤ 5%** en primera prueba. |
| **QA-02** | **Eficiencia de desempeño (Rendimiento)** | 300 clientes concurrentes ubicados en Arequipa | Consultan simultáneamente el catálogo de puestos y buscan productos filtrados por puesto y categoría | Hora pico de compras (sábados y domingos entre 09:00 y 11:30 a. m.), condiciones normales de operación | Módulo de Catálogo y Búsqueda (API REST + Caché) | El sistema consulta índices optimizados, aplica compresión gzip/brotli y devuelve la lista de productos con imágenes en formato WebP | Percentil 95 del tiempo de respuesta (**p95) ≤ 1.5 s**; payload total de la vista **≤ 400 KB**; tasa de éxito de peticiones HTTP 200 **≥ 99.5%**. |
| **QA-03** | **Fiabilidad (Disponibilidad y Resiliencia)** | Cliente que finaliza un pedido multi-puesto con pago Yape | Envía la orden confirmada hacia 3 puestos distintos, pero la API/servicio de mensajería de WhatsApp se encuentra fuera de servicio (timeout de red HTTP 504) | Operación normal, contingencia o caída externa de red móvil | Módulo de Pedidos y Notificaciones (cola asíncrona de eventos) | El sistema asegura la transacción en PostgreSQL mediante transacción atómica, confirma la recepción al cliente en pantalla y deposita las notificaciones en una cola de reintentos automáticos | **0 pedidos perdidos** (100% persistencia transaccional); confirmación al cliente en pantalla en **≤ 2.0 s**; reintento automático y entrega de notificación en **≤ 5 minutos** tras el restablecimiento del servicio. |

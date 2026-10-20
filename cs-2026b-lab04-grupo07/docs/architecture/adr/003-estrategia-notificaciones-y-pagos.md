# ADR-003: Integración de pagos con Yape y notificaciones por WhatsApp mediante Puertos y Adaptadores

- **Estado:** Aceptado
- **Fecha:** 2026-10-19
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

El flujo troncal de **San Camilo en Línea** exige que el cliente realice el pago consolidado de productos de múltiples puestos usando **Yape**, y que cada comerciante reciba de inmediato en su celular la orden detallada de su puesto mediante **WhatsApp** para su preparación rápida (**RF-03**, **RF-04**).

Al diseñar estas dos integraciones externas, se identificaron los siguientes compromisos y drivers de [`drivers.md`](../drivers.md):
- **R-03 (Presupuesto cero):** Se dispone de $0 USD/mes. No es viable contratar pasarelas de pago comerciales con costos fijos de suscripción mensual ni la API corporativa de WhatsApp Cloud (que cobra por plantilla y conversación iniciada en dólares).
- **R-04 (Restricción técnica y normativa):** El Banco de Crédito (BCP/Yape) no ofrece una API REST pública gratuita para microcomerciantes del mercado; además, se debe acatar la Ley N.º 29733 de Protección de Datos Personales del Perú al manipular números celulares y montos.
- **QA-01 (Usabilidad crítica en celulares de gama baja):** Los comerciantes deben recibir los pedidos en su aplicación cotidiana (WhatsApp) sin obligarlos a mantener apps complejas en primer plano que agoten los 2 GB de RAM de sus dispositivos.
- **QA-03 (Fiabilidad y Resiliencia):** El escenario QA-03 exige **0 pedidos perdidos** y reintentos automáticos en $\le 5$ minutos si WhatsApp experimenta cortes de conectividad.
- **QA-04 (Modificabilidad):** El sistema debe permitir enchufar una pasarela automática formal (e.g., Plin, Niubiz o Culqi) en $\le 3$ días-persona cuando el proyecto pase a una fase comercial con financiamiento.

---

## Alternativas consideradas

1. **Pasarelas comerciales integradas y WhatsApp Business API Cloud Oficial:**
   - *Ventajas:* Conciliación bancaria 100 % automatizada y webhooks bidireccionales oficiales.
   - *Desventajas:* Costos mensuales y comisiones por transacción que violan **R-03** ($0/mes), además de requerir constitución de empresa y trámites de verificación en Meta que exceden el plazo de 1 mes (**R-01**).
2. **Llamadas síncronas HTTP directas acopladas en los controladores de pedidos:**
   - *Ventajas:* Implementación ingenua rápida en pocas líneas de código.
   - *Desventajas:* Acopla el flujo de creación de pedidos a la disponibilidad inmediata de servicios de terceros. Si la red móvil del mercado o WhatsApp tiene latencia, la petición del cliente se bloquea (timeout), degradando el rendimiento (**QA-02**) y provocando órdenes inconsistentes (**QA-03**).
3. **Patrón de Puertos y Adaptadores (Arquitectura Hexagonal) con cola asíncrona (Elegida):**
   - *Ventajas:* Desacopla la lógica del dominio mediante interfaces puras (`IPasarelaPago` y `INotificadorWhatsApp`). Para Yape, el adaptador procesa el comprobante y número de operación con verificación administrativa rápida; para WhatsApp, genera enlaces universales estructurados (`wa.me`) para confirmación inmediata desde el cliente y utiliza Celery/Redis para reintentos asíncronos resilientes.

---

## Decisión

**Adoptaremos el patrón de Puertos y Adaptadores (Arquitectura Hexagonal) para aislar las integraciones de Pagos y Notificaciones del dominio central:**

1. **Módulo de Pagos (`pagos`):**
   - Se define el puerto `PasarelaPagoPort` con métodos `registrar_pago()`, `validar_comprobante()` y `consultar_estado()`.
   - Se implementa el adaptador `YapeManualAdapter`: valida el formato del número de operación único de 8 dígitos, comprime la captura de pantalla del comprobante en cliente y la almacena localmente, marcando la orden en estado `PENDIENTE_VERIFICACION`.
2. **Módulo de Notificaciones (`notificaciones`):**
   - Se define el puerto `NotificadorPort` con el método `despachar_aviso_pedido()`.
   - Se implementa el adaptador `WhatsAppSchemeAdapter`: genera deep links directos mediante el URL scheme oficial `https://wa.me/51<telefono>?text=<mensaje_url_encoded>` con el resumen tabulado del pedido por puesto (producto, cantidad, total y modalidad de entrega).
   - Para seguimiento en segundo plano, se implementa `CeleryWhatsAppWorker`: si la confirmación falla, encola el aviso en Redis y reintenta con retroceso exponencial (*exponential backoff*).
3. **Seguridad y Privacidad (R-04):**
   - Los números telefónicos y datos de transacciones se encriptan en reposo y se omiten de los archivos de log de la aplicación.

---

## Consecuencias

### Positivas:
- **Cero costo de licenciamiento (R-03):** El sistema opera al 100 % dentro del presupuesto de $0 USD sin depender de APIs bancarias pagas.
- **Resiliencia y 0 pedidos perdidos (QA-03):** La orden se guarda atómicamente en PostgreSQL independientemente de si el servicio de mensajería responde al instante.
- **Fácil modificación y evolución (QA-04):** Cambiar de validación manual de Yape a una pasarela automática futura solo requiere crear una nueva clase que implemente `PasarelaPagoPort`, sin modificar una sola línea del módulo de `pedidos`.
- **Fricción mínima para el comerciante (QA-01):** El comerciante recibe la comanda directamente en su WhatsApp habitual con un formato limpio y legible.

### Negativas / Riesgos y Mitigación:
- **Conciliación semi-automática:** Al no haber webhook bancario directo de Yape, existe el riesgo de que un cliente ingrese un código de operación falso.
  - *Mitigación:* La PWA del comerciante y del administrador incluye un botón de "Confirmar abono en cuenta" que se valida con un solo toque antes de autorizar el despacho de la mercadería.

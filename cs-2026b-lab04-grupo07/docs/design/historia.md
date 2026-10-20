# Historia de Usuario — San Camilo en Línea

## HU-01: Carrito y pedido a múltiples puestos con pago unificado vía Yape

**Como** cliente de la plataforma San Camilo en Línea,  
**quiero** armar un carrito de compras agregando productos de diversos puestos comerciales del Mercado San Camilo y pagarlos de forma unificada mediante una única transferencia por Yape,  
**para** evitar realizar múltiples pagos individuales a cada comerciante, consolidar mis compras en un solo proceso y coordinar el recojo o delivery de forma ordenada.

---

### Criterios de Aceptación (Formato Dado / Cuando / Entonces)

#### Criterio 1: Confirmación de pedido multi-puesto y pago aprobado (Flujo de éxito)
- **Dado** que el cliente tiene un pedido en estado `BORRADOR` con productos seleccionados de dos o más puestos comerciales distintos del Mercado San Camilo y con stock suficiente disponible en cada uno,
- **Cuando** el cliente confirma la orden, selecciona la modalidad de entrega (`RECOJO_EN_PUESTO` o `DELIVERY`), ingresa el número de operación y adjunta la captura del comprobante de Yape por el monto total exacto, y el pago es validado en el sistema,
- **Entonces** el pedido general cambia a estado `PAGADO`, se generan automáticamente las subórdenes (`PedidoPuesto`) para cada puesto en estado `RECIBIDO`, se reserva formalmente el stock de cada producto en el catálogo y se despacha una notificación estructurada por WhatsApp a cada comerciante involucrado con el detalle de los productos a preparar.

#### Criterio 2: Rechazo de comprobante o expiración del tiempo límite (Flujo de excepción)
- **Dado** que el cliente tiene un pedido en estado `CONFIRMADO` (en espera de comprobante) con stock temporalmente bloqueado,
- **Cuando** el comprobante de Yape es rechazado por inconsistencia en el monto/código o transcurren más de 15 minutos sin registrar la transferencia,
- **Entonces** el pedido consolidado cambia a estado `CANCELADO`, las subórdenes por puesto asociadas se marcan como `RECHAZADO`, se libera inmediatamente el stock reservado en el catálogo para otros compradores y se notifica al cliente en pantalla el motivo del rechazo.

#### Criterio 3: Preparación individual por puesto y consolidación de entrega (Flujo logístico)
- **Dado** que un pedido multi-puesto está en estado `PAGADO` y cada comerciante ha marcado su suborden (`PedidoPuesto`) como `LISTO` tras alistar la mercadería en su puesto físico del mercado,
- **Cuando** el cliente o repartidor retira los paquetes de cada puesto y se confirma la recepción final,
- **Entonces** cada suborden cambia a estado `RECOGIDO` y, al completarse el retiro de todos los puestos, el pedido consolidado pasa a estado `ENTREGADO`.

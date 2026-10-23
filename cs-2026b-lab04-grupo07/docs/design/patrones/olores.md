# Detección de Olores de Código y Decisión de Patrones — San Camilo en Línea

Este documento corresponde al entregable **E1** del Laboratorio 07 (Patrones de Diseño GoF, EPIS-UNSA). Se analiza la versión inicial de `src/pedidos/antes/servicio.py` para fundamentar la refactorización mediante métricas objetivas y principios de diseño SOLID.

---

## 1. Salida de Complejidad Ciclomática (Radon) — Versión `antes`

Medición ejecutada con `radon cc -s -a src/pedidos/antes/servicio.py`:

```text
src/pedidos/antes/servicio.py
    M 43:4 ServicioPedidos.confirmar_y_pagar - C (15)
    C 36:0 ServicioPedidos - B (10)
    M 99:4 ServicioPedidos.sugerir_descripcion - B (8)
    C 24:0 Pedido - A (3)
    M 38:4 ServicioPedidos.__init__ - A (3)
    C 13:0 Linea - A (2)
    M 32:4 Pedido.total - A (2)
    M 19:4 Linea.subtotal - A (1)

8 blocks (classes, functions, methods) analyzed.
Average complexity: B (5.5)
```

> **Diagnóstico:** El método `confirmar_y_pagar` supera el umbral recomendado de 10 caminos independientes, situándose en **Complejidad 15 (Rango C)**. Resulta altamente propenso a errores, difícil de testear de forma exhaustiva y rígido ante la incorporación de nuevas formas de pago o modificaciones en el ciclo de vida de la orden.

---

## 2. Tabla de Olores Detectados y Decisión Arquitectónica

Siguiendo la metodología *Refactoring to Patterns* (Kerievsky, Fowler), los patrones de diseño GoF solo se introducen si resuelven un olor concreto y comprobado.

| # | Líneas | Olor detectado (Code Smell) | Patrón GoF propuesto | Principio SOLID | Costo / Trade-off | Decisión del Equipo |
|:---|:---|:---|:---|:---|:---|:---|
| **1** | 59–79 | **Sentencias condicionales (`if/elif`) por variante de medio de pago** (`medio == "YAPE"`, `medio == "PLIN"`). Crece linealmente cada vez que San Camilo en Línea soporte una nueva billetera digital (e.g., Tunki, Tarjeta, Agora). | **Strategy** + **Factory Method (con Registro)** | **O — Abierto / Cerrado (OCP)** y **D — Inversión de Dependencias (DIP)** | Introduce interfaces abstractas (`PasarelaPago`) y un registro de creadores. Agrega archivos adicionales e indirección. | **Aceptado:** Permite registrar medios de pago dinámicamente en tiempo de ejecución sin reabrir ni editar `ServicioPedidos`. |
| **2** | 60–76 | **Acoplamiento a SDKs externos y conversión de tipos desordenada**. El servicio de aplicación conoce detalles de bajo nivel: que Yape recibe soles en float y retorna un diccionario con `'ok'`, mientras que Plin cobra en céntimos enteros multiplicando por 100 y retorna tuplas con código HTTP. | **Adapter (Adaptador de Objetos)** | **D — Inversión de Dependencias (DIP)** e **I — Segregación de Interfaces (ISP)** | Una clase adaptadora por cada proveedor externo que traduce peticiones y respuestas. | **Aceptado:** Aísla el modelo de dominio frente a cambios en APIs o SDKs de terceros. |
| **3** | 60–76 | **Código duplicado en bucles de reintento (`for intento in range(3)`)** mezclado directamente en el flujo transaccional. La misma política de 3 reintentos ante `TimeoutError` se replica para Yape y Plin. | **Decorator (Envoltorio Transversal)** | **S — Responsabilidad Única (SRP)** y **O — Abierto / Cerrado (OCP)** | Un objeto intermedio en la cadena de llamadas que envuelve a la pasarela real. | **Aceptado:** Reutiliza la resiliencia de forma no invasiva y asegura que solo se reintenten fallas de red, nunca cobros rechazados por reglas de negocio. |
| **4** | 44–52 | **Condicionales anidados basados en strings sobre el atributo `pedido.estado`** (`if estado != "BORRADOR"`, `if CANCELADO`, `if PAGADO`). Si se agrega un nuevo estado (e.g., `EN_PREPARACION` o `ENTREGADO`), se deben alterar múltiples condicionales en todo el servicio. Además, provocó el bug de mutar a `CONFIRMADO` antes de validar el medio. | **State (Estado)** | **S — Responsabilidad Única (SRP)**, **O — Abierto / Cerrado (OCP)** y **L — Sustitución de Liskov (LSP)** | Se requiere una jerarquía polimórfica (`EstadoPedido`, `Borrador`, `Confirmado`, etc.) y delegación desde la entidad `Pedido`. | **Aceptado:** Implementa directamente el diagrama de máquina de estados de Lab 05. Hace que las transiciones inválidas sean imposibles por diseño. |
| **5** | 82–84 | **Notificación manual ("Hardcoded")** a WhatsApp y reportes (`self.eventos.append(...)`) dentro de la lógica de pago. Agregar auditoría o avisos por correo obligaría a tocar `ServicioPedidos`. | **Observer (Publicador / Suscriptor)** | **S — Responsabilidad Única (SRP)** y **O — Abierto / Cerrado (OCP)** | Creación de un bus/publicador de eventos en memoria y suscriptores específicos. | **Aceptado (para E4):** Desacopla las consecuencias secundarias del éxito de la transacción. |
| **6** | Propuesta IA | **"Crear `FabricaPasarelas` como Singleton con variable global"** para acceder a la fábrica desde cualquier punto de la aplicación. | **Singleton** | N/A (Viola DIP y testeabilidad) | Introduce estado global mutable oculto, acopla componentes y dificulta enormemente la inyección de dobles de prueba (mocks). | **Rechazado (Patternitis):** No se justifica estado global. Es preferible instanciar e inyectar la fábrica o pasarla en el constructor del servicio. |
| **7** | Propuesta IA | **"Usar Abstract Factory para construir familias de pasarelas y validadores"** (e.g. `FamiliaYapeFactory`, `FamiliaPlinFactory`). | **Abstract Factory** | N/A (Sobreingeniería) | Multiplica el número de clases y fábricas abstractas innecesariamente. | **Rechazado (Patternitis):** En San Camilo en Línea no existen familias dependientes de productos interconectados; una simple Factory basada en registro (Factory Method) resuelve completamente la variación con menor costo cognitivo. |
| **8** | 99–120 | **Condicionales para proveedores de LLM y guardrails encadenados manualmente** en `sugerir_descripcion`. | **Strategy** + **Adapter** + **Chain of Responsibility** | **S — Responsabilidad Única (SRP)** y **O — Abierto / Cerrado (OCP)** | Cadena de manejadores independientes para cada guardrail y adaptadores por proveedor. | **Aceptado (para E5):** Permite cambiar de proveedor de IA (Claude, OpenAI, Local) y agregar reglas de moderación como eslabones intercambiables. |

---

## 3. Conclusión de la Evaluación Inicial

- **Patrones aceptados para refactorizar en la fase actual:**
  - **Strategy + Adapter + Factory (E2):** Abordan los olores 1 y 2 en el procesamiento de pagos.
  - **State (E3):** Resuelve el olor 4, garantizando que el ciclo de vida del pedido sea robusto y respetuoso de la máquina de estados.
- **Patrones deliberadamente rechazados para evitar "Patternitis":**
  - **Singleton:** Rechazado para preservar la independencia de los tests y evitar estado global.
  - **Abstract Factory:** Rechazado por sobrediseño innecesario al no existir familias de objetos.

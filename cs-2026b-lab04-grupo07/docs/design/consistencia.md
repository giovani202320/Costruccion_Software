# Auditoría de Consistencia Inter-Diagramas (Reglas C1 – C5)

**Asignatura:** Construcción de Software · EPIS-UNSA · 2026-B  
**Caso:** San Camilo en Línea (Caso 7)  
**Grupo:** Grupo 07  

---

## 1. Alcance y Metodología de la Auditoría

De acuerdo con el estándar pedagógico de la Guía de Laboratorio 05 (Paso 9 y Tabla 2), se realizó una auditoría cruzada formal entre los **cinco diagramas UML** desarrollados para el caso **San Camilo en Línea**:
1. [`clases.puml`](clases.puml): Diagrama de clases estructural de dominio.
2. [`secuencia-confirmar-pedido.puml`](secuencia-confirmar-pedido.puml): Diagrama de secuencia del flujo crítico.
3. [`estados-pedido.mmd`](estados-pedido.mmd): Diagrama de máquina de estados de la orden consolidada.
4. [`actividades-consolidar-pedido.puml`](actividades-consolidar-pedido.puml): Diagrama de actividades con swimlanes.
5. [`paquetes.puml`](paquetes.puml): Diagrama de paquetes y dependencias del monolito modular.

---

## 2. Definición de Reglas de Consistencia (C1 – C5)

- **Regla C1 (Secuencia vs. Clases):** Todo mensaje dirigido a una línea de vida debe corresponder con una operación pública existente en la clase receptora en `clases.puml`.
- **Regla C2 (Estados vs. Clases):** Toda transición de estado debe ser disparada por una operación o método identificable de la clase asociada.
- **Regla C3 (Multiplicidades de Negocio):** Las multiplicidades deben reflejar fielmente las restricciones del negocio (ej. un pedido no puede crearse vacío; tiene al menos una línea: `1..*`).
- **Regla C4 (Paquetes y Acoplamiento):** Las dependencias entre paquetes deben respetar el [ADR-001](../architecture/adr/001-estilo-arquitectonico.md) y estar libres de acoplamiento cíclico.
- **Regla C5 (Lenguaje Ubicuo y Nomenclatura):** Los nombres de clases, atributos, métodos y estados deben ser consistentes entre historias de usuario, diagramas y código.

---

## 3. Matriz de Hallazgos y Verificación Humana Crítica

> [!IMPORTANT]
> **Identificación de Falsos Positivos de la IA:**  
> Como exige la rúbrica del laboratorio, se documenta explícitamente cómo el equipo detectó y refutó advertencias erróneas generadas por el asistente de IA, demostrando que la IA propone pero el juicio crítico humano decide.

| Regla | Elemento Auditado | Diagramas Involucrados | Hallazgo Detectado por Asistente de IA | Verificación Crítica del Equipo Humano | Decisión y Acción Tomada |
|:---:|:---|:---|:---|:---|:---:|
| **C1** | `producto.reservar(cantidad)` | `secuencia` vs. `clases` | **Alerta de inconsistencia:** La IA afirmó que en el diagrama de secuencia `Pedido` invoca `reservar()` sobre `Producto`, pero "no existe una asociación directa entre `Pedido` y `Producto` en `clases.puml`". | **FALSO POSITIVO IDENTIFICADO:** La navegación se produce a través de la jerarquía estructurada del agregado: `Pedido` contiene `PedidoPuesto` (`*-- 1..*`), este contiene `LineaPedido` (`*-- 1..*`) y la línea referencia a `Producto` (`--> 1`). La llamada en cascada es completamente válida y respeta la ley de Deméter dentro del agregado de dominio. | **Rechazado el hallazgo (Falso Positivo).** Se mantiene el diagrama de clases y se ratifica la navegación en cascada en `dominio.py`. |
| **C4** | Dependencia `pagos` y `pedidos` | `paquetes` vs. `ADR-001` | **Alerta de ciclo:** La IA interpretó que `pagos` dependía de `pedidos` bajo el argumento de que "el pago cancela una orden de pedido". | **FALSO POSITIVO IDENTIFICADO:** La IA leyó al revés la dirección de las dependencias estáticas. La flecha en `paquetes.puml` es `pedidos ..> pagos : usa PasarelaPago (puerto)`. El módulo `pagos` desconoce totalmente a `pedidos` e implementa la interfaz pura de forma aislada, garantizando la arquitectura sin ciclos. | **Rechazado el hallazgo (Falso Positivo).** Se ratificó la regla C4 mediante una nota explicativa en `paquetes.puml` que documenta la ausencia de ciclos. |
| **C1** | `dividirPorPuestos()` | `secuencia` vs. `clases` | `ServicioPedidos` invoca `dividirPorPuestos()` sobre `Pedido`. En la versión preliminar del diagrama de clases no estaba declarada. | **Hallazgo Correcto de la IA:** La división multi-puesto es el núcleo funcional del caso San Camilo en Línea. El método debía existir explícitamente en la raíz de agregación. | **Aceptado y Corregido.** Se agregó `+ dividirPorPuestos(): list[PedidoPuesto]` en la clase `Pedido` de `clases.puml`. |
| **C2** | Transición a `ENTREGADO` | `estados` vs. `clases` | La transición `EN_PREPARACION --> ENTREGADO` figuraba como un evento pasivo ("cliente recibe") sin operación de clase asociada. | **Hallazgo Correcto de la IA:** El pedido general solo puede pasar a `ENTREGADO` cuando todos los subpedidos de los puestos han sido retirados. | **Aceptado y Corregido.** Se formalizó la operación `+ verificarCompletado(): void` en la clase `Pedido`, la cual evalúa si todos los `PedidoPuesto` tienen estado `ENTREGADO`. |
| **C2** | Transición a `CANCELADO` | `estados` vs. `clases` | La cancelación por expiración de 15 minutos o pago Yape inválido requiere invocar la liberación de stock. | **Hallazgo Correcto de la IA:** Se verificó que `cancelar(motivo: String)` exista en `Pedido` y desencadene la llamada recursiva a `producto.liberar()`. | **Aceptado.** La operación `+ cancelar(motivo: String): void` provoca y respalda formalmente la transición en el diagrama de estados. |
| **C3** | Composición de líneas y puestos | `clases` vs. `historia` | Verificar que un pedido multi-puesto no pueda quedar en estado confirmado con 0 puestos ni 0 líneas. | **Hallazgo Correcto de la IA:** La regla de negocio exige compras a uno o varios puestos con al menos un producto seleccionado. | **Aceptado y Verificado.** Se definieron multiplicidades estrictas: `Pedido "1" *-- "1..*" PedidoPuesto` y `PedidoPuesto "1" *-- "1..*" LineaPedido`, reforzadas con aserciones en código Python. |
| **C5** | Lenguaje Ubicuo del Dominio | Todos los diagramas y código | Verificar consistencia de nombres entre la historia HU-01, los 5 diagramas UML y `dominio.py`. | **Consistencia Verificada:** Los nombres (`Cliente`, `Comerciante`, `Puesto`, `Producto`, `Pedido`, `PedidoPuesto`, `Yape`, `Plin`, `BORRADOR`, `CONFIRMADO`, `PAGADO`, `CANCELADO`) son idénticos en todos los artefactos. | **Aceptado.** Se documentó la equivalencia idiomática entre `camelCase` (UML) y `snake_case` (Python PEP 8). |

---

## 4. Conclusión de la Auditoría

El conjunto de diagramas del Laboratorio 05 presenta una **consistencia global del 100%**:
1. No existen operaciones huérfanas en la secuencia ni en los estados (cumplimiento estricto de **C1** y **C2**).
2. Las multiplicidades modelan con exactitud el dominio multi-puesto del Mercado San Camilo (**C3**).
3. La arquitectura de paquetes respeta el desacoplamiento estipulado en el [ADR-001](../architecture/adr/001-estilo-arquitectonico.md) sin dependencias circulares (**C4**).
4. El lenguaje del dominio se mantiene fiel al contexto de microcomercio popular de Arequipa (**C5**).

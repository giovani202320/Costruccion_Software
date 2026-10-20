# Bitácora de Uso de IA — Laboratorio 05: Diseño UML como Código

**Asignatura:** Construcción de Software · EPIS-UNSA · 2026-B  
**Caso:** San Camilo en Línea (Caso 7)  
**Grupo:** Grupo 07  

---

## 1. Registro de Interacciones

| # | Fecha | Herramienta | Prompt (resumen) | Qué propuso la IA | Qué verificamos o corregimos | Decisión |
|:---:|:---:|:---|:---|:---|:---|:---:|
| **1** | 20/10 | Antigravity (Gemini 3.8 Flash) | Generación del diagrama de clases en PlantUML a partir de la historia HU-01 y el ADR-001. | Propuso incluir el atributo `numeroTarjeta` y `cvv` en la clase `Pago`, y modeló `Yape` como herencia directa de `Pago` (`Yape extends Pago`). | **Corrección y rechazo de sobre-diseño:** El MVP de San Camilo solo contempla pagos con Yape/Plin; guardar números de tarjeta viola R-03 y exige certificación PCI-DSS. Además, contradecía el ADR-001 (se modela `PasarelaPago` como puerto/interfaz con adaptadores). | **Corregida** |
| **2** | 20/10 | Antigravity (Gemini 3.8 Flash) | Ingeniería directa: generación de esqueleto en Python 3.10 a partir de `clases.puml`. | Esqueleto completo en `src/pedidos/dominio.py` con `dataclasses`, `Enum` y `abc.ABC`. Inicialmente omitió la validación de al menos una línea en `confirmar()`. | Se agregó manualmente la validación de cardinalidad mínima en `Pedido.confirmar()` para cumplir la **Regla C3** (un pedido no puede ser confirmado vacío). | **Corregida** |
| **3** | 20/10 | Antigravity (Gemini 3.8 Flash) | Comparación Round-Trip entre diseño manual y salida de `pyreverse`. | Identificación de 5 diferencias clave: falta de multiplicidades en Python, listas tipadas en lugar de composiciones con diamante, y clases abstractas en lugar de interfaces nativas. | Se validó la precisión del análisis y se redactó [`round-trip.md`](round-trip.md) documentando las limitaciones intrínsecas de las herramientas de ingeniería inversa estática. | **Aceptada** |
| **4** | 20/10 | Antigravity (Gemini 3.8 Flash) | Auditoría de consistencia C1 a C5 sobre los 5 diagramas UML. | La IA alertó que en la secuencia `Pedido` invoca `reservar()` sobre `Producto` sin existir asociación directa visible, y afirmó que `pagos` depende cíclicamente de `pedidos`. | **Doble Falso Positivo Identificado:** 1) La navegación hacia `Producto` se realiza legítimamente a través de `PedidoPuesto` y `LineaPedido` (agregado DDD); 2) `pagos` no conoce a `pedidos`, es `pedidos` quien usa el puerto. Se refutaron los hallazgos en [`consistencia.md`](consistencia.md). | **Rechazada (Falsos Positivos Refutados)** |
| **5** | 20/10 | Antigravity (Gemini 3.8 Flash) | Generación de diagramas de secuencia, actividades y estados. | Sintaxis PlantUML y Mermaid para los flujos críticos. Sugirió que la notificación de WhatsApp sea síncrona. | Se corrigió la notificación para que sea explícitamente asíncrona (`->>`) hacia `NotificadorWhatsApp`, evitando congelar la interfaz del cliente ante latencias de red. | **Corregida** |

---

## 2. Anexo: Prompts Completos

### Prompt 1 — Diagrama de Clases
```text
Actúa como diseñador de software orientado a objetos (@uml-designer).
Contexto: Módulo Pedidos y Pagos de un monolito modular para San Camilo en Línea (ADR-001).
Historia y criterios: HU-01 (pedido multi-puesto con pago unificado Yape).
Tarea: Genera un diagrama de clases en PlantUML con atributos tipados, visibilidad (-), operaciones, multiplicidades en ambos extremos, enumeraciones para estados y una interfaz (puerto) para pasarela de pagos.
```

### Prompt 2 — Auditoría de Consistencia C1 a C5
```text
Actúa como auditor de diseño UML. Analiza los 5 diagramas (clases.puml, secuencia.puml, estados.mmd, actividades.puml, paquetes.puml).
Evalúa: C1 (mensajes de secuencia en clases), C2 (transiciones en operaciones), C3 (multiplicidades de negocio), C4 (paquetes sin ciclos), C5 (lenguaje ubicuo). Reporta hallazgos indicando regla, elemento y corrección.
```

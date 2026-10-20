# Round-Trip Engineering: Comparación entre Diseño e Ingeniería Inversa

**Asignatura:** Construcción de Software · EPIS-UNSA · 2026-B  
**Caso:** San Camilo en Línea (Caso 7)  
**Grupo:** Grupo 07  

---

## 1. Contexto del Experimento Round-Trip

De acuerdo con el flujo de ingeniería directa e inversa asistido por IA (Guía de Laboratorio 05, Paso 8):
1. **Ingeniería Directa:** A partir del diagrama de clases diseñado en PlantUML ([`clases.puml`](clases.puml)), se implementó el esqueleto del modelo de dominio en Python 3.10 ([`src/pedidos/dominio.py`](../../src/pedidos/dominio.py)) utilizando `dataclasses`, `Enum`, `type hints` y clases abstractas (`abc.ABC`).
2. **Ingeniería Inversa:** A partir del código ejecutable generado, se ejecutó la herramienta estándar `pyreverse` (incluida en `pylint`) mediante el comando:
   ```bash
   pyreverse -o puml -p pedidos src/pedidos
   ```
   generando el diagrama inverso [`classes_pedidos.puml`](classes_pedidos.puml) y su render en imagen [`img/classes_pedidos.png`](img/classes_pedidos.png).

---

## 2. Tabla Comparativa de Diferencias Observadas

A continuación se detallan las diferencias técnicas detectadas al confrontar el **Diagrama de Diseño Manual** frente al **Diagrama Obtenido por Ingeniería Inversa**:

| # | Diferencia Observada | Diagrama de Diseño (`clases.puml`) | Diagrama Inverso (`classes_pedidos.puml`) | Causa Técnica | Acción Tomada / Justificación |
|:---:|:---|:---|:---|:---|:---|
| **1** | **Representación de Composiciones y Agregaciones** | Modela relaciones fuertes todo-parte mediante composición (`Pedido "1" *-- "1..*" PedidoPuesto` y `PedidoPuesto "1" *-- "1..*" LineaPedido`). | Los subpedidos y líneas figuran como atributos de colección: `subpedidos : List[PedidoPuesto]` y `lineas : List[LineaPedido]` dentro de la clase. | `pyreverse` inspecciona tipos estáticos de atributos pero no puede inferir la semántica de ciclo de vida (que las partes mueren con el todo) a partir de listas estándar. | **Ninguna en código.** Se documenta como una limitación intrínseca de las herramientas de introspección estática. El diagrama de diseño manual se mantiene como especificación de referencia. |
| **2** | **Ausencia de Multiplicidades** | Especifica cardinalidades exactas en ambos extremos de toda asociación (`1` a `1..*`, `1` a `0..*`, `1` a `0..1`). | No muestra multiplicidades numéricas en las líneas de asociación. | El sistema de tipos de Python no soporta cardinalidades mínimas ni máximas (sabe que es una lista, pero no si tiene mínimo 1 elemento). | **Acción en código:** Se implementó una validación defensiva en el método `confirmar()` de `Pedido` para arrojar `ValueError` si el pedido no contiene al menos 1 línea (**Regla C3**). |
| **3** | **Puertos e Interfaces frente a Clases Abstractas** | Modela `PasarelaPago`, `RepositorioPedidos` y `NotificadorWhatsApp` con el estereotipo `<<puerto>>` e interfaces con realización (`<|..`). | Aparecen como clases ordinarias que heredan de `abc.ABC`, y la relación de los adaptadores figura como herencia de clases (`<|--`). | Python no cuenta con una palabra clave nativa `interface`. La convención oficial de la comunidad es usar `abc.ABC` con métodos `@abstractmethod`. | **Aceptable en Python.** Se documenta la equivalencia semántica directa entre el puerto hexagonal de UML y la clase abstracta de Python. |
| **4** | **Convención de Nomenclatura (camelCase vs. snake_case)** | Nombres en formato `camelCase` estándar internacional de UML (`totalConsolidado`, `dividirPorPuestos()`, `codigoOperacion`). | Nombres en formato `snake_case` (`total_consolidado`, `dividir_por_puestos()`, `codigo_operacion`). | Convención idiomática de estilo obligatoria en Python (PEP 8). | **Aceptable.** Se documenta la correspondencia biunívoca 1:1 entre identificadores, cumpliendo la **Regla C5** (lenguaje ubicuo preservado). |
| **5** | **Encapsulamiento y Visibilidad de Campos** | Se define visibilidad privada estricta (`-`) para proteger los invariantes de dominio. | Los atributos de las dataclasses se exponen como públicos (sin prefijo `_`). | En Python las dataclasses generan parámetros públicos para permitir la instanciación idiomática por palabras clave (`__init__(puesto=...)`). | **Aceptable.** La consistencia transaccional se protege mediante métodos de negocio (`confirmar()`, `registrar_pago()`, `cancelar()`). |

---

## 3. Conclusiones del Ciclo Round-Trip

1. **El valor del diagrama como plano:** El código fuente en Python por sí solo no expresa las reglas de cardinalidad ni la fuerza de las relaciones (composición vs. asociación). El diagrama UML de diseño actúa como el **plano arquitectónico indispensable** que guía las validaciones que el lenguaje de programación no puede tipar de forma nativa.
2. **Fidelidad estructural:** A pesar de las limitaciones de visualización de `pyreverse`, la estructura modular, los métodos de dominio y las jerarquías de puertos y adaptadores coinciden en un 100%, validando que el esqueleto implementado respeta fielmente la arquitectura definida en el [ADR-001](../architecture/adr/001-estilo-arquitectonico.md).

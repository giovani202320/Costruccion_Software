# Matriz de decisión — San Camilo en Línea

Documento de evaluación y selección fundamentada del estilo arquitectónico para la plataforma de pedidos multi-puesto **San Camilo en Línea** (Caso 7), en el marco de la Guía de Laboratorio 04 de Construcción de Software (EPIS-UNSA).

---

## Alternativas

- **A. Monolito en capas (Layered / N-Tier Architecture):** El sistema se organiza en capas horizontales superpuestas (Presentación, Lógica de Negocio y Acceso a Datos / Persistencia), compartiendo una base de datos centralizada. Cada capa depende exclusivamente de la capa inmediata inferior. Es sencillo y rápido de estructurar inicialmente, pero genera un alto acoplamiento horizontal y dificulta la evolución independiente de dominios como puestos, pedidos y pagos.
- **B. Microservicios (Microservices Architecture):** La solución se descompone en un conjunto de servicios autónomos e independientes por contexto delimitado (Servicio Catálogo-Puestos, Servicio Carrito-Pedidos, Servicio Pagos Yape, Servicio Notificaciones WhatsApp), cada uno con su propio almacenamiento de datos y comunicados a través de un API Gateway y un broker de eventos asíncronos. Ofrece escalabilidad fina y despliegues aislados, pero impone una alta complejidad operativa, sobrecosto de infraestructura, latencia de red añadida y dificultad en la consistencia de transacciones multi-puesto.
- **C. Monolito modular (Modular Monolith):** El sistema se compila y despliega como una única unidad ejecutable, pero con una estricta separación interna en módulos de dominio cohesivos (`catalogo_puestos`, `pedidos`, `pagos`, `notificaciones`, `usuarios`) con fronteras e interfaces públicas explícitas (puertos y adaptadores). Combina la simplicidad operativa y bajo costo de un solo proceso con la alta modificabilidad y orden de código de arquitecturas desacopladas, permitiendo migrar a microservicios en el futuro si la carga lo justifica.

---

## Criterios y pesos (deben sumar 100 %)

| Criterio | Peso | Justificación (driver relacionado) |
|:---|:---:|:---|
| **Tiempo de entrega (Viabilidad en 1 mes)** | **25 %** | **R-01** (MVP en producción en 1 mes) y **R-02** (equipo de 3 estudiantes). Una arquitectura compleja impediría llegar a tiempo al lanzamiento con funcionalidades completas. |
| **Costo operativo y simplicidad de despliegue** | **20 %** | **R-03** (presupuesto $0 USD / mes o VPS básico $\le \$5/\text{mes}$) y **R-02** (equipo sin dedicación exclusiva a DevOps ni mantenimiento de clústeres distribuidos). |
| **Capacidad de interacción y rendimiento móvil** | **20 %** | **QA-01** (atributo crítico: publicación de productos y confirmación en $\le 3$ toques en celulares de gama baja) y **QA-02** (p95 $\le 1.5\text{ s}$ en redes 3G intermitentes del mercado). Favorece comunicaciones directas en memoria sin sobrecarga de red interna. |
| **Modificabilidad y desacoplamiento modular** | **20 %** | **QA-04** (modificabilidad para incorporar nuevas pasarelas o canales en $\le 3$ días-persona) y **RF-01 a RF-05** (independencia entre la gestión de inventario por puesto y la consolidación de órdenes multi-puesto). |
| **Fiabilidad e integridad transaccional** | **15 %** | **QA-03** (0 pedidos perdidos y confirmación en pantalla $\le 2.0\text{ s}$) y **RF-02 / RF-03** (garantía de atomicidad al subdividir la orden consolidada entre múltiples puestos y asociar el pago de Yape). |

---

## Matriz (puntaje 1 = muy malo … 5 = excelente)

| Criterio (peso) | A. Monolito en capas | B. Microservicios | C. Monolito modular |
|:---|:---:|:---:|:---:|
| **Tiempo de entrega** (25 %) | 5 | 1 | 4 |
| **Costo operativo y simplicidad** (20 %) | 5 | 1 | 5 |
| **Capacidad de interacción y rendimiento** (20 %) | 3 | 3 | 4 |
| **Modificabilidad y desacoplamiento** (20 %) | 2 | 5 | 4 |
| **Fiabilidad e integridad transaccional** (15 %) | 4 | 2 | 4 |
| **Total ponderado** | **3.85** | **2.35** | **4.20** |

### Cálculo detallado del puntaje ponderado:
- **Monolito en capas:** $(0.25 \times 5) + (0.20 \times 5) + (0.20 \times 3) + (0.20 \times 2) + (0.15 \times 4) = 1.25 + 1.00 + 0.60 + 0.40 + 0.60 = \mathbf{3.85}$
- **Microservicios:** $(0.25 \times 1) + (0.20 \times 1) + (0.20 \times 3) + (0.20 \times 5) + (0.15 \times 2) = 0.25 + 0.20 + 0.60 + 1.00 + 0.30 = \mathbf{2.35}$
- **Monolito modular:** $(0.25 \times 4) + (0.20 \times 5) + (0.20 \times 4) + (0.20 \times 4) + (0.15 \times 4) = 1.00 + 1.00 + 0.80 + 0.80 + 0.60 = \mathbf{4.20}$

---

## Conclusión

Elegimos la **Alternativa C: Monolito modular** con un puntaje de **4.20 / 5.00**. 

Esta decisión equilibra de manera óptima las restricciones determinantes del proyecto:
1. Permite entregar el MVP dentro del plazo estricto de **1 mes** (**R-01**) con un equipo de **3 estudiantes** (**R-02**), evitando la sobrecarga de configurar y depurar redes distribuidas, service mesh, múltiples pipelines CI/CD o contratos remotos.
2. Es ejecutable con un **costo de hosting de $0 a $5 USD/mes** (**R-03**) en un único contenedor o VPS básico, compartiendo una instancia relacional de **PostgreSQL** con esquemas aislados por módulo.
3. Garantiza la **alta interacción y baja latencia** requerida para comerciantes y clientes (**QA-01**, **QA-02**) al realizar las comunicaciones inter-módulo directamente en memoria mediante llamadas a servicios de aplicación, sin penalización de serialización HTTP ni saltos de red adicionales.
4. Mantiene la **modificabilidad** (**QA-04**) y transaccionalidad atómica (**QA-03**) para pedidos multi-puesto mediante el patrón de puertos y adaptadores (Arquitectura Hexagonal interna), dejando abierta la posibilidad de extraer módulos a microservicios a futuro si el volumen de pedidos supera la capacidad del servidor.

Ver registro formal de la decisión en [ADR-001: Adoptar un monolito modular para el MVP de San Camilo en Línea](adr/001-estilo-arquitectonico.md).

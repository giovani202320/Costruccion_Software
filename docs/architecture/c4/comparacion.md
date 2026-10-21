# Comparación de herramientas y vistas - Lab 06

## Modelo único frente a diagrama manual

`workspace.dsl` es la fuente única de verdad: el mismo modelo produjo las cinco vistas en PlantUML y Mermaid. Esto evita renombrar, duplicar o corregir manualmente elementos en cada diagrama.

| Criterio | Structurizr DSL y exportación | C4-PlantUML escrito a mano |
|---|---|---|
| Tiempo inicial | Requiere definir un modelo con identificadores y relaciones, pero las vistas posteriores se generan de forma consistente. | Es rápido para un único contexto pequeño, como `contexto-manual.puml`. |
| Errores detectados | `structurizr validate` identifica referencias inválidas antes de exportar. | Los errores de consistencia entre archivos se detectan manualmente. |
| Cambio de un contenedor | Se cambia en `workspace.dsl` y se reexportan todas las vistas. | Debe localizarse y editarse cada archivo de diagrama afectado. |
| Uso recomendado | Arquitectura del proyecto y evolución de los cinco niveles/vistas C4. | Comparación didáctica o un diagrama aislado y pequeño. |

## Vista dinámica C4 frente a secuencia UML

La vista dinámica `confirmarYape` resume el caso crítico en diez pasos arquitectónicos: PWA, módulos de pedidos, catálogo, pagos y notificaciones, persistencia, Redis y el worker. El diagrama de secuencia UML de Lab 05 aporta mayor detalle de objetos y operaciones (`Pedido.confirmar`, reserva/liberación de productos, ramas de pago aprobado/rechazado y activaciones). La primera sirve para explicar colaboración entre componentes y contenedores al equipo técnico; la segunda sirve para implementar y comprobar el comportamiento del dominio.
